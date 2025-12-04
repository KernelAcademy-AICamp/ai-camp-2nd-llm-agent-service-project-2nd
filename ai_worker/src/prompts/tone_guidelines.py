"""
AI 톤앤매너 가이드라인

핵심 원칙: "해결책 제시 X → 객관적 정보 제시 O"

사용법:
    from src.prompts.tone_guidelines import OBJECTIVE_TONE_GUIDELINES

    system_prompt = f'''
    {기존_시스템_프롬프트}

    {OBJECTIVE_TONE_GUIDELINES}
    '''
"""

import re
from typing import List, Tuple

# =============================================================================
# 톤앤매너 가이드라인 상수
# =============================================================================

OBJECTIVE_TONE_GUIDELINES = """
## AI 응답 가이드라인 (반드시 준수)

### 1. 객관적 사실만 제시
- 사용: "~입니다", "~으로 확인됩니다", "~으로 나타납니다"
- 금지: "~하세요", "~해야 합니다", "~하시기 바랍니다"

### 2. 통계/수치 기반 정보
- 사용: "유사 판례 10건 중 7건 승소 (70%)"
- 사용: "위자료 범위: 2천만원~4천만원"
- 금지: "승소 가능성이 높습니다", "위자료를 3천만원으로 청구하세요"

### 3. 부족한 부분은 현황만 언급
- 사용: "해당 기간 증거가 없습니다"
- 사용: "부정행위 관련 증거: 0건"
- 금지: "증거를 더 확보하세요", "이 증거를 제출해야 합니다"

### 4. 판단/조언 표현 금지
- 금지: "~이 좋겠습니다", "~을 권장합니다", "~이 유리합니다"
- 사용: "유사 판례에서는 ~으로 나타납니다"
"""

DISCLAIMER_TEXT = "※ 본 정보는 참고용이며 법률 조언이 아닙니다. 최종 판단은 변호사와 상담하시기 바랍니다."

# =============================================================================
# 금지 표현 목록
# =============================================================================

FORBIDDEN_EXPRESSIONS = [
    # 명령/지시형
    r"~하세요",
    r"~하십시오",
    r"~해야 합니다",
    r"~해야 합니다",
    r"~하시기 바랍니다",
    r"~을 권장합니다",
    r"~이 좋겠습니다",

    # 주관적 판단
    r"승소 가능성이 높습니다",
    r"승소할 것 같습니다",
    r"유리합니다",
    r"불리합니다",

    # 조언형
    r"~을 추천합니다",
    r"~을 제안합니다",
    r"확보하세요",
    r"제출하세요",
    r"청구하세요",
]

# 정규식 패턴으로 컴파일
FORBIDDEN_PATTERNS = [
    re.compile(pattern.replace("~", r".{0,20}"))
    for pattern in FORBIDDEN_EXPRESSIONS
]

# =============================================================================
# 검증 함수
# =============================================================================

def validate_tone(text: str) -> Tuple[bool, List[str]]:
    """
    텍스트가 톤앤매너 가이드라인을 준수하는지 검증

    Args:
        text: 검증할 텍스트

    Returns:
        Tuple[bool, List[str]]: (준수 여부, 위반 표현 목록)

    Example:
        >>> is_valid, violations = validate_tone("증거를 더 확보하세요")
        >>> print(is_valid)  # False
        >>> print(violations)  # ["확보하세요"]
    """
    violations = []

    for pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(text)
        violations.extend(matches)

    # 단순 키워드 검사 추가
    simple_keywords = [
        "하세요", "하십시오", "해야 합니다", "권장합니다",
        "좋겠습니다", "유리합니다", "불리합니다",
        "확보하세요", "제출하세요", "청구하세요"
    ]

    for keyword in simple_keywords:
        if keyword in text:
            violations.append(keyword)

    # 중복 제거
    violations = list(set(violations))

    return len(violations) == 0, violations


def get_objective_reasoning_example() -> str:
    """
    객관적 톤의 reasoning 예시 반환

    Returns:
        str: 예시 텍스트
    """
    return """
### 올바른 reasoning 예시

#### 증거 분석
- ✅ "호텔 만남과 '또' 표현으로 반복적 외도 정황이 나타납니다"
- ❌ "호텔 만남과 '또'라는 표현이 반복적 외도를 암시하므로 증거로 활용하세요"

#### 유책사유 판단
- ✅ "민법 840조 1호(부정행위)에 해당하는 정황입니다"
- ❌ "부정행위로 판단되므로 이를 근거로 소송을 진행하세요"

#### 증거 현황
- ✅ "2024년 3월~5월 기간의 증거가 없습니다"
- ❌ "2024년 3월~5월 기간의 증거가 부족하므로 추가 확보가 필요합니다"
"""
