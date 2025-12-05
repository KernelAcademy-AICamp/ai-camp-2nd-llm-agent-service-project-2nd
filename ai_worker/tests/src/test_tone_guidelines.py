"""
Test suite for Tone Guidelines
톤앤매너 가이드라인 검증 테스트
"""

from src.prompts.tone_guidelines import (
    OBJECTIVE_TONE_GUIDELINES,
    DISCLAIMER_TEXT,
    FORBIDDEN_EXPRESSIONS,
    FORBIDDEN_PATTERNS,
    validate_tone,
    get_objective_reasoning_example,
)


class TestToneGuidelinesConstants:
    """톤 가이드라인 상수 테스트"""

    def test_guidelines_exists(self):
        """가이드라인 상수가 존재하는지 테스트"""
        assert OBJECTIVE_TONE_GUIDELINES is not None
        assert len(OBJECTIVE_TONE_GUIDELINES) > 0

    def test_guidelines_contains_key_phrases(self):
        """가이드라인에 핵심 문구가 포함되어 있는지 테스트"""
        assert "객관적" in OBJECTIVE_TONE_GUIDELINES
        assert "~입니다" in OBJECTIVE_TONE_GUIDELINES
        assert "금지" in OBJECTIVE_TONE_GUIDELINES

    def test_disclaimer_exists(self):
        """면책 문구가 존재하는지 테스트"""
        assert DISCLAIMER_TEXT is not None
        assert "법률 조언이 아닙니다" in DISCLAIMER_TEXT

    def test_forbidden_expressions_list(self):
        """금지 표현 목록이 정의되어 있는지 테스트"""
        assert len(FORBIDDEN_EXPRESSIONS) > 0
        assert any("하세요" in expr for expr in FORBIDDEN_EXPRESSIONS)
        assert any("해야 합니다" in expr for expr in FORBIDDEN_EXPRESSIONS)

    def test_forbidden_patterns_compiled(self):
        """금지 표현 패턴이 컴파일되어 있는지 테스트"""
        assert len(FORBIDDEN_PATTERNS) > 0
        # 패턴이 정규식 객체인지 확인
        for pattern in FORBIDDEN_PATTERNS:
            assert hasattr(pattern, 'findall')


class TestValidateTone:
    """validate_tone 함수 테스트"""

    def test_valid_objective_tone(self):
        """객관적 톤의 텍스트가 통과하는지 테스트"""
        valid_texts = [
            "해당 기간의 증거가 없습니다",
            "부정행위 관련 증거: 3건",
            "유사 판례에서는 승소율이 70%로 나타납니다",
            "2024년 3월~5월 기간의 증거가 확인됩니다",
            "호텔 만남과 '또' 표현으로 반복적 외도 정황이 나타납니다",
        ]

        for text in valid_texts:
            is_valid, violations = validate_tone(text)
            assert is_valid, f"'{text}' should be valid but got violations: {violations}"

    def test_invalid_imperative_tone(self):
        """명령형 톤이 거부되는지 테스트"""
        invalid_texts = [
            "증거를 더 확보하세요",
            "이 서류를 제출하세요",
            "변호사와 상담하십시오",
        ]

        for text in invalid_texts:
            is_valid, violations = validate_tone(text)
            assert not is_valid, f"'{text}' should be invalid"
            assert len(violations) > 0

    def test_invalid_advice_tone(self):
        """조언형 톤이 거부되는지 테스트"""
        invalid_texts = [
            "이 방법을 권장합니다",
            "소송이 유리합니다",
            "증거 수집이 좋겠습니다",
        ]

        for text in invalid_texts:
            is_valid, violations = validate_tone(text)
            assert not is_valid, f"'{text}' should be invalid"

    def test_invalid_obligation_tone(self):
        """의무형 톤이 거부되는지 테스트"""
        invalid_texts = [
            "증거를 제출해야 합니다",
            "소송을 진행해야 합니다",
        ]

        for text in invalid_texts:
            is_valid, violations = validate_tone(text)
            assert not is_valid, f"'{text}' should be invalid"
            assert any("해야 합니다" in v for v in violations)

    def test_returns_specific_violations(self):
        """위반 사항이 구체적으로 반환되는지 테스트"""
        text = "증거를 확보하세요. 소송을 진행해야 합니다."
        is_valid, violations = validate_tone(text)

        assert not is_valid
        assert "확보하세요" in violations or any("하세요" in v for v in violations)
        assert "해야 합니다" in violations

    def test_empty_text(self):
        """빈 텍스트 처리 테스트"""
        is_valid, violations = validate_tone("")
        assert is_valid
        assert len(violations) == 0

    def test_mixed_content(self):
        """혼합 내용 테스트 - 객관적 + 조언형"""
        text = "현재 증거가 3건 확인됩니다. 추가로 증거를 확보하세요."
        is_valid, violations = validate_tone(text)

        assert not is_valid
        assert len(violations) > 0


