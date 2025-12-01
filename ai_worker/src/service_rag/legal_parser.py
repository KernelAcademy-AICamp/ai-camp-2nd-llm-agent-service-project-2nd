"""
Legal Parser Module
법령과 판례 텍스트 파싱
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.service_rag.schemas import Statute, CaseLaw


class StatuteParser:
    """
    법령 파서

    Given: 법령 텍스트
    When: parse() 호출
    Then: Statute 객체 반환
    """

    def __init__(self):
        """초기화"""
        # 법령 패턴: "민법 제840조(이혼원인)"
        self.statute_pattern = re.compile(r"(\S+)\s+(제\d+조(?:의\d+)?)")
        self.article_pattern = re.compile(r"제\d+조(?:의\d+)?")

    def parse(
        self,
        text: str,
        statute_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Statute:
        """
        법령 텍스트 파싱

        Args:
            text: 법령 조문 텍스트
            statute_id: 법령 고유 ID (없으면 UUID 생성)
            metadata: 추가 메타데이터

        Returns:
            Statute: 파싱된 법령 객체

        Raises:
            ValueError: 빈 텍스트인 경우
        """
        if not text or text.strip() == "":
            raise ValueError("Empty statute text")

        text = text.strip()
        metadata = metadata or {}

        # statute_id 생성
        if not statute_id:
            statute_id = str(uuid.uuid4())

        # 법령명 추출
        statute_name = self._extract_statute_name(text)

        # 조항 번호 추출
        article_number = self._extract_article_number(text)

        # 내용 추출 (전체 텍스트 사용)
        content = text

        # effective_date 파싱 (문자열이면 date로 변환)
        effective_date = metadata.get("effective_date")
        if effective_date and isinstance(effective_date, str):
            effective_date = datetime.strptime(effective_date, "%Y-%m-%d").date()

        return Statute(
            statute_id=statute_id,
            name=statute_name,
            statute_number=metadata.get("statute_number"),
            article_number=article_number,
            content=content,
            effective_date=effective_date,
            category=metadata.get("category", "일반")
        )

    def _extract_statute_name(self, text: str) -> str:
        """
        법령명 추출

        Args:
            text: 법령 텍스트

        Returns:
            str: 법령명 (예: "민법")
        """
        match = self.statute_pattern.search(text)
        if match:
            return match.group(1)

        # 패턴 매칭 실패 시 첫 단어 사용
        first_line = text.split("\n")[0]
        first_word = first_line.split()[0] if first_line.split() else "법령"
        return first_word

    def _extract_article_number(self, text: str) -> str:
        """
        조항 번호 추출

        Args:
            text: 법령 텍스트

        Returns:
            str: 조항 번호 (예: "제840조")
        """
        match = self.article_pattern.search(text)
        if match:
            return match.group(0)

        # 패턴 매칭 실패 시 기본값
        return "제0조"

    def parse_batch(self, texts: List[str]) -> List[Statute]:
        """
        여러 법령 조문 일괄 파싱

        Args:
            texts: 법령 텍스트 리스트

        Returns:
            List[Statute]: 파싱된 법령 객체 리스트
        """
        results = []
        for text in texts:
            statute = self.parse(text)
            results.append(statute)
        return results


class CaseLawParser:
    """
    판례 파서

    Given: 판례 텍스트
    When: parse() 호출
    Then: CaseLaw 객체 반환
    """

    def __init__(self):
        """초기화"""
        self.case_number_pattern = re.compile(r"사건번호:\s*(\S+)")
        self.court_pattern = re.compile(r"법원:\s*(.+)")
        self.date_pattern = re.compile(r"선고일:\s*(\d{4}-\d{2}-\d{2})")
        self.case_name_pattern = re.compile(r"사건명:\s*(.+)")
        self.summary_pattern = re.compile(r"\[판결 요지\](.*?)(?:\[판결 전문\]|$)", re.DOTALL)

    def parse(
        self,
        text: str,
        case_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CaseLaw:
        """
        판례 텍스트 파싱

        Args:
            text: 판례 텍스트
            case_id: 판례 고유 ID (없으면 UUID 생성)
            metadata: 추가 메타데이터

        Returns:
            CaseLaw: 파싱된 판례 객체

        Raises:
            ValueError: 빈 텍스트이거나 필수 필드 누락 시
        """
        if not text or text.strip() == "":
            raise ValueError("Empty case text")

        text = text.strip()
        metadata = metadata or {}

        # case_id 생성
        if not case_id:
            case_id = str(uuid.uuid4())

        # 필수 필드 추출
        case_number = self._extract_case_number(text)
        court = self._extract_court(text)
        decision_date_str = self._extract_decision_date(text)
        case_name = self._extract_case_name(text)
        summary = self._extract_summary(text)

        # 필수 필드 검증
        if not all([case_number, court, decision_date_str, case_name, summary]):
            raise ValueError("Missing required fields in case text")

        # 날짜 파싱
        decision_date = datetime.strptime(decision_date_str, "%Y-%m-%d").date()

        # 판결 전문 추출 (있으면)
        full_text = self._extract_full_text(text)

        return CaseLaw(
            case_id=case_id,
            case_number=case_number,
            court=court,
            decision_date=decision_date,
            case_name=case_name,
            summary=summary,
            full_text=full_text,
            related_statutes=metadata.get("related_statutes", []),
            category=metadata.get("category", "가사")
        )

    def _extract_case_number(self, text: str) -> Optional[str]:
        """사건번호 추출"""
        match = self.case_number_pattern.search(text)
        return match.group(1) if match else None

    def _extract_court(self, text: str) -> Optional[str]:
        """법원 추출"""
        match = self.court_pattern.search(text)
        return match.group(1).strip() if match else None

    def _extract_decision_date(self, text: str) -> Optional[str]:
        """선고일 추출"""
        match = self.date_pattern.search(text)
        return match.group(1) if match else None

    def _extract_case_name(self, text: str) -> Optional[str]:
        """사건명 추출"""
        match = self.case_name_pattern.search(text)
        return match.group(1).strip() if match else None

    def _extract_summary(self, text: str) -> Optional[str]:
        """판결 요지 추출"""
        match = self.summary_pattern.search(text)
        if match:
            summary = match.group(1).strip()
            return summary
        return None

    def _extract_full_text(self, text: str) -> Optional[str]:
        """판결 전문 추출"""
        full_text_pattern = re.compile(r"\[판결 전문\](.*)", re.DOTALL)
        match = full_text_pattern.search(text)
        if match:
            return match.group(1).strip()
        return None

    def parse_batch(self, texts: List[str]) -> List[CaseLaw]:
        """
        여러 판례 일괄 파싱

        Args:
            texts: 판례 텍스트 리스트

        Returns:
            List[CaseLaw]: 파싱된 판례 객체 리스트
        """
        results = []
        for text in texts:
            case_law = self.parse(text)
            results.append(case_law)
        return results


class LegalParser:
    """
    법률 문서 통합 파서

    법령과 판례를 파싱하는 통합 인터페이스
    """

    def __init__(self):
        """초기화 - 내부 파서 생성"""
        self.statute_parser = StatuteParser()
        self.case_parser = CaseLawParser()

    def parse_statute(
        self,
        text: str,
        statute_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Statute:
        """
        법령 파싱

        Args:
            text: 법령 텍스트
            statute_id: 법령 ID
            metadata: 메타데이터

        Returns:
            Statute: 파싱된 법령
        """
        return self.statute_parser.parse(text, statute_id, metadata)

    def parse_case(
        self,
        text: str,
        case_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CaseLaw:
        """
        판례 파싱

        Args:
            text: 판례 텍스트
            case_id: 판례 ID
            metadata: 메타데이터

        Returns:
            CaseLaw: 파싱된 판례
        """
        return self.case_parser.parse(text, case_id, metadata)
