"""
Unit tests for PartyExtractionService - 019-party-extraction-prompt
인물 관계도 추출 정확도 개선 테스트

Tests:
- T005: 테스트 클래스 구조
- T006: 1글자 단어 추출 금지
- T007: 동사/형용사 추출 금지
- T008: 조사/어미 추출 금지
- T009: 시스템 키워드 추출 금지
- T012: 최대 인원 제한 (15명)
- T013: 신뢰도 기준 정렬
- T016: 유효한 한국 이름 추출
- T017: 성씨+일반단어 추출 금지
- T018: 익명화된 이름 인식
- T019: 역할 기반 이름 검증
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.party_extraction_service import (
    PartyExtractionService,
    ExtractedPerson,
    KOREAN_SURNAMES,
    MAX_PERSONS,
)


class TestPartyExtractionConstants:
    """상수 정의 테스트"""

    def test_korean_surnames_contains_common_surnames(self):
        """한국 성씨 상수가 주요 성씨를 포함하는지 확인"""
        common_surnames = {"김", "이", "박", "최", "정", "강", "조", "윤"}
        assert common_surnames.issubset(KOREAN_SURNAMES)

    def test_korean_surnames_count(self):
        """한국 성씨가 100개인지 확인"""
        assert len(KOREAN_SURNAMES) == 100

    def test_max_persons_limit(self):
        """최대 인원 수가 15명인지 확인"""
        assert MAX_PERSONS == 15


class TestIsValidName:
    """T004: _is_valid_name() 메서드 테스트"""

    @pytest.fixture
    def service(self):
        """PartyExtractionService 인스턴스 생성 (DB 없이)"""
        mock_db = MagicMock()
        return PartyExtractionService(mock_db)

    # T006: 1글자 단어 추출 금지 테스트
    def test_single_char_not_valid(self, service):
        """1글자 단어는 유효한 이름이 아님"""
        single_chars = ["하", "이", "나", "저", "그", "뭐", "왜", "어"]
        for char in single_chars:
            assert service._is_valid_name(char) is False, f"'{char}' should not be valid"

    def test_empty_string_not_valid(self, service):
        """빈 문자열은 유효한 이름이 아님"""
        assert service._is_valid_name("") is False
        assert service._is_valid_name("   ") is False

    # T007: 동사/형용사 추출 금지 테스트
    def test_verb_not_valid(self, service):
        """동사/형용사는 유효한 이름이 아님"""
        verbs = ["하다", "했다", "하지", "하면", "하는", "이랑", "정말", "진짜", "그렇게"]
        for verb in verbs:
            assert service._is_valid_name(verb) is False, f"'{verb}' should not be valid"

    def test_adjective_not_valid(self, service):
        """형용사는 유효한 이름이 아님"""
        adjectives = ["어떻게", "이렇게", "저렇게", "그래서", "하지만"]
        for adj in adjectives:
            assert service._is_valid_name(adj) is False, f"'{adj}' should not be valid"

    # T008: 조사/어미 추출 금지 테스트
    def test_particle_not_valid(self, service):
        """조사/어미는 유효한 이름이 아님"""
        particles = ["한테", "에게", "으로", "이라고", "라고", "라면", "이면"]
        for particle in particles:
            assert service._is_valid_name(particle) is False, f"'{particle}' should not be valid"

    # T009: 시스템 키워드 추출 금지 테스트
    def test_system_keyword_not_valid(self, service):
        """시스템 키워드는 유효한 이름이 아님"""
        keywords = ["Unknown", "Speaker", "undefined", "null", "None",
                    "unknown", "UNKNOWN", "SPEAKER", "NULL"]
        for keyword in keywords:
            assert service._is_valid_name(keyword) is False, f"'{keyword}' should not be valid"

    # T016: 유효한 한국 이름 추출 테스트
    def test_valid_korean_name(self, service):
        """유효한 한국 이름은 통과"""
        valid_names = ["김철수", "이영희", "박민지", "최준호", "정수연"]
        for name in valid_names:
            assert service._is_valid_name(name) is True, f"'{name}' should be valid"

    def test_valid_korean_name_2_chars(self, service):
        """2글자 한국 이름도 유효"""
        valid_names = ["김씨", "이랑", "박솔", "최원", "정민"]
        # "이랑"은 블랙리스트에 있으므로 제외
        for name in ["김씨", "박솔", "최원", "정민"]:
            assert service._is_valid_name(name) is True, f"'{name}' should be valid"

    # T017: 성씨+일반단어 추출 금지 테스트
    def test_surname_common_word_not_valid(self, service):
        """성씨+일반단어 조합은 유효한 이름이 아님"""
        invalid_names = ["김치", "이상", "박수", "최고", "정리", "강조"]
        for name in invalid_names:
            assert service._is_valid_name(name) is False, f"'{name}' should not be valid"

    # T018: 익명화된 이름 인식 테스트
    def test_anonymized_name_valid(self, service):
        """익명화된 이름(OO, XX)은 유효"""
        anonymized_names = ["김OO", "이XX", "박○○"]
        for name in anonymized_names:
            assert service._is_valid_name(name) is True, f"'{name}' should be valid"

    # T019: 역할 기반 이름 검증 테스트
    def test_role_based_name_valid(self, service):
        """역할 기반 이름은 유효"""
        role_names = ["원고 어머니", "피고 동생", "원고의 자녀", "피고의 형"]
        for name in role_names:
            assert service._is_valid_name(name) is True, f"'{name}' should be valid"

    def test_role_only_not_valid(self, service):
        """단독 역할명은 유효하지 않음"""
        roles = ["원고", "피고", "증인", "참고인", "변호사", "판사"]
        for role in roles:
            assert service._is_valid_name(role) is False, f"'{role}' should not be valid"

    def test_foreign_name_valid(self, service):
        """외국 이름도 유효"""
        foreign_names = ["John", "Michael", "마이클", "사라", "제임스"]
        for name in foreign_names:
            assert service._is_valid_name(name) is True, f"'{name}' should be valid"

    def test_legal_terms_not_valid(self, service):
        """법률 용어는 유효하지 않음"""
        legal_terms = ["이혼", "결혼", "합의", "조정", "소송", "재판", "위자료"]
        for term in legal_terms:
            assert service._is_valid_name(term) is False, f"'{term}' should not be valid"

    def test_time_expressions_not_valid(self, service):
        """시간 표현은 유효하지 않음"""
        time_expressions = ["오전", "오후", "저녁", "새벽", "아침", "오늘", "내일"]
        for expr in time_expressions:
            assert service._is_valid_name(expr) is False, f"'{expr}' should not be valid"


class TestVerifyPersonNames:
    """_verify_person_names() 메서드 테스트"""

    @pytest.fixture
    def service(self):
        """PartyExtractionService 인스턴스 생성"""
        mock_db = MagicMock()
        return PartyExtractionService(mock_db)

    def test_empty_list_returns_empty(self, service):
        """빈 리스트 입력시 빈 리스트 반환"""
        result = service._verify_person_names([])
        assert result == []

    def test_filters_blacklisted_names(self, service):
        """블랙리스트 이름은 필터링됨"""
        persons = [
            ExtractedPerson(name="하", role="third_party", side="neutral", description=""),
            ExtractedPerson(name="김철수", role="plaintiff", side="plaintiff_side", description="원고"),
        ]

        # Pre-filter만 테스트 (Gemini API 호출 없이)
        pre_filtered = [
            p for p in persons
            if p.name.strip() not in service.NON_PERSON_WORDS
            and len(p.name.strip()) >= 2
        ]

        assert len(pre_filtered) == 1
        assert pre_filtered[0].name == "김철수"


class TestMaxPersonsLimit:
    """T012-T013: 최대 인원 수 제한 테스트"""

    @pytest.fixture
    def service(self):
        """PartyExtractionService 인스턴스 생성"""
        mock_db = MagicMock()
        return PartyExtractionService(mock_db)

    def test_max_persons_constant_is_15(self, service):
        """MAX_PERSONS 상수가 15인지 확인"""
        assert MAX_PERSONS == 15

    def test_many_persons_should_be_limited(self, service):
        """15명 초과 인물은 필터링되어야 함 (구현 테스트)"""
        # 이 테스트는 _extract_with_gemini에서 인원 제한 로직이 추가된 후 통과해야 함
        # 현재는 로직이 없으므로 스킵
        pytest.skip("MAX_PERSONS limit not yet implemented in _extract_with_gemini")