class TestObjectiveReasoningExample:
    """get_objective_reasoning_example 함수 테스트"""

    def test_example_exists(self):
        """예시 텍스트가 반환되는지 테스트"""
        example = get_objective_reasoning_example()
        assert example is not None
        assert len(example) > 0

    def test_example_contains_correct_incorrect(self):
        """올바른/잘못된 예시가 포함되어 있는지 테스트"""
        example = get_objective_reasoning_example()
        # 체크마크와 X 마크 확인
        assert "✅" in example
        assert "❌" in example


class TestRealWorldScenarios:
    """실제 사용 시나리오 테스트"""

    def test_evidence_summary_tone(self):
        """증거 요약 톤 테스트"""
        # 올바른 톤
        valid_summary = """
        증거 현황:
        - 카카오톡 대화: 15건
        - 녹음 파일: 3건
        - 사진 자료: 7건

        2024년 1월~3월 기간의 증거가 없습니다.
        부정행위 관련 증거는 5건으로 확인됩니다.
        """
        is_valid, _ = validate_tone(valid_summary)
        assert is_valid

    def test_legal_analysis_tone(self):
        """법적 분석 톤 테스트"""
        # 잘못된 톤
        invalid_analysis = """
        분석 결과:
        부정행위 정황이 확인되므로 소송을 진행하세요.
        위자료는 3천만원으로 청구하는 것이 좋겠습니다.
        """
        is_valid, violations = validate_tone(invalid_analysis)
        assert not is_valid
        assert len(violations) >= 2

    def test_ai_reasoning_tone(self):
        """AI 분석 reasoning 톤 테스트"""
        # 올바른 reasoning
        valid_reasoning = "호텔 만남과 '또' 표현으로 반복적 외도 정황이 나타납니다"
        is_valid, _ = validate_tone(valid_reasoning)
        assert is_valid

        # 잘못된 reasoning
        invalid_reasoning = "호텔 만남으로 외도가 의심되므로 증거로 활용하세요"
        is_valid, _ = validate_tone(invalid_reasoning)
        assert not is_valid


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_similar_but_valid_phrases(self):
        """금지 표현과 유사하지만 유효한 문구 테스트"""
        # "하세요"가 포함되어 있지만 다른 맥락
        # 실제로는 "하세요"가 포함되면 거부됨
        text = "사용자가 '증거를 제출하세요'라고 말했습니다"
        is_valid, violations = validate_tone(text)
        # 인용문 내에도 금지 표현이 있으면 거부됨
        assert not is_valid

    def test_unicode_handling(self):
        """유니코드 문자 처리 테스트"""
        text = "증거가 확인됩니다 🔍"
        is_valid, _ = validate_tone(text)
        assert is_valid

    def test_multiline_text(self):
        """여러 줄 텍스트 테스트"""
        text = """첫 번째 줄입니다.
        두 번째 줄입니다.
        세 번째 줄입니다."""
        is_valid, _ = validate_tone(text)
        assert is_valid

    def test_long_text_performance(self):
        """긴 텍스트 성능 테스트"""
        # 긴 텍스트도 처리 가능해야 함
        long_text = "증거가 확인됩니다. " * 1000
        is_valid, _ = validate_tone(long_text)
        assert is_valid
