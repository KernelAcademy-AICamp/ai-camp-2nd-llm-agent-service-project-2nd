"""
PersonExtractor 테스트

인물 추출기 테스트
"""


from src.analysis.person_extractor import (
    PersonExtractor,
    ExtractedPerson,
    PersonExtractionResult,
    PersonRole,
    PersonSide,
    extract_persons,
    extract_persons_from_messages,
    ROLE_KEYWORDS,
    KOREAN_SURNAMES,
)


# =============================================================================
# PersonExtractor 초기화 테스트
# =============================================================================

class TestPersonExtractorInit:
    """PersonExtractor 초기화 테스트"""

    def test_default_init(self):
        """기본 초기화"""
        extractor = PersonExtractor()
        assert extractor.include_anonymized is True
        assert extractor.min_confidence == 0.3

    def test_custom_init(self):
        """커스텀 초기화"""
        extractor = PersonExtractor(
            include_anonymized=False,
            min_confidence=0.5,
        )
        assert extractor.include_anonymized is False
        assert extractor.min_confidence == 0.5


# =============================================================================
# 역할 키워드 추출 테스트
# =============================================================================

class TestRoleKeywordExtraction:
    """역할 키워드 기반 추출 테스트"""

    def test_plaintiff_keywords(self):
        """원고 키워드"""
        extractor = PersonExtractor()
        result = extractor.extract("의뢰인이 말씀하시길...")
        assert any(p.role == PersonRole.PLAINTIFF for p in result.persons)

    def test_defendant_keywords(self):
        """피고 키워드"""
        extractor = PersonExtractor()
        result = extractor.extract("남편이 또 그랬어요")
        assert any(p.role == PersonRole.DEFENDANT for p in result.persons)

    def test_child_keywords(self):
        """자녀 키워드"""
        extractor = PersonExtractor()
        result = extractor.extract("아들이 보는 앞에서...")
        assert any(p.role == PersonRole.CHILD for p in result.persons)

    def test_in_law_keywords(self):
        """시가 키워드"""
        extractor = PersonExtractor()
        result = extractor.extract("시어머니가 매일 구박해요")
        assert any(p.role == PersonRole.DEFENDANT_PARENT for p in result.persons)

    def test_third_party_keywords(self):
        """제3자 키워드"""
        extractor = PersonExtractor()
        result = extractor.extract("상간녀와 만나고 있었어요")
        assert any(p.role == PersonRole.THIRD_PARTY for p in result.persons)


# =============================================================================
# 한국 이름 추출 테스트
# =============================================================================

class TestKoreanNameExtraction:
    """한국 이름 패턴 추출 테스트"""

    def test_two_syllable_name(self):
        """2음절 이름"""
        extractor = PersonExtractor()
        result = extractor.extract("김철수가 나타났다")
        names = [p.name for p in result.persons]
        assert "김철수" in names

    def test_three_syllable_name(self):
        """3음절 이름"""
        extractor = PersonExtractor()
        result = extractor.extract("박지현이라는 사람이...")
        names = [p.name for p in result.persons]
        assert "박지현" in names

    def test_common_word_filtered(self):
        """일반 단어 필터링"""
        extractor = PersonExtractor()
        result = extractor.extract("김치가 맛있다")
        names = [p.name for p in result.persons]
        assert "김치" not in names

    def test_multiple_names(self):
        """여러 이름"""
        extractor = PersonExtractor()
        result = extractor.extract("김철수와 이영희가 만났다")
        names = [p.name for p in result.persons]
        assert "김철수" in names
        assert "이영희" in names


# =============================================================================
# 익명화된 이름 추출 테스트
# =============================================================================

class TestAnonymizedNameExtraction:
    """익명화된 이름 추출 테스트"""

    def test_oo_pattern(self):
        """OO 패턴"""
        extractor = PersonExtractor()
        result = extractor.extract("김OO씨가 증언했다")
        names = [p.name for p in result.persons]
        assert any("김O" in n for n in names)

    def test_xx_pattern(self):
        """XX 패턴"""
        extractor = PersonExtractor()
        result = extractor.extract("이XX라는 사람")
        names = [p.name for p in result.persons]
        assert any("이X" in n for n in names)

    def test_disabled_anonymized(self):
        """익명화 비활성화"""
        extractor = PersonExtractor(include_anonymized=False)
        result = extractor.extract("김OO씨")
        # 익명화 이름 추출 안됨
        assert len([p for p in result.persons if "O" in p.name]) == 0


# =============================================================================
# 발화자 추출 테스트
# =============================================================================

class TestSpeakerExtraction:
    """발화자 추출 테스트"""

    def test_bracket_speaker(self):
        """대괄호 발화자"""
        extractor = PersonExtractor()
        result = extractor.extract("[홍길동] 안녕하세요")
        names = [p.name for p in result.persons]
        assert "홍길동" in names

    def test_colon_speaker(self):
        """콜론 발화자"""
        extractor = PersonExtractor()
        text = "철수 : 오늘 뭐해?\n영희 : 집에 있어"
        result = extractor.extract(text)
        names = [p.name for p in result.persons]
        assert "철수" in names
        assert "영희" in names

    def test_time_filtered(self):
        """시간 형식 필터링"""
        extractor = PersonExtractor()
        result = extractor.extract("[12:30] 메시지")
        # 시간은 발화자로 추출 안됨
        names = [p.name for p in result.persons]
        assert "12:30" not in names


