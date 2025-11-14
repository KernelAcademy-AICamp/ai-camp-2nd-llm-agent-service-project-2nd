"""
법률 조항 크롤링 시스템
"""

import re
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
from urllib.parse import quote, urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logging import logger
from app.models.law import Law, LawCategory, LawUpdate
from app.database.session import get_db
from app.services.rag.retriever import LegalRAGSystem


class LawCrawler:
    """법률 조항 크롤러 기본 클래스"""

    def __init__(self):
        """크롤러 초기화"""
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.rate_limit = 1  # 초당 요청 수
        self.last_request_time = datetime.now()

    async def __aenter__(self):
        """비동기 컨텍스트 진입"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 종료"""
        if self.session:
            await self.session.close()

    async def _rate_limit_wait(self):
        """요청 속도 제한"""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < 1 / self.rate_limit:
            await asyncio.sleep(1 / self.rate_limit - elapsed)
        self.last_request_time = datetime.now()

    async def fetch(self, url: str) -> str:
        """URL에서 데이터 가져오기"""
        await self._rate_limit_wait()

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise


class KoreanLawCrawler(LawCrawler):
    """한국 법령정보센터 크롤러"""

    def __init__(self):
        """한국 법령 크롤러 초기화"""
        super().__init__()
        self.base_url = "https://www.law.go.kr"
        self.api_key = settings.LAW_API_KEY  # 법령정보센터 API 키

        # 주요 법률 카테고리
        self.categories = {
            "헌법": ["헌법"],
            "민법": ["민법", "민사소송법", "민사집행법"],
            "형법": ["형법", "형사소송법"],
            "상법": ["상법", "회사법", "어음법", "수표법"],
            "행정법": ["행정기본법", "행정절차법", "행정소송법"],
            "노동법": ["근로기준법", "노동조합법", "최저임금법", "산업안전보건법"],
            "부동산법": ["부동산등기법", "주택임대차보호법", "상가건물임대차보호법"],
            "세법": ["국세기본법", "소득세법", "법인세법", "부가가치세법"],
            "지적재산권법": ["특허법", "상표법", "저작권법", "디자인보호법"],
            "정보통신법": ["정보통신망법", "개인정보보호법", "전자상거래법"]
        }

    async def crawl_all_laws(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """모든 법률 크롤링"""
        all_laws = []

        for category, law_names in self.categories.items():
            logger.info(f"Crawling category: {category}")

            for law_name in law_names:
                try:
                    laws = await self.crawl_law_by_name(law_name, category)
                    all_laws.extend(laws)

                    if limit and len(all_laws) >= limit:
                        return all_laws[:limit]

                except Exception as e:
                    logger.error(f"Error crawling {law_name}: {e}")
                    continue

        return all_laws

    async def crawl_law_by_name(self, law_name: str, category: str) -> List[Dict[str, Any]]:
        """특정 법률명으로 크롤링"""
        # Open API 사용 (법령정보센터)
        if self.api_key:
            return await self._crawl_via_api(law_name, category)
        else:
            # API 키가 없으면 웹 스크래핑
            return await self._crawl_via_web(law_name, category)

    async def _crawl_via_api(self, law_name: str, category: str) -> List[Dict[str, Any]]:
        """API를 통한 크롤링"""
        laws = []

        # 법령 검색 API
        search_url = f"{self.base_url}/DRF/lawSearch.do"
        params = {
            'OC': self.api_key,
            'target': 'law',
            'query': law_name,
            'type': 'XML'
        }

        try:
            url = f"{search_url}?{urlencode(params)}"
            xml_data = await self.fetch(url)

            # XML 파싱
            root = ET.fromstring(xml_data)

            for law_elem in root.findall('.//law'):
                law_id = law_elem.find('법령ID').text if law_elem.find('법령ID') is not None else None

                if law_id:
                    # 법령 상세 정보 조회
                    detail_data = await self._fetch_law_detail(law_id, category)
                    if detail_data:
                        laws.extend(detail_data)

        except Exception as e:
            logger.error(f"API crawling error: {e}")

        return laws

    async def _fetch_law_detail(self, law_id: str, category: str) -> List[Dict[str, Any]]:
        """법령 상세 정보 조회"""
        detail_url = f"{self.base_url}/DRF/lawService.do"
        params = {
            'OC': self.api_key,
            'target': 'law',
            'ID': law_id,
            'type': 'XML',
            'mobileYn': 'N'
        }

        articles = []

        try:
            url = f"{detail_url}?{urlencode(params)}"
            xml_data = await self.fetch(url)

            # XML 파싱
            root = ET.fromstring(xml_data)

            # 법령 기본 정보
            law_name = root.find('.//법령명_한글').text if root.find('.//법령명_한글') is not None else ""
            law_abbr = root.find('.//법령약칭명').text if root.find('.//법령약칭명') is not None else ""
            enforcement_date = root.find('.//시행일자').text if root.find('.//시행일자') is not None else None

            # 조문 파싱
            for article in root.findall('.//조문'):
                article_num = article.find('조문번호').text if article.find('조문번호') is not None else ""
                article_title = article.find('조문제목').text if article.find('조문제목') is not None else ""
                article_content = article.find('조문내용').text if article.find('조문내용') is not None else ""

                # 항 파싱
                paragraphs = []
                for para in article.findall('.//항'):
                    para_num = para.find('항번호').text if para.find('항번호') is not None else ""
                    para_content = para.find('항내용').text if para.find('항내용') is not None else ""
                    paragraphs.append({
                        'number': para_num,
                        'content': para_content
                    })

                article_data = {
                    'law_id': law_id,
                    'law_name': law_name,
                    'law_name_abbr': law_abbr,
                    'category': category,
                    'article_number': article_num,
                    'article_title': article_title,
                    'article_content': article_content,
                    'paragraphs': paragraphs,
                    'enforcement_date': self._parse_date(enforcement_date),
                    'is_active': True,
                    'source_url': f"{self.base_url}/LSW/lsInfoP.do?lsiSeq={law_id}"
                }

                articles.append(article_data)

        except Exception as e:
            logger.error(f"Detail fetching error for law_id {law_id}: {e}")

        return articles

    async def _crawl_via_web(self, law_name: str, category: str) -> List[Dict[str, Any]]:
        """웹 스크래핑을 통한 크롤링"""
        laws = []

        # 검색 URL
        search_url = f"{self.base_url}/LSW/main.html"

        try:
            # 검색 수행
            search_params = {
                'query': law_name,
                'menuId': '0'
            }

            url = f"{search_url}?{urlencode(search_params)}"
            html = await self.fetch(url)

            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(html, 'html.parser')

            # 검색 결과에서 법령 링크 추출
            law_links = soup.select('.law_list a')

            for link in law_links[:5]:  # 상위 5개만
                law_url = self.base_url + link.get('href', '')
                law_detail = await self._scrape_law_detail(law_url, category)
                if law_detail:
                    laws.extend(law_detail)

        except Exception as e:
            logger.error(f"Web scraping error: {e}")

        return laws

    async def _scrape_law_detail(self, url: str, category: str) -> List[Dict[str, Any]]:
        """법령 상세 페이지 스크래핑"""
        articles = []

        try:
            html = await self.fetch(url)
            soup = BeautifulSoup(html, 'html.parser')

            # 법령명 추출
            law_name = soup.select_one('.law_title').text.strip() if soup.select_one('.law_title') else ""

            # 조문 추출
            article_elements = soup.select('.article')

            for elem in article_elements:
                article_num = elem.select_one('.article_num').text.strip() if elem.select_one('.article_num') else ""
                article_title = elem.select_one('.article_title').text.strip() if elem.select_one('.article_title') else ""
                article_content = elem.select_one('.article_content').text.strip() if elem.select_one('.article_content') else ""

                article_data = {
                    'law_name': law_name,
                    'category': category,
                    'article_number': article_num,
                    'article_title': article_title,
                    'article_content': article_content,
                    'source_url': url,
                    'is_active': True
                }

                articles.append(article_data)

        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")

        return articles

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # YYYYMMDD 형식
            if len(date_str) == 8:
                return datetime.strptime(date_str, '%Y%m%d')
            # YYYY-MM-DD 형식
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            # YYYY.MM.DD 형식
            elif '.' in date_str:
                return datetime.strptime(date_str, '%Y.%m.%d')
        except Exception as e:
            logger.error(f"Date parsing error: {e}")

        return None

    async def save_to_database(self, laws: List[Dict[str, Any]], db: AsyncSession):
        """크롤링된 법률을 데이터베이스에 저장"""
        rag_system = LegalRAGSystem()

        for law_data in laws:
            try:
                # 중복 확인
                stmt = select(Law).where(
                    Law.law_name == law_data['law_name'],
                    Law.article_number == law_data['article_number']
                )
                existing = await db.execute(stmt)
                existing_law = existing.scalar_one_or_none()

                if existing_law:
                    # 업데이트
                    for key, value in law_data.items():
                        if hasattr(existing_law, key):
                            setattr(existing_law, key, value)

                    existing_law.updated_at = datetime.now()
                    existing_law.last_crawled_at = datetime.now()
                else:
                    # 새로 추가
                    law = Law(**law_data)
                    law.last_crawled_at = datetime.now()
                    db.add(law)

                    # RAG 시스템에 인덱싱
                    await rag_system.index_law(law)

            except Exception as e:
                logger.error(f"Database save error: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {len(laws)} laws to database")

    async def update_laws(self, db: AsyncSession):
        """법률 업데이트 확인 및 적용"""
        # 최근 업데이트된 법률 조회
        update_url = f"{self.base_url}/DRF/lawUpdateList.do"
        params = {
            'OC': self.api_key,
            'fromDate': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
            'toDate': datetime.now().strftime('%Y%m%d'),
            'type': 'XML'
        }

        try:
            url = f"{update_url}?{urlencode(params)}"
            xml_data = await self.fetch(url)

            # XML 파싱
            root = ET.fromstring(xml_data)

            for update_elem in root.findall('.//lawUpdate'):
                law_id = update_elem.find('법령ID').text
                update_type = update_elem.find('제개정구분').text
                update_date = update_elem.find('공포일자').text

                # 상세 정보 조회 및 업데이트
                detail_data = await self._fetch_law_detail(law_id, "")
                if detail_data:
                    await self.save_to_database(detail_data, db)

                    # 업데이트 이력 저장
                    law_update = LawUpdate(
                        law_id=law_id,
                        update_type=update_type,
                        update_date=self._parse_date(update_date),
                        update_content=f"{update_type} on {update_date}"
                    )
                    db.add(law_update)

            await db.commit()

        except Exception as e:
            logger.error(f"Update check error: {e}")


class LawCategoryManager:
    """법률 카테고리 관리"""

    def __init__(self):
        """카테고리 매니저 초기화"""
        self.categories = {
            "헌법": {
                "parent": None,
                "description": "대한민국 헌법",
                "icon": "⚖️"
            },
            "민법": {
                "parent": None,
                "description": "민사 관계 법률",
                "icon": "📜"
            },
            "형법": {
                "parent": None,
                "description": "형사 관계 법률",
                "icon": "⚔️"
            },
            "상법": {
                "parent": None,
                "description": "상거래 관계 법률",
                "icon": "💼"
            },
            "행정법": {
                "parent": None,
                "description": "행정 관계 법률",
                "icon": "🏛️"
            },
            "노동법": {
                "parent": None,
                "description": "근로 관계 법률",
                "icon": "👷"
            },
            "부동산법": {
                "parent": None,
                "description": "부동산 관계 법률",
                "icon": "🏠"
            },
            "세법": {
                "parent": None,
                "description": "조세 관계 법률",
                "icon": "💰"
            },
            "지적재산권법": {
                "parent": None,
                "description": "지적재산권 관계 법률",
                "icon": "💡"
            },
            "정보통신법": {
                "parent": None,
                "description": "정보통신 관계 법률",
                "icon": "💻"
            }
        }

    async def initialize_categories(self, db: AsyncSession):
        """데이터베이스에 카테고리 초기화"""
        for name, info in self.categories.items():
            # 중복 확인
            stmt = select(LawCategory).where(LawCategory.name == name)
            existing = await db.execute(stmt)
            category = existing.scalar_one_or_none()

            if not category:
                category = LawCategory(
                    name=name,
                    parent_id=info['parent'],
                    description=info['description'],
                    icon=info['icon'],
                    is_active=True
                )
                db.add(category)

        await db.commit()
        logger.info("Law categories initialized")


class LawSearchOptimizer:
    """법률 검색 최적화"""

    def __init__(self):
        """검색 최적화 초기화"""
        self.common_terms = {
            '계약': ['계약서', '약정', '합의'],
            '손해배상': ['배상', '손해', '피해'],
            '해지': ['해제', '취소', '파기'],
            '임대차': ['임대', '임차', '전세', '월세'],
            '근로': ['노동', '고용', '취업']
        }

    def expand_search_terms(self, query: str) -> List[str]:
        """검색어 확장"""
        expanded = [query]

        for base, synonyms in self.common_terms.items():
            if base in query:
                for synonym in synonyms:
                    expanded.append(query.replace(base, synonym))

        return list(set(expanded))

    def optimize_query(self, query: str) -> str:
        """검색 쿼리 최적화"""
        # 불필요한 조사 제거
        particles = ['은', '는', '이', '가', '을', '를', '에', '에서', '으로', '로']
        for particle in particles:
            query = query.replace(particle, ' ')

        # 공백 정리
        query = ' '.join(query.split())

        return query