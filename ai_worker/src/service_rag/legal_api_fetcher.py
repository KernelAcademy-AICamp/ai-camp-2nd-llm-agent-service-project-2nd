"""
국가법령정보 공동활용 API 클라이언트

법령 및 판례 데이터를 API로부터 수집합니다.
API 문서: https://open.law.go.kr/LSO/main.do

인증 방식: OC 파라미터 (회원 ID)
"""

import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StatuteArticle:
    """조문 데이터"""
    law_name: str           # 법령명 (예: 민법)
    article_number: str     # 조항 번호 (예: 제840조)
    article_title: str      # 조문 제목
    content: str            # 조문 내용
    effective_date: Optional[str] = None
    law_id: Optional[str] = None  # 법령 고유 ID


@dataclass
class PrecedentData:
    """판례 데이터"""
    case_number: str        # 사건번호 (예: 2022다12345)
    court_name: str         # 법원명
    case_type: str          # 사건 유형
    judgment_date: str      # 판결일
    summary: str            # 판시사항/요지
    full_text: Optional[str] = None  # 전문
    precedent_id: Optional[str] = None


class LegalAPIClient:
    """
    국가법령정보 공동활용 API 클라이언트

    사용법:
        client = LegalAPIClient(member_id="your_member_id")
        articles = client.get_statute_articles("민법", "840")
    """

    BASE_URL = "http://www.law.go.kr/DRF"

    def __init__(self, member_id: Optional[str] = None):
        """
        Args:
            member_id: 국가법령정보 공동활용 회원 ID (OC 파라미터)
                       환경변수 LAW_API_MEMBER_ID로도 설정 가능
        """
        self.member_id = member_id or os.getenv("LAW_API_MEMBER_ID", "")
        if not self.member_id:
            logger.warning("LAW_API_MEMBER_ID not set. API calls may fail.")

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Optional[ET.Element]:
        """API 요청 실행"""
        params["OC"] = self.member_id
        params["type"] = "XML"

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.content)
            return root

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return None

    def search_statutes(self, query: str, page: int = 1, rows: int = 20) -> List[Dict]:
        """
        법령 검색

        Args:
            query: 검색어 (예: "민법", "이혼")
            page: 페이지 번호
            rows: 페이지당 결과 수

        Returns:
            검색된 법령 목록
        """
        params = {
            "target": "law",
            "query": query,
            "page": page,
            "display": rows
        }

        root = self._request("lawSearch.do", params)
        if root is None:
            return []

        results = []
        for law in root.findall(".//law"):
            results.append({
                "law_id": self._get_text(law, "법령ID"),
                "law_name": self._get_text(law, "법령명한글"),
                "law_type": self._get_text(law, "법령구분명"),
                "law_number": self._get_text(law, "법령일련번호"),
                "promulgation_date": self._get_text(law, "공포일자"),
                "effective_date": self._get_text(law, "시행일자")
            })

        return results

    def get_statute_detail(self, law_id: str) -> Optional[Dict]:
        """
        법령 상세 정보 조회

        Args:
            law_id: 법령 ID (MST 값)

        Returns:
            법령 상세 정보
        """
        params = {
            "target": "law",
            "MST": law_id
        }

        root = self._request("lawService.do", params)
        if root is None:
            return None

        # 기본 정보
        base_info = root.find(".//기본정보")
        if base_info is None:
            return None

        return {
            "law_id": law_id,
            "law_name": self._get_text(base_info, "법령명_한글"),
            "law_type": self._get_text(base_info, "법령구분"),
            "promulgation_date": self._get_text(base_info, "공포일자"),
            "effective_date": self._get_text(base_info, "시행일자"),
            "articles": self._parse_articles(root)
        }

    def get_article(self, law_id: str, article_number: str) -> Optional[StatuteArticle]:
        """
        특정 조문 조회

        Args:
            law_id: 법령 ID (MST 값)
            article_number: 조문 번호 (예: "840" -> 제840조)

        Returns:
            조문 데이터
        """
        # 조문 번호 형식: 0084000 (7자리, 앞 5자리가 조번호, 뒤 2자리가 항번호)
        jo_number = article_number.zfill(5) + "00"

        params = {
            "target": "jo",
            "MST": law_id,
            "JO": jo_number
        }

        root = self._request("lawService.do", params)
        if root is None:
            return None

        jo_elem = root.find(".//조문")
        if jo_elem is None:
            return None

        return StatuteArticle(
            law_name=self._get_text(root, ".//법령명_한글") or "",
            article_number=f"제{article_number}조",
            article_title=self._get_text(jo_elem, "조문제목") or "",
            content=self._get_text(jo_elem, "조문내용") or "",
            effective_date=self._get_text(root, ".//시행일자"),
            law_id=law_id
        )

    def get_civil_law_divorce_articles(self) -> List[StatuteArticle]:
        """
        민법 이혼 관련 조문 조회 (제834조 ~ 제843조)

        법령 전체를 가져온 후 이혼 관련 조문만 추출합니다.

        Returns:
            이혼 관련 조문 목록
        """
        # 민법 최신 버전 법령 ID (MST)
        # 법령일련번호는 버전마다 다르므로 검색으로 최신 ID를 가져옴
        CIVIL_LAW_MST = "265307"  # 민법 최신 버전

        logger.info("민법 전체 조문 가져오는 중...")

        # 민법 전체 가져오기 (timeout 증가)
        params = {
            "target": "law",
            "MST": CIVIL_LAW_MST,
            "OC": self.member_id,
            "type": "XML"
        }

        url = f"{self.BASE_URL}/lawService.do"

        try:
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except Exception as e:
            logger.error(f"Failed to fetch civil law: {e}")
            return []

        # 이혼 관련 조문 번호 범위 (834 ~ 843)
        divorce_range = range(834, 844)

        articles = []
        for jo in root.findall(".//조문단위"):
            jo_num_elem = jo.find("조문번호")
            jo_title_elem = jo.find("조문제목")
            jo_content_elem = jo.find("조문내용")

            if jo_num_elem is None or jo_num_elem.text is None:
                continue

            try:
                jo_num = int(jo_num_elem.text)
            except ValueError:
                continue

            # 이혼 관련 조문만 추출 (834 ~ 843)
            if jo_num in divorce_range:
                title = jo_title_elem.text.strip() if jo_title_elem is not None and jo_title_elem.text else ""
                content = jo_content_elem.text.strip() if jo_content_elem is not None and jo_content_elem.text else ""

                # 빈 조문 건너뛰기 (편/장/절 제목 등)
                if not content or len(content) < 10:
                    continue

                article = StatuteArticle(
                    law_name="민법",
                    article_number=f"제{jo_num}조",
                    article_title=title,
                    content=content,
                    effective_date=None,
                    law_id=CIVIL_LAW_MST
                )
                articles.append(article)
                logger.info(f"Fetched: 민법 제{jo_num}조 - {title}")

        logger.info(f"총 {len(articles)}개 이혼 관련 조문 추출 완료")
        return articles

    def search_precedents(self, query: str, page: int = 1, rows: int = 20) -> List[Dict]:
        """
        판례 검색

        Args:
            query: 검색어 (예: "이혼", "재산분할")
            page: 페이지 번호
            rows: 페이지당 결과 수

        Returns:
            검색된 판례 목록
        """
        params = {
            "target": "prec",
            "query": query,
            "page": page,
            "display": rows
        }

        root = self._request("lawSearch.do", params)
        if root is None:
            return []

        results = []
        for prec in root.findall(".//prec"):
            results.append({
                "prec_id": self._get_text(prec, "판례일련번호"),
                "case_number": self._get_text(prec, "사건번호"),
                "case_name": self._get_text(prec, "사건명"),
                "court_name": self._get_text(prec, "법원명"),
                "judgment_date": self._get_text(prec, "선고일자"),
                "case_type": self._get_text(prec, "사건종류명")
            })

        return results

    def get_precedent_detail(self, prec_id: str) -> Optional[PrecedentData]:
        """
        판례 상세 조회

        Args:
            prec_id: 판례 일련번호

        Returns:
            판례 상세 데이터
        """
        params = {
            "target": "prec",
            "ID": prec_id
        }

        root = self._request("lawService.do", params)
        if root is None:
            return None

        prec_elem = root.find(".//판례정보")
        if prec_elem is None:
            return None

        return PrecedentData(
            case_number=self._get_text(prec_elem, "사건번호") or "",
            court_name=self._get_text(prec_elem, "법원명") or "",
            case_type=self._get_text(prec_elem, "사건종류명") or "",
            judgment_date=self._get_text(prec_elem, "선고일자") or "",
            summary=self._get_text(prec_elem, "판시사항") or self._get_text(prec_elem, "판결요지") or "",
            full_text=self._get_text(prec_elem, "판례내용"),
            precedent_id=prec_id
        )

    def get_divorce_precedents(self, max_count: int = 50) -> List[PrecedentData]:
        """
        이혼 관련 주요 판례 조회

        Args:
            max_count: 최대 수집 개수

        Returns:
            이혼 관련 판례 목록
        """
        # 이혼 관련 검색어
        search_terms = ["이혼", "재산분할", "양육권", "위자료"]

        all_precedents = []
        seen_ids = set()

        for term in search_terms:
            if len(all_precedents) >= max_count:
                break

            results = self.search_precedents(term, rows=20)

            for prec_info in results:
                if len(all_precedents) >= max_count:
                    break

                prec_id = prec_info.get("prec_id")
                if prec_id and prec_id not in seen_ids:
                    seen_ids.add(prec_id)

                    try:
                        detail = self.get_precedent_detail(prec_id)
                        if detail:
                            all_precedents.append(detail)
                            logger.info(f"Fetched precedent: {detail.case_number}")
                    except Exception as e:
                        logger.error(f"Failed to fetch precedent {prec_id}: {e}")

        return all_precedents

    def _parse_articles(self, root: ET.Element) -> List[Dict]:
        """조문 목록 파싱"""
        articles = []
        for jo in root.findall(".//조문"):
            articles.append({
                "article_number": self._get_text(jo, "조문번호"),
                "article_title": self._get_text(jo, "조문제목"),
                "content": self._get_text(jo, "조문내용")
            })
        return articles

    @staticmethod
    def _get_text(elem: ET.Element, tag: str) -> Optional[str]:
        """XML 엘리먼트에서 텍스트 추출"""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None


# ============================================
# 테스트 실행
# ============================================
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # 회원 ID 입력
    member_id = os.getenv("LAW_API_MEMBER_ID")
    if not member_id:
        print("환경변수 LAW_API_MEMBER_ID를 설정하거나,")
        print("실행 시 인자로 회원 ID를 전달하세요.")
        print("\n사용법: python legal_api_fetcher.py <회원ID>")
        if len(sys.argv) > 1:
            member_id = sys.argv[1]
        else:
            sys.exit(1)

    client = LegalAPIClient(member_id=member_id)

    print("\n=== 민법 검색 테스트 ===")
    results = client.search_statutes("민법", rows=5)
    for r in results:
        print(f"  - {r['law_name']} ({r['law_id']})")

    print("\n=== 이혼 관련 조문 수집 테스트 ===")
    articles = client.get_civil_law_divorce_articles()
    for art in articles[:3]:  # 처음 3개만 출력
        print(f"\n{art.article_number}: {art.article_title}")
        print(f"  내용: {art.content[:100]}...")

    print(f"\n총 {len(articles)}개 조문 수집 완료")
