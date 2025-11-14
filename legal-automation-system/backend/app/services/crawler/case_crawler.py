"""
판례 크롤링 시스템
"""

import re
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import logger
from app.models.law import LawCase, LawInterpretation
from app.services.rag.retriever import LegalRAGSystem


class CaseCrawler:
    """판례 및 법령해석 크롤러"""

    def __init__(self):
        """판례 크롤러 초기화"""
        self.base_url = "https://glaw.scourt.go.kr"  # 대법원 종합법률정보
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.rate_limit = 0.5  # 초당 요청 수

    async def __aenter__(self):
        """비동기 컨텍스트 진입"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 종료"""
        if self.session:
            await self.session.close()

    async def crawl_recent_cases(
        self,
        court_type: str = "supreme",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        최근 판례 크롤링

        Args:
            court_type: 법원 종류 (supreme, high, district)
            limit: 크롤링할 판례 수

        Returns:
            판례 정보 리스트
        """
        cases = []

        try:
            # 법원별 검색
            if court_type == "supreme":
                cases.extend(await self._crawl_supreme_court_cases(limit))
            elif court_type == "high":
                cases.extend(await self._crawl_high_court_cases(limit))
            elif court_type == "district":
                cases.extend(await self._crawl_district_court_cases(limit))
            else:
                # 모든 법원
                cases.extend(await self._crawl_supreme_court_cases(limit // 3))
                cases.extend(await self._crawl_high_court_cases(limit // 3))
                cases.extend(await self._crawl_district_court_cases(limit // 3))

        except Exception as e:
            logger.error(f"Case crawling error: {e}")

        return cases

    async def _crawl_supreme_court_cases(self, limit: int) -> List[Dict[str, Any]]:
        """대법원 판례 크롤링"""
        cases = []

        try:
            # 대법원 판례 검색 페이지
            search_url = f"{self.base_url}/case/SearchServlet"

            for page in range(1, (limit // 10) + 2):
                params = {
                    'searchType': 'case',
                    'courtType': 'S',  # Supreme Court
                    'page': page,
                    'pageSize': 10,
                    'sortType': 'date',
                    'sortOrder': 'desc'
                }

                url = f"{search_url}?{urlencode(params)}"

                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        page_cases = await self._parse_case_list(html, "대법원")
                        cases.extend(page_cases)

                        if len(cases) >= limit:
                            break

                await asyncio.sleep(1 / self.rate_limit)

        except Exception as e:
            logger.error(f"Supreme Court crawling error: {e}")

        return cases[:limit]

    async def _crawl_high_court_cases(self, limit: int) -> List[Dict[str, Any]]:
        """고등법원 판례 크롤링"""
        cases = []

        try:
            search_url = f"{self.base_url}/case/SearchServlet"

            for page in range(1, (limit // 10) + 2):
                params = {
                    'searchType': 'case',
                    'courtType': 'H',  # High Court
                    'page': page,
                    'pageSize': 10,
                    'sortType': 'date',
                    'sortOrder': 'desc'
                }

                url = f"{search_url}?{urlencode(params)}"

                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        page_cases = await self._parse_case_list(html, "고등법원")
                        cases.extend(page_cases)

                        if len(cases) >= limit:
                            break

                await asyncio.sleep(1 / self.rate_limit)

        except Exception as e:
            logger.error(f"High Court crawling error: {e}")

        return cases[:limit]

    async def _crawl_district_court_cases(self, limit: int) -> List[Dict[str, Any]]:
        """지방법원 판례 크롤링"""
        cases = []

        try:
            search_url = f"{self.base_url}/case/SearchServlet"

            for page in range(1, (limit // 10) + 2):
                params = {
                    'searchType': 'case',
                    'courtType': 'D',  # District Court
                    'page': page,
                    'pageSize': 10,
                    'sortType': 'date',
                    'sortOrder': 'desc'
                }

                url = f"{search_url}?{urlencode(params)}"

                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        page_cases = await self._parse_case_list(html, "지방법원")
                        cases.extend(page_cases)

                        if len(cases) >= limit:
                            break

                await asyncio.sleep(1 / self.rate_limit)

        except Exception as e:
            logger.error(f"District Court crawling error: {e}")

        return cases[:limit]

    async def _parse_case_list(self, html: str, court_name: str) -> List[Dict[str, Any]]:
        """판례 목록 파싱"""
        cases = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 판례 목록 추출
            case_items = soup.select('.case_list_item')

            for item in case_items:
                case_data = {}

                # 사건번호
                case_num_elem = item.select_one('.case_number')
                if case_num_elem:
                    case_data['case_number'] = case_num_elem.text.strip()

                # 판결일
                date_elem = item.select_one('.judgment_date')
                if date_elem:
                    date_str = date_elem.text.strip()
                    case_data['judgment_date'] = self._parse_date(date_str)

                # 사건명/제목
                title_elem = item.select_one('.case_title')
                if title_elem:
                    case_data['title'] = title_elem.text.strip()

                # 판결 요지
                summary_elem = item.select_one('.case_summary')
                if summary_elem:
                    case_data['summary'] = summary_elem.text.strip()

                # 상세 링크
                detail_link = item.select_one('a')
                if detail_link:
                    detail_url = self.base_url + detail_link.get('href', '')
                    # 상세 정보 크롤링
                    detail_data = await self._crawl_case_detail(detail_url)
                    case_data.update(detail_data)

                case_data['court_name'] = court_name
                case_data['source_url'] = detail_url if detail_link else ""

                if case_data.get('case_number'):
                    cases.append(case_data)

        except Exception as e:
            logger.error(f"Case list parsing error: {e}")

        return cases

    async def _crawl_case_detail(self, url: str) -> Dict[str, Any]:
        """판례 상세 정보 크롤링"""
        detail_data = {}

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 전문 추출
                    full_text_elem = soup.select_one('.case_full_text')
                    if full_text_elem:
                        detail_data['full_text'] = full_text_elem.text.strip()

                    # 판시사항
                    decision_elem = soup.select_one('.case_decision')
                    if decision_elem:
                        detail_data['decision'] = decision_elem.text.strip()

                    # 관련 법령
                    related_laws = []
                    law_elems = soup.select('.related_law')
                    for law_elem in law_elems:
                        related_laws.append(law_elem.text.strip())
                    detail_data['related_laws'] = related_laws

                    # 참조 판례
                    reference_cases = []
                    ref_elems = soup.select('.reference_case')
                    for ref_elem in ref_elems:
                        reference_cases.append(ref_elem.text.strip())
                    detail_data['reference_cases'] = reference_cases

        except Exception as e:
            logger.error(f"Case detail crawling error: {e}")

        return detail_data

    async def crawl_law_interpretations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """법령해석 크롤링"""
        interpretations = []

        try:
            # 법제처 법령해석
            moleg_url = "https://www.moleg.go.kr/lawinfo/nwLwAnList.mo"

            for page in range(1, (limit // 10) + 2):
                params = {
                    'mid': 'a10105020000',
                    'currentPage': page,
                    'pageRow': 10
                }

                url = f"{moleg_url}?{urlencode(params)}"

                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        page_interpretations = await self._parse_interpretation_list(html)
                        interpretations.extend(page_interpretations)

                        if len(interpretations) >= limit:
                            break

                await asyncio.sleep(1 / self.rate_limit)

        except Exception as e:
            logger.error(f"Interpretation crawling error: {e}")

        return interpretations[:limit]

    async def _parse_interpretation_list(self, html: str) -> List[Dict[str, Any]]:
        """법령해석 목록 파싱"""
        interpretations = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 해석례 목록
            items = soup.select('.interpretation_item')

            for item in items:
                interp_data = {}

                # 해석례 번호
                num_elem = item.select_one('.interp_number')
                if num_elem:
                    interp_data['interpretation_number'] = num_elem.text.strip()

                # 질의기관
                request_elem = item.select_one('.requesting_agency')
                if request_elem:
                    interp_data['requesting_agency'] = request_elem.text.strip()

                # 회신기관
                response_elem = item.select_one('.responding_agency')
                if response_elem:
                    interp_data['responding_agency'] = response_elem.text.strip()

                # 질의일/회신일
                request_date_elem = item.select_one('.request_date')
                if request_date_elem:
                    interp_data['request_date'] = self._parse_date(request_date_elem.text.strip())

                response_date_elem = item.select_one('.response_date')
                if response_date_elem:
                    interp_data['response_date'] = self._parse_date(response_date_elem.text.strip())

                # 질의 내용
                question_elem = item.select_one('.question')
                if question_elem:
                    interp_data['question'] = question_elem.text.strip()

                # 회신 내용
                answer_elem = item.select_one('.answer')
                if answer_elem:
                    interp_data['answer'] = answer_elem.text.strip()

                if interp_data.get('interpretation_number'):
                    interpretations.append(interp_data)

        except Exception as e:
            logger.error(f"Interpretation parsing error: {e}")

        return interpretations

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # 다양한 날짜 형식 처리
            date_str = date_str.strip()

            # 2024.01.01 형식
            if '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))

            # 2024-01-01 형식
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')

            # 2024년 1월 1일 형식
            elif '년' in date_str:
                pattern = r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
                match = re.match(pattern, date_str)
                if match:
                    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))

        except Exception as e:
            logger.error(f"Date parsing error: {e}")

        return None

    async def save_cases_to_database(self, cases: List[Dict[str, Any]], db: AsyncSession):
        """판례를 데이터베이스에 저장"""
        rag_system = LegalRAGSystem()

        for case_data in cases:
            try:
                # 중복 확인
                stmt = select(LawCase).where(
                    LawCase.case_number == case_data.get('case_number')
                )
                existing = await db.execute(stmt)
                existing_case = existing.scalar_one_or_none()

                if existing_case:
                    # 업데이트
                    for key, value in case_data.items():
                        if hasattr(existing_case, key):
                            setattr(existing_case, key, value)

                    existing_case.updated_at = datetime.now()
                else:
                    # 새로 추가
                    case = LawCase(**case_data)
                    db.add(case)

                    # RAG 시스템에 인덱싱 (판례용 인덱스)
                    # await rag_system.index_case(case)

            except Exception as e:
                logger.error(f"Case save error: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {len(cases)} cases to database")

    async def save_interpretations_to_database(
        self,
        interpretations: List[Dict[str, Any]],
        db: AsyncSession
    ):
        """법령해석을 데이터베이스에 저장"""
        for interp_data in interpretations:
            try:
                # 중복 확인
                stmt = select(LawInterpretation).where(
                    LawInterpretation.interpretation_number == interp_data.get('interpretation_number')
                )
                existing = await db.execute(stmt)
                existing_interp = existing.scalar_one_or_none()

                if existing_interp:
                    # 업데이트
                    for key, value in interp_data.items():
                        if hasattr(existing_interp, key):
                            setattr(existing_interp, key, value)

                    existing_interp.updated_at = datetime.now()
                else:
                    # 새로 추가
                    interpretation = LawInterpretation(**interp_data)
                    db.add(interpretation)

            except Exception as e:
                logger.error(f"Interpretation save error: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {len(interpretations)} interpretations to database")


class CaseAnalyzer:
    """판례 분석기"""

    def __init__(self):
        """판례 분석기 초기화"""
        self.decision_patterns = {
            '원고승': ['원고 승', '원고의 청구를 인용', '피고는.*지급하라'],
            '피고승': ['원고 패', '원고의 청구를 기각', '원고의 청구를 모두 기각'],
            '일부승': ['일부 인용', '일부 기각', '일부만 인용'],
            '파기환송': ['파기하고.*환송', '파기 환송'],
            '상고기각': ['상고를 기각', '상고를 모두 기각'],
            '각하': ['각하한다', '상고를 각하']
        }

    def analyze_decision(self, case_text: str) -> str:
        """판결 분석"""
        for decision_type, patterns in self.decision_patterns.items():
            for pattern in patterns:
                if re.search(pattern, case_text):
                    return decision_type

        return "기타"

    def extract_legal_principles(self, case_text: str) -> List[str]:
        """법리 추출"""
        principles = []

        # 판시사항 패턴
        principle_patterns = [
            r'【판시사항】([^【]+)',
            r'【법리】([^【]+)',
            r'【판결요지】([^【]+)'
        ]

        for pattern in principle_patterns:
            matches = re.finditer(pattern, case_text)
            for match in matches:
                principle = match.group(1).strip()
                if principle:
                    principles.append(principle)

        return principles

    def extract_key_issues(self, case_text: str) -> List[str]:
        """핵심 쟁점 추출"""
        issues = []

        # 쟁점 패턴
        issue_patterns = [
            r'쟁점[은는]\s*([^.。]+)[.。]',
            r'문제[는은]\s*([^.。]+)[.。]',
            r'판단하건대[,，]\s*([^.。]+)[.。]'
        ]

        for pattern in issue_patterns:
            matches = re.finditer(pattern, case_text)
            for match in matches:
                issue = match.group(1).strip()
                if issue:
                    issues.append(issue)

        return issues