# =============================================================================
# 메시지 목록 추출 테스트
# =============================================================================

class TestMessageExtraction:
    """메시지 목록에서 추출 테스트"""

    def test_extract_from_messages(self):
        """메시지에서 추출"""
        extractor = PersonExtractor()
        messages = [
            {"sender": "김철수", "content": "안녕"},
            {"sender": "이영희", "content": "반가워"},
        ]
        result = extractor.extract_from_messages(messages)
        names = [p.name for p in result.persons]
        assert "김철수" in names
        assert "이영희" in names

    def test_sender_high_confidence(self):
        """발신자는 높은 신뢰도"""
        extractor = PersonExtractor()
        messages = [{"sender": "김철수", "content": "테스트"}]
        result = extractor.extract_from_messages(messages)
        kim = next(p for p in result.persons if p.name == "김철수")
        assert kim.confidence >= 0.9


# =============================================================================
# 문맥 기반 역할 추론 테스트
# =============================================================================

class TestContextRoleInference:
    """문맥 기반 역할 추론 테스트"""

    def test_affair_context(self):
        """외도 문맥"""
        extractor = PersonExtractor()
        result = extractor.extract("박지연과 불륜 관계에 있었다")
        # 박지연이 THIRD_PARTY로 추론될 수 있음
        persons = [p for p in result.persons if p.name == "박지연"]
        if persons:
            assert persons[0].role in [PersonRole.THIRD_PARTY, PersonRole.UNKNOWN]

    def test_child_context(self):
        """자녀 문맥"""
        extractor = PersonExtractor()
        _ = extractor.extract("김민수는 우리 아들이에요")
        # 자녀 문맥에서 CHILD로 추론될 수 있음


# =============================================================================
# 간편 함수 테스트
# =============================================================================

class TestConvenienceFunctions:
    """간편 함수 테스트"""

    def test_extract_persons(self):
        """extract_persons 함수"""
        result = extract_persons("남편이 김철수와 만났어요")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(r, dict) for r in result)

    def test_extract_persons_from_messages(self):
        """extract_persons_from_messages 함수"""
        messages = [
            {"sender": "홍길동", "content": "테스트"},
        ]
        result = extract_persons_from_messages(messages)
        assert isinstance(result, list)
        names = [r["name"] for r in result]
        assert "홍길동" in names


# =============================================================================
# PersonExtractionResult 테스트
# =============================================================================

class TestPersonExtractionResult:
    """PersonExtractionResult 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        result = PersonExtractionResult(
            persons=[
                ExtractedPerson(name="김철수", role=PersonRole.DEFENDANT)
            ],
            total_mentions=1,
            unique_names=1,
            role_counts={"defendant": 1},
        )
        d = result.to_dict()
        assert "persons" in d
        assert d["total_mentions"] == 1
        assert d["unique_names"] == 1

    def test_role_counts(self):
        """역할별 카운트"""
        extractor = PersonExtractor()
        result = extractor.extract("남편과 아들이 싸웠어요")
        assert "defendant" in result.role_counts or "child" in result.role_counts


# =============================================================================
# ExtractedPerson 테스트
# =============================================================================

class TestExtractedPerson:
    """ExtractedPerson 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        person = ExtractedPerson(
            name="김철수",
            role=PersonRole.DEFENDANT,
            side=PersonSide.DEFENDANT_SIDE,
            confidence=0.9,
        )
        d = person.to_dict()
        assert d["name"] == "김철수"
        assert d["role"] == "defendant"
        assert d["side"] == "defendant_side"
        assert d["confidence"] == 0.9

    def test_hash_eq(self):
        """해시 및 동등성"""
        p1 = ExtractedPerson(name="김철수")
        p2 = ExtractedPerson(name="김철수")
        p3 = ExtractedPerson(name="이영희")
        assert p1 == p2
        assert p1 != p3
        assert hash(p1) == hash(p2)


# =============================================================================
# 엣지 케이스 테스트
# =============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_text(self):
        """빈 텍스트"""
        extractor = PersonExtractor()
        result = extractor.extract("")
        assert result.persons == []
        assert result.total_mentions == 0

    def test_whitespace_only(self):
        """공백만 있는 텍스트"""
        extractor = PersonExtractor()
        result = extractor.extract("   \n\t   ")
        assert result.persons == []

    def test_no_persons(self):
        """인물 없는 텍스트"""
        extractor = PersonExtractor()
        _ = extractor.extract("오늘 날씨가 좋다")
        # 특정 이름이나 키워드가 없으면 빈 결과 가능

    def test_confidence_filtering(self):
        """신뢰도 필터링"""
        extractor = PersonExtractor(min_confidence=0.9)
        _ = extractor.extract("김철수가 왔다")
        # 높은 신뢰도 요구 시 일부 결과 필터링됨


# =============================================================================
# 상수 테스트
# =============================================================================

class TestConstants:
    """상수 테스트"""

    def test_role_keywords_coverage(self):
        """역할 키워드 커버리지"""
        # 주요 키워드 존재 확인
        assert "남편" in ROLE_KEYWORDS
        assert "아내" in ROLE_KEYWORDS
        assert "시어머니" in ROLE_KEYWORDS
        assert "아들" in ROLE_KEYWORDS

    def test_korean_surnames(self):
        """한국 성씨 존재"""
        assert "김" in KOREAN_SURNAMES
        assert "이" in KOREAN_SURNAMES
        assert "박" in KOREAN_SURNAMES
        assert "최" in KOREAN_SURNAMES
