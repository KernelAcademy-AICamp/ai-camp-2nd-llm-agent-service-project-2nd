"""
PersonExtractor - 텍스트에서 인물 정보 추출

규칙 기반 한국어 인물명 추출기
- 패턴 기반 이름 추출
- 역할 키워드 매핑
- 관계 추론

LLM 의존 없이 규칙 기반으로 구현
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum


# =============================================================================
# 상수 정의
# =============================================================================

class PersonRole(Enum):
    """인물 역할"""
    PLAINTIFF = "plaintiff"           # 원고 (의뢰인)
    DEFENDANT = "defendant"           # 피고 (상대방)
    CHILD = "child"                   # 자녀
    PLAINTIFF_PARENT = "plaintiff_parent"    # 원고 부모
    DEFENDANT_PARENT = "defendant_parent"    # 피고 부모
    RELATIVE = "relative"             # 친척
    FRIEND = "friend"                 # 친구
    COLLEAGUE = "colleague"           # 직장 동료
    THIRD_PARTY = "third_party"       # 제3자 (외도 상대 등)
    WITNESS = "witness"               # 증인
    UNKNOWN = "unknown"               # 미상


class PersonSide(Enum):
    """인물 측면 (누구 편인지)"""
    PLAINTIFF_SIDE = "plaintiff_side"
    DEFENDANT_SIDE = "defendant_side"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


# 역할 키워드 → PersonRole 매핑
ROLE_KEYWORDS: Dict[str, Tuple[PersonRole, PersonSide]] = {
    # 원고 측
    "의뢰인": (PersonRole.PLAINTIFF, PersonSide.PLAINTIFF_SIDE),
    "원고": (PersonRole.PLAINTIFF, PersonSide.PLAINTIFF_SIDE),
    "나": (PersonRole.PLAINTIFF, PersonSide.PLAINTIFF_SIDE),
    "저": (PersonRole.PLAINTIFF, PersonSide.PLAINTIFF_SIDE),
    "본인": (PersonRole.PLAINTIFF, PersonSide.PLAINTIFF_SIDE),

    # 피고 측
    "상대방": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "피고": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "남편": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "아내": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "배우자": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "그 사람": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "그 남자": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),
    "그 여자": (PersonRole.DEFENDANT, PersonSide.DEFENDANT_SIDE),

    # 자녀
    "아들": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "딸": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "자녀": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "아이": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "애": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "큰애": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "작은애": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "첫째": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "둘째": (PersonRole.CHILD, PersonSide.NEUTRAL),
    "막내": (PersonRole.CHILD, PersonSide.NEUTRAL),

    # 원고 부모
    "친정어머니": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "친정아버지": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "친정엄마": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "친정아빠": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "우리 엄마": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "우리 아빠": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "저희 어머니": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),
    "저희 아버지": (PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE),

    # 피고 부모
    "시어머니": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "시아버지": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "시엄마": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "시아빠": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "시부모": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "장모": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),
    "장인": (PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE),

    # 친척
    "시누이": (PersonRole.RELATIVE, PersonSide.DEFENDANT_SIDE),
    "시동생": (PersonRole.RELATIVE, PersonSide.DEFENDANT_SIDE),
    "형님": (PersonRole.RELATIVE, PersonSide.UNKNOWN),
    "동서": (PersonRole.RELATIVE, PersonSide.UNKNOWN),
    "처남": (PersonRole.RELATIVE, PersonSide.PLAINTIFF_SIDE),
    "처제": (PersonRole.RELATIVE, PersonSide.PLAINTIFF_SIDE),
    "매형": (PersonRole.RELATIVE, PersonSide.PLAINTIFF_SIDE),

    # 제3자 (그 여자/그 남자는 피고 섹션에서 정의됨)
    "상간녀": (PersonRole.THIRD_PARTY, PersonSide.UNKNOWN),
    "상간남": (PersonRole.THIRD_PARTY, PersonSide.UNKNOWN),
    "바람상대": (PersonRole.THIRD_PARTY, PersonSide.UNKNOWN),
    "외도상대": (PersonRole.THIRD_PARTY, PersonSide.UNKNOWN),

    # 친구/동료
    "친구": (PersonRole.FRIEND, PersonSide.UNKNOWN),
    "동료": (PersonRole.COLLEAGUE, PersonSide.UNKNOWN),
    "직장동료": (PersonRole.COLLEAGUE, PersonSide.UNKNOWN),
    "회사동료": (PersonRole.COLLEAGUE, PersonSide.UNKNOWN),
}

# 한국 성씨 목록 (상위 빈도)
KOREAN_SURNAMES = {
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
    "홍", "고", "문", "양", "손", "배", "백", "허", "유", "남",
    "심", "노", "하", "곽", "성", "차", "주", "우", "구", "민",
    "진", "나", "지", "엄", "변", "채", "원", "천", "방", "공",
}

# 익명화 패턴 (OO, XX, ○○ 등)
ANONYMIZED_PATTERNS = [
    r"[가-힣]O{1,2}",      # 김OO, 이O
    r"[가-힣]○{1,2}",     # 김○○
    r"[가-힣]X{1,2}",      # 김XX
    r"[가-힣]◯{1,2}",     # 김◯◯
    r"[가-힣]\*{1,2}",     # 김**
]


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class ExtractedPerson:
    """추출된 인물 정보"""
    name: str                                    # 이름 또는 호칭
    role: PersonRole = PersonRole.UNKNOWN        # 역할
    side: PersonSide = PersonSide.UNKNOWN        # 측면
    aliases: List[str] = field(default_factory=list)  # 별칭들
    confidence: float = 0.5                      # 신뢰도 (0~1)
    source_context: str = ""                     # 추출된 문맥

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {
            "name": self.name,
            "role": self.role.value,
            "side": self.side.value,
            "aliases": self.aliases,
            "confidence": self.confidence,
            "source_context": self.source_context,
        }

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, ExtractedPerson):
            return self.name == other.name
        return False


@dataclass
class PersonExtractionResult:
    """인물 추출 결과"""
    persons: List[ExtractedPerson]
    total_mentions: int                          # 총 언급 횟수
    unique_names: int                            # 고유 이름 수
    role_counts: Dict[str, int] = field(default_factory=dict)  # 역할별 카운트

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {
            "persons": [p.to_dict() for p in self.persons],
            "total_mentions": self.total_mentions,
            "unique_names": self.unique_names,
            "role_counts": self.role_counts,
        }


# =============================================================================
# PersonExtractor 클래스
# =============================================================================

class PersonExtractor:
    """텍스트에서 인물 정보를 추출하는 클래스"""

    def __init__(
        self,
        include_anonymized: bool = True,
        min_confidence: float = 0.3,
    ):
        """
        Args:
            include_anonymized: 익명화된 이름(김OO) 포함 여부
            min_confidence: 최소 신뢰도 (이하는 제외)
        """
        self.include_anonymized = include_anonymized
        self.min_confidence = min_confidence

        # 이름 패턴 컴파일
        self._compile_patterns()

    def _compile_patterns(self):
        """정규식 패턴 컴파일"""
        # 한국 이름 패턴 (성 + 이름 1~2자)
        surname_pattern = "|".join(KOREAN_SURNAMES)
        self.korean_name_pattern = re.compile(
            rf"({surname_pattern})[가-힣]{{1,2}}"
        )

        # 익명화된 이름 패턴
        if self.include_anonymized:
            self.anonymized_patterns = [
                re.compile(p) for p in ANONYMIZED_PATTERNS
            ]
        else:
            self.anonymized_patterns = []

        # 역할 키워드 패턴 (단어 경계)
        self.role_patterns = {}
        for keyword in ROLE_KEYWORDS.keys():
            # 키워드 앞뒤로 적절한 컨텍스트 허용
            self.role_patterns[keyword] = re.compile(
                rf"(?:^|[\s,.]){re.escape(keyword)}(?:$|[\s,.가-힣])"
            )

    def extract(self, text: str) -> PersonExtractionResult:
        """
        텍스트에서 인물 정보 추출

        Args:
            text: 분석할 텍스트

        Returns:
            PersonExtractionResult: 추출 결과
        """
        if not text or not text.strip():
            return PersonExtractionResult(
                persons=[],
                total_mentions=0,
                unique_names=0,
                role_counts={},
            )

        persons_dict: Dict[str, ExtractedPerson] = {}
        total_mentions = 0

        # 1. 역할 키워드 기반 추출
        role_persons = self._extract_by_role_keywords(text)
        for person in role_persons:
            self._merge_person(persons_dict, person)
            total_mentions += 1

        # 2. 한국 이름 패턴 추출
        name_persons = self._extract_korean_names(text)
        for person in name_persons:
            self._merge_person(persons_dict, person)
            total_mentions += 1

        # 3. 익명화된 이름 추출
        if self.include_anonymized:
            anon_persons = self._extract_anonymized_names(text)
            for person in anon_persons:
                self._merge_person(persons_dict, person)
                total_mentions += 1

        # 4. 발화자 추출 (카카오톡 형식)
        speaker_persons = self._extract_speakers(text)
        for person in speaker_persons:
            self._merge_person(persons_dict, person)
            total_mentions += 1

        # 신뢰도 필터링
        filtered_persons = [
            p for p in persons_dict.values()
            if p.confidence >= self.min_confidence
        ]

        # 역할별 카운트
        role_counts = {}
        for person in filtered_persons:
            role_key = person.role.value
            role_counts[role_key] = role_counts.get(role_key, 0) + 1

        return PersonExtractionResult(
            persons=filtered_persons,
            total_mentions=total_mentions,
            unique_names=len(filtered_persons),
            role_counts=role_counts,
        )

    def _extract_by_role_keywords(self, text: str) -> List[ExtractedPerson]:
        """역할 키워드 기반 추출"""
        persons = []

        for keyword, (role, side) in ROLE_KEYWORDS.items():
            pattern = self.role_patterns.get(keyword)
            if pattern and pattern.search(text):
                # 문맥 추출 (키워드 주변 30자)
                match = pattern.search(text)
                start = max(0, match.start() - 15)
                end = min(len(text), match.end() + 15)
                context = text[start:end].strip()

                person = ExtractedPerson(
                    name=keyword,
                    role=role,
                    side=side,
                    confidence=0.9,  # 키워드 매칭은 높은 신뢰도
                    source_context=context,
                )
                persons.append(person)

        return persons

    def _extract_korean_names(self, text: str) -> List[ExtractedPerson]:
        """한국 이름 패턴 추출"""
        persons = []

        for match in self.korean_name_pattern.finditer(text):
            name = match.group()

            # 일반 단어 필터링 (예: 김치, 이상, 박수 등)
            if self._is_common_word(name):
                continue

            # 문맥 추출
            start = max(0, match.start() - 15)
            end = min(len(text), match.end() + 15)
            context = text[start:end].strip()

            # 문맥에서 역할 추론
            role, side = self._infer_role_from_context(context, name)

            person = ExtractedPerson(
                name=name,
                role=role,
                side=side,
                confidence=0.7,  # 이름 패턴은 중간 신뢰도
                source_context=context,
            )
            persons.append(person)

        return persons

    def _extract_anonymized_names(self, text: str) -> List[ExtractedPerson]:
        """익명화된 이름 추출"""
        persons = []

        for pattern in self.anonymized_patterns:
            for match in pattern.finditer(text):
                name = match.group()

                # 문맥 추출
                start = max(0, match.start() - 15)
                end = min(len(text), match.end() + 15)
                context = text[start:end].strip()

                # 문맥에서 역할 추론
                role, side = self._infer_role_from_context(context, name)

                person = ExtractedPerson(
                    name=name,
                    role=role,
                    side=side,
                    confidence=0.8,  # 익명화 패턴은 높은 신뢰도
                    source_context=context,
                )
                persons.append(person)

        return persons

    def _extract_speakers(self, text: str) -> List[ExtractedPerson]:
        """카카오톡 발화자 추출"""
        persons = []

        # 카카오톡 형식: [이름] 메시지 또는 이름 : 메시지
        patterns = [
            r"\[([^\]]+)\]",           # [이름]
            r"^([가-힣a-zA-Z0-9_]+)\s*:",  # 이름 :
        ]

        seen_speakers = set()

        for line in text.split("\n"):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    speaker = match.group(1).strip()

                    # 너무 짧거나 긴 것 필터링
                    if len(speaker) < 1 or len(speaker) > 20:
                        continue

                    # 시간 형식 필터링
                    if re.match(r"^\d{1,2}:\d{2}", speaker):
                        continue

                    if speaker not in seen_speakers:
                        seen_speakers.add(speaker)

                        person = ExtractedPerson(
                            name=speaker,
                            role=PersonRole.UNKNOWN,
                            side=PersonSide.UNKNOWN,
                            confidence=0.85,
                            source_context=line[:50],
                        )
                        persons.append(person)

        return persons

    def _infer_role_from_context(
        self, context: str, name: str
    ) -> Tuple[PersonRole, PersonSide]:
        """문맥에서 역할 추론"""
        # 외도/불륜 관련 키워드
        affair_keywords = ["외도", "바람", "불륜", "상간", "만나"]
        if any(kw in context for kw in affair_keywords):
            return PersonRole.THIRD_PARTY, PersonSide.UNKNOWN

        # 자녀 관련 키워드
        child_keywords = ["아들", "딸", "자녀", "애들", "아이"]
        if any(kw in context for kw in child_keywords):
            return PersonRole.CHILD, PersonSide.NEUTRAL

        # 부모 관련 키워드
        if "시어머니" in context or "시아버지" in context:
            return PersonRole.DEFENDANT_PARENT, PersonSide.DEFENDANT_SIDE
        if "친정" in context or "우리 엄마" in context:
            return PersonRole.PLAINTIFF_PARENT, PersonSide.PLAINTIFF_SIDE

        return PersonRole.UNKNOWN, PersonSide.UNKNOWN

    def _is_common_word(self, name: str) -> bool:
        """일반 단어인지 확인"""
        common_words = {
            # 일반 명사
            "김치", "이상", "박수", "최고", "정리", "강조", "조금",
            "윤리", "장소", "임시", "한국", "오늘", "서울", "신청",
            "권리", "황금", "안녕", "송금", "전화", "홍보", "고민",
            "문제", "양식", "손해", "배달", "백화", "허락", "남자",
            "심리", "노력", "하루", "성공", "차이", "주의", "민원",
            # 법률 용어
            "강제", "조정", "이혼", "양육", "재산",
        }
        return name in common_words

    def _merge_person(
        self, persons_dict: Dict[str, ExtractedPerson], new_person: ExtractedPerson
    ):
        """인물 정보 병합"""
        if new_person.name in persons_dict:
            existing = persons_dict[new_person.name]

            # 더 높은 신뢰도 사용
            if new_person.confidence > existing.confidence:
                existing.confidence = new_person.confidence

            # 역할 정보 업데이트 (unknown이 아닌 경우)
            if (existing.role == PersonRole.UNKNOWN and
                new_person.role != PersonRole.UNKNOWN):
                existing.role = new_person.role
                existing.side = new_person.side

            # 별칭 추가
            if new_person.source_context and new_person.source_context not in existing.aliases:
                existing.aliases.append(new_person.source_context)
        else:
            persons_dict[new_person.name] = new_person

    def extract_from_messages(
        self, messages: List[Dict]
    ) -> PersonExtractionResult:
        """
        메시지 목록에서 인물 추출

        Args:
            messages: [{"sender": "...", "content": "..."}] 형식

        Returns:
            PersonExtractionResult: 추출 결과
        """
        all_persons: Dict[str, ExtractedPerson] = {}
        total_mentions = 0

        for msg in messages:
            # 발신자 추출
            sender = msg.get("sender", "")
            if sender:
                person = ExtractedPerson(
                    name=sender,
                    role=PersonRole.UNKNOWN,
                    side=PersonSide.UNKNOWN,
                    confidence=0.95,  # 발신자는 높은 신뢰도
                )
                self._merge_person(all_persons, person)
                total_mentions += 1

            # 내용에서 추출
            content = msg.get("content", "")
            if content:
                result = self.extract(content)
                for person in result.persons:
                    self._merge_person(all_persons, person)
                total_mentions += result.total_mentions

        # 역할별 카운트
        role_counts = {}
        for person in all_persons.values():
            role_key = person.role.value
            role_counts[role_key] = role_counts.get(role_key, 0) + 1

        return PersonExtractionResult(
            persons=list(all_persons.values()),
            total_mentions=total_mentions,
            unique_names=len(all_persons),
            role_counts=role_counts,
        )


# =============================================================================
# 간편 함수
# =============================================================================

def extract_persons(text: str) -> List[Dict]:
    """
    텍스트에서 인물 추출 (간편 함수)

    Args:
        text: 분석할 텍스트

    Returns:
        인물 정보 딕셔너리 리스트
    """
    extractor = PersonExtractor()
    result = extractor.extract(text)
    return [p.to_dict() for p in result.persons]


def extract_persons_from_messages(messages: List[Dict]) -> List[Dict]:
    """
    메시지 목록에서 인물 추출 (간편 함수)

    Args:
        messages: [{"sender": "...", "content": "..."}] 형식

    Returns:
        인물 정보 딕셔너리 리스트
    """
    extractor = PersonExtractor()
    result = extractor.extract_from_messages(messages)
    return [p.to_dict() for p in result.persons]
