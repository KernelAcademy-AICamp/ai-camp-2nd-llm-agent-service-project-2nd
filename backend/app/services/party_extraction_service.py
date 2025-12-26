"""
Party Extraction Service - Extract parties and relationships from fact summary using Gemini
017-party-graph-improvement: Fact-summary 기반 인물/관계 자동 추출
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PartyType, RelationshipType
from app.repositories.party_repository import PartyRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.dynamo import get_case_fact_summary
from app.utils.gemini_client import generate_chat_completion_gemini
from app.middleware import NotFoundError, PermissionError, ValidationError

logger = logging.getLogger(__name__)

# ============================================================================
# 019-party-extraction-prompt: 인물 추출 정확도 개선 상수들
# ============================================================================

# 한국 성씨 목록 (상위 100개)
KOREAN_SURNAMES = {
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
    "홍", "고", "문", "양", "손", "배", "백", "허", "유", "남",
    "심", "노", "하", "곽", "성", "차", "주", "우", "구", "민",
    "진", "나", "지", "엄", "변", "채", "원", "천", "방", "공",
    "현", "함", "여", "염", "석", "추", "도", "소", "설", "선",
    "마", "길", "연", "위", "표", "명", "기", "반", "왕", "금",
    "옥", "육", "인", "맹", "제", "모", "탁", "국", "어", "은",
    "편", "용", "예", "경", "봉", "사", "부", "황보", "남궁", "제갈",
    "독고", "선우", "동방", "사공", "서문", "어금", "장곡", "등정", "망절", "무본",
}

# 최대 추출 인원 수
MAX_PERSONS = 15


@dataclass
class ExtractedPerson:
    """Extracted person from fact summary"""
    name: str
    role: str  # plaintiff, defendant, child, third_party, family
    side: str  # plaintiff_side, defendant_side, neutral
    description: str


@dataclass
class ExtractedRelationship:
    """Extracted relationship from fact summary"""
    from_name: str
    to_name: str
    type: str  # marriage, affair, parent_child, sibling, in_law, cohabit
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of party extraction"""
    persons: List[ExtractedPerson]
    relationships: List[ExtractedRelationship]
    new_parties_count: int
    merged_parties_count: int
    new_relationships_count: int
    party_id_map: Dict[str, str]  # name -> party_id mapping


class PartyExtractionService:
    """
    Service for extracting parties and relationships from fact summary using Gemini.

    Workflow:
    1. Get fact summary from DynamoDB
    2. Call Gemini API with structured JSON output prompt
    3. Parse JSON response to extract persons and relationships
    4. Merge with existing parties (by name)
    5. Save to PostgreSQL
    """

    def __init__(self, db: Session):
        self.db = db
        self.party_repo = PartyRepository(db)
        self.member_repo = CaseMemberRepository(db)

    def extract_from_fact_summary(
        self,
        case_id: str,
        user_id: str,
        fact_summary_text: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract parties and relationships from fact summary.

        Args:
            case_id: Case ID
            user_id: User ID for permission check
            fact_summary_text: Optional fact summary text (if not provided, fetched from DynamoDB)

        Returns:
            ExtractionResult with extracted and merged data
        """
        logger.info(f"[PartyExtraction] Starting extraction for case_id={case_id}")

        # 1. Permission check
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("사건 접근 권한이 없습니다")

        # 2. Get fact summary - use provided text or fetch from DynamoDB
        if fact_summary_text:
            fact_summary = fact_summary_text
        else:
            summary_data = get_case_fact_summary(case_id)
            if not summary_data:
                raise NotFoundError("FactSummary")
            # Use modified_summary if available, otherwise ai_summary
            fact_summary = summary_data.get("modified_summary") or summary_data.get("ai_summary", "")

        if not fact_summary or len(fact_summary) < 50:
            raise ValidationError("사실관계 요약이 너무 짧습니다. 최소 50자 이상이어야 합니다.")

        # 3. Call Gemini to extract persons and relationships
        extracted_persons, extracted_relationships = self._extract_with_gemini(fact_summary)

        if not extracted_persons:
            logger.warning(f"[PartyExtraction] No persons extracted for case_id={case_id}")
            return ExtractionResult(
                persons=[],
                relationships=[],
                new_parties_count=0,
                merged_parties_count=0,
                new_relationships_count=0,
                party_id_map={}
            )

        # 4. Merge with existing parties and save
        result = self._merge_and_save(case_id, extracted_persons, extracted_relationships)

        logger.info(
            f"[PartyExtraction] Completed for case_id={case_id}: "
            f"new={result.new_parties_count}, merged={result.merged_parties_count}, "
            f"relationships={result.new_relationships_count}"
        )

        return result

    def _extract_with_gemini(
        self,
        fact_summary: str
    ) -> Tuple[List[ExtractedPerson], List[ExtractedRelationship]]:
        """
        Call Gemini API to extract persons and relationships from fact summary.
        Uses 2-step verification to filter out non-person names.

        Returns:
            Tuple of (persons, relationships)
        """
        prompt_messages = self._build_extraction_prompt(fact_summary)

        try:
            # Step 1: Extract persons and relationships
            response = generate_chat_completion_gemini(
                messages=prompt_messages,
                model=settings.GEMINI_MODEL_CHAT,
                temperature=0.1,  # Low temperature for structured output
                max_tokens=2000
            )

            # Parse JSON response
            persons, relationships = self._parse_extraction_response(response)

            if not persons:
                return persons, relationships

            # Step 2: Verify extracted names are actual person names
            verified_persons = self._verify_person_names(persons)

            # 019-party-extraction-prompt: MAX_PERSONS 제한 적용
            # 15명 초과 시 신뢰도(extraction_confidence) 기준 정렬 후 상위 15명만 선택
            if len(verified_persons) > MAX_PERSONS:
                logger.info(
                    f"[PartyExtraction] Limiting persons from {len(verified_persons)} to {MAX_PERSONS}"
                )
                # 현재는 신뢰도 정보가 없으므로 순서대로 상위 15명 선택
                # 향후 신뢰도 필드 추가 시 정렬 로직 적용 가능
                verified_persons = verified_persons[:MAX_PERSONS]

            # Filter relationships to only include verified persons
            verified_names = {p.name for p in verified_persons}
            verified_relationships = [
                r for r in relationships
                if r.from_name in verified_names and r.to_name in verified_names
            ]

            logger.info(
                f"[PartyExtraction] Verification: {len(persons)} -> {len(verified_persons)} persons, "
                f"{len(relationships)} -> {len(verified_relationships)} relationships"
            )

            return verified_persons, verified_relationships

        except Exception as e:
            logger.error(f"[PartyExtraction] Gemini API error: {e}")
            raise ValidationError(f"인물 추출 중 오류가 발생했습니다: {str(e)}")

    # Non-person words to filter out (019-party-extraction-prompt: 확장된 블랙리스트 ~150단어)
    NON_PERSON_WORDS = {
        # === 1글자 단어 (절대 인물 아님) ===
        "하", "이", "나", "저", "그", "뭐", "왜", "어", "네", "예",
        "아", "오", "음", "응", "헐", "앗", "엥", "흠", "쯧", "윽",

        # === 동사/형용사 어간 및 활용형 ===
        "하다", "했다", "하고", "하면", "하는", "하지", "하게", "하자", "하니",
        "한다", "한다고", "하겠어", "하세요", "해서", "해도", "해야", "해줘",
        "이다", "이고", "이면", "이라", "이니", "이야", "였다", "이었다",
        "있다", "있고", "있어", "있으면", "없다", "없어", "없으면",
        "된다", "되고", "되면", "되어", "됐다", "안됨", "안된",
        "간다", "가고", "가면", "가서", "갔다", "온다", "오고", "왔다",
        "본다", "보고", "보면", "봐서", "봤다", "봐도", "보니",
        "먹다", "먹고", "먹어", "싶다", "싶어", "싶으면",
        "알다", "알고", "알아", "몰라", "모르고", "살다", "살고", "살아",

        # === 부사/접속사/감탄사 ===
        "정말", "진짜", "너무", "매우", "아주", "굉장히", "엄청",
        "이렇게", "그렇게", "저렇게", "어떻게", "왜냐면", "왜냐하면",
        "그래서", "하지만", "그러나", "그런데", "그리고", "또한", "게다가",
        "일단", "우선", "먼저", "다음", "이제", "지금", "아직", "벌써",
        "오히려", "차라리", "결국", "역시", "물론", "당연히",
        "제발", "부디", "아마", "혹시", "설마", "어쩌면",

        # === 조사/어미 ===
        "이랑", "한테", "에게", "으로", "이라고", "라고", "라면", "이면",
        "에서", "까지", "부터", "마저", "조차", "이나", "나마",
        "이요", "요", "이에요", "예요", "입니다", "습니다",

        # === 대명사 ===
        "우리", "너희", "그들", "이것", "저것", "그것", "여기", "저기", "거기",
        "누구", "무엇", "어디", "언제", "어느", "자신", "본인",

        # === 시간 표현 ===
        "오전", "오후", "저녁", "새벽", "아침", "밤", "점심", "낮",
        "오늘", "내일", "어제", "모레", "글피", "이번주", "다음주", "지난주",
        "올해", "내년", "작년", "이번달", "다음달", "지난달",
        "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",

        # === 법률 용어 ===
        "이혼", "결혼", "합의", "조정", "소송", "재판", "판결", "위자료",
        "양육권", "양육비", "재산분할", "면접교섭", "가사", "민사", "형사",
        "항소", "상고", "심리", "변론", "증거", "기일", "출석", "불출석",

        # === 역할/직함 (단독 사용시) ===
        "원고", "피고", "증인", "참고인", "변호사", "판사", "조정위원",
        "대리인", "소송대리인", "법정대리인", "후견인",

        # === 가족 관계 일반명사 ===
        "자녀", "부모", "배우자", "친구", "동료", "직장", "회사",
        "남편", "아내", "아버지", "어머니", "아들", "딸", "형", "동생",
        "언니", "오빠", "누나", "할머니", "할아버지", "삼촌", "이모", "고모",

        # === 시스템 키워드 ===
        "Unknown", "unknown", "UNKNOWN",
        "Speaker", "speaker", "SPEAKER",
        "System", "system", "SYSTEM",
        "undefined", "null", "None", "NULL",
        "Date", "Time", "Document", "File",

        # === 성씨+일반단어 조합 (오추출 방지) ===
        "김치", "이상", "박수", "최고", "정리", "강조", "조정",
        "윤리", "장난", "임시", "한심", "오늘", "서류", "신고",
        "권리", "황당", "안녕", "송금", "류행", "전화", "홍보",

        # === 기타 오추출 빈발 단어 ===
        "이혼아", "결혼식", "법원", "고마워", "미안해", "조심해",
        "그래요", "아니요", "네에", "됐어", "알았어", "몰랐어",
        "사람", "분들", "여러분", "손님", "고객", "이용자",
    }

    def _is_valid_name(self, name: str) -> bool:
        """
        019-party-extraction-prompt: 이름 유효성 검증 메서드

        검증 규칙:
        1. 길이 체크 (2글자 이상)
        2. 블랙리스트 체크
        3. 한국 성씨 검증 (한글 이름인 경우)
        4. 역할 기반 이름 허용 ("원고 어머니" 등)
        5. 익명화 패턴 인식 (김OO, 박XX 등)

        Returns:
            True if valid name, False otherwise
        """
        if not name:
            return False

        name = name.strip()

        # 1. 길이 체크: 2글자 미만은 무조건 제외
        if len(name) < 2:
            return False

        # 2. 블랙리스트 체크
        if name in self.NON_PERSON_WORDS:
            return False
        if name.lower() in self.NON_PERSON_WORDS:
            return False

        # 3. 역할 기반 이름 체크: "원고 어머니", "피고 동생" 등은 허용
        role_pattern = re.compile(r'^(원고|피고|증인|참고인)(의?\s*(아버지|어머니|형|동생|언니|오빠|누나|자녀|아들|딸|배우자|본인|측))$')
        if role_pattern.match(name):
            return True

        # 단독 역할명은 불허
        if name in {"원고", "피고", "증인", "참고인", "변호사", "판사"}:
            return False

        # 4. 익명화 패턴 인식: 김OO, 이XX, 박○○ 등
        anonymized_pattern = re.compile(r'^[가-힣][OXox○●]+$')
        if anonymized_pattern.match(name):
            return True

        # 5. 한글 이름 검증
        korean_pattern = re.compile(r'^[가-힣]+$')
        if korean_pattern.match(name):
            # 2-4글자 한글 이름
            if 2 <= len(name) <= 4:
                first_char = name[0]
                # 성씨로 시작하면 더 신뢰
                if first_char in KOREAN_SURNAMES:
                    # 성씨+일반단어 조합 체크 (블랙리스트에 있는지)
                    if name in self.NON_PERSON_WORDS:
                        return False
                    return True
                else:
                    # 성씨가 아닌 2글자는 허용 (외자 이름 등)
                    return True
            # 5글자 이상 한글은 이름이 아닐 가능성 높음
            elif len(name) >= 5:
                return False

        # 6. 영문 이름 검증 (외국 이름)
        english_pattern = re.compile(r'^[A-Za-z][a-z]+$')
        if english_pattern.match(name) and len(name) >= 2:
            return True

        # 7. 한글+띄어쓰기 (복합 이름: "김 변호사", "박 대리")
        compound_pattern = re.compile(r'^[가-힣]+\s+[가-힣]+$')
        if compound_pattern.match(name):
            parts = name.split()
            if len(parts) == 2:
                first = parts[0]
                # 첫 글자가 성씨이면 유효
                if first in KOREAN_SURNAMES or (len(first) == 1 and first in KOREAN_SURNAMES):
                    return True

        # 기본: 2글자 이상이고 블랙리스트에 없으면 허용
        return len(name) >= 2

    def _verify_person_names(
        self,
        persons: List[ExtractedPerson]
    ) -> List[ExtractedPerson]:
        """
        Step 2: Verify extracted names are actual person names.
        019-party-extraction-prompt: _is_valid_name() 메서드를 사용하여 1차 필터링 후 Gemini 검증.
        """
        if not persons:
            return []

        # Pre-filter: _is_valid_name()을 사용하여 유효한 이름만 필터링
        pre_filtered = [
            p for p in persons
            if self._is_valid_name(p.name)
        ]

        if not pre_filtered:
            logger.info("[PartyExtraction] All names filtered by _is_valid_name()")
            return []

        names = [p.name for p in pre_filtered]
        names_str = ", ".join(names)

        verification_prompt = [
            {
                "role": "system",
                "content": """당신은 텍스트에서 실제 사람 이름만 식별하는 전문가입니다.

## 규칙
1. 실제 사람 이름만 선택 (한국 이름, 외국 이름, 별명 포함)
2. 다음은 사람 이름이 아님:
   - 시간 표현: 오전, 오후, 저녁, 새벽, 아침
   - 법률 용어: 이혼, 결혼, 합의, 조정, 소송
   - 상태 표현: 정됨, 완료, 진행, 확인
   - 일반 명사: 자녀, 부모, 배우자, 친구
3. "원고", "피고"는 역할이므로 사람 이름이 아님 (단, "원고 김철수"에서 "김철수"는 이름)

## 출력 형식 (JSON만 출력)
{"valid_names": ["실제 이름1", "실제 이름2"]}"""
            },
            {
                "role": "user",
                "content": f"다음 중 실제 사람 이름만 선택하세요: [{names_str}]"
            }
        ]

        try:
            response = generate_chat_completion_gemini(
                messages=verification_prompt,
                model=settings.GEMINI_MODEL_CHAT,
                temperature=0.0,  # Deterministic for verification
                max_tokens=500
            )

            # Parse response
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            valid_names = set(data.get("valid_names", []))

            # Filter persons to only include verified names
            verified_persons = [p for p in persons if p.name in valid_names]

            logger.info(f"[PartyExtraction] Name verification: {names} -> {list(valid_names)}")
            return verified_persons

        except Exception as e:
            logger.warning(f"[PartyExtraction] Name verification failed, using pre-filtered names: {e}")
            # Fallback: return pre-filtered persons (already filtered by NON_PERSON_WORDS)
            return pre_filtered

    def _build_extraction_prompt(self, fact_summary: str) -> List[Dict[str, str]]:
        """Build Gemini prompt for structured extraction"""

        system_prompt = """당신은 이혼 소송 사실관계에서 **실제 사람 이름만** 추출하는 전문가입니다.

## 중요: 한국어 이름 패턴
한국어 이름은 다음 형식만 인정합니다:
- 성+이름: "김철수", "이영희", "박준호" (2-4글자)
- 이름만: "철수", "영희", "민정" (2-3글자, 명확한 인명일 때만)
- 외국 이름: "John", "Sarah" 등
- 호칭+이름: "김 변호사", "박 과장"

## 절대 추출하지 말 것 (형태소/일반어)
다음은 **인물 이름이 아닙니다**:
- 동사/형용사 어간: 하다, 하고, 하면, 하게, 하는, 하지, 한다고, 하겠어, 하세요, 하자
- 대명사: 나, 저, 우리, 너, 그, 그녀
- 부사/접속사: 이렇게, 그렇게, 정말, 진짜, 이제, 지금, 오히려, 엄청
- 조사/어미: 이랑, 한테, 에서, 이라, 나도, 나자, 나야, 이야
- 시간 표현: 오전, 오후, 저녁, 아침, 이번주, 오늘도
- 일반 명사: 동료, 친구, 자녀, 부모, 아내, 남편, 변호사, 손님
- 감탄/인사: 고마워, 미안해, 조심해
- 시스템어: Speaker, System, Unknown, Date, Document

## 출력 형식 (JSON만 출력)
{
  "persons": [
    {
      "name": "김철수",
      "role": "plaintiff|defendant|child|third_party|family",
      "description": "원고, 40대 남성"
    }
  ],
  "relationships": [
    {
      "from_name": "김철수",
      "to_name": "이영희",
      "type": "marriage|affair|parent_child|sibling|in_law|cohabit",
      "description": "부부 관계"
    }
  ]
}

## 추출 규칙
1. **이름 형식 검증**: 성+이름(2-4글자) 또는 명확한 외국 이름만 추출
2. **최대 10명**: 핵심 인물만 추출 (원고, 피고, 자녀, 외도 상대 등)
3. **확실한 이름만**: "~씨", "~님" 없이 실명이 명시된 경우만
4. **역할 대용 금지**: "원고", "피고", "상대방", "그 여자" 등은 이름이 아님
5. **형태소 제외**: 동사, 형용사, 부사, 조사는 절대 이름이 아님
6. **인물 없으면 빈 배열**: {"persons": [], "relationships": []}"""

        user_prompt = f"""다음 사실관계 요약에서 **실제 사람 이름**만 추출하세요.
형태소, 동사, 일반 명사는 제외하고, 성+이름 형식의 실명만 추출합니다.

## 사실관계 요약
{fact_summary}

## 추출 시 확인사항
- 이것이 한국어 성+이름 형식인가? (예: 김철수, 이영희)
- 동사/형용사 어간이 아닌가? (예: 하다, 이렇게 제외)
- 일반 명사가 아닌가? (예: 동료, 친구, 아내 제외)

JSON 형식으로 응답하세요."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def _parse_extraction_response(
        self,
        response: str
    ) -> Tuple[List[ExtractedPerson], List[ExtractedRelationship]]:
        """Parse Gemini JSON response"""

        # Clean response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[PartyExtraction] JSON parse error: {e}, response: {response[:500]}")
            raise ValidationError("AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.")

        persons = []
        for p in data.get("persons", []):
            if not p.get("name"):
                continue
            persons.append(ExtractedPerson(
                name=p.get("name", "").strip(),
                role=self._normalize_role(p.get("role", "third_party")),
                side=p.get("side", "neutral"),
                description=p.get("description", "")
            ))

        relationships = []
        for r in data.get("relationships", []):
            if not r.get("from_name") or not r.get("to_name"):
                continue
            relationships.append(ExtractedRelationship(
                from_name=r.get("from_name", "").strip(),
                to_name=r.get("to_name", "").strip(),
                type=self._normalize_relationship_type(r.get("type", "other")),
                description=r.get("description", ""),
                start_date=r.get("start_date"),
                end_date=r.get("end_date")
            ))

        return persons, relationships

    def _normalize_role(self, role: str) -> str:
        """Normalize role string to PartyType enum value"""
        role_map = {
            "plaintiff": "plaintiff",
            "원고": "plaintiff",
            "defendant": "defendant",
            "피고": "defendant",
            "child": "child",
            "자녀": "child",
            "third_party": "third_party",
            "제3자": "third_party",
            "family": "family",
            "친족": "family",
            "witness": "third_party",
            "증인": "third_party",
        }
        return role_map.get(role.lower(), "third_party")

    def _normalize_relationship_type(self, rel_type: str) -> str:
        """Normalize relationship type string"""
        type_map = {
            "marriage": "marriage",
            "혼인": "marriage",
            "부부": "marriage",
            "affair": "affair",
            "불륜": "affair",
            "외도": "affair",
            "parent_child": "parent_child",
            "부모자녀": "parent_child",
            "sibling": "sibling",
            "형제자매": "sibling",
            "in_law": "in_law",
            "인척": "in_law",
            "시댁": "in_law",
            "처가": "in_law",
            "cohabit": "cohabit",
            "동거": "cohabit",
        }
        return type_map.get(rel_type.lower(), "marriage")

    def _merge_and_save(
        self,
        case_id: str,
        persons: List[ExtractedPerson],
        relationships: List[ExtractedRelationship]
    ) -> ExtractionResult:
        """
        Merge extracted data with existing parties and save to database.
        Uses name-based matching for merging.
        """
        # Get existing parties for this case
        existing_parties = self.party_repo.get_parties_by_case(case_id)
        existing_by_name = {p.name.lower(): p for p in existing_parties}

        party_id_map: Dict[str, str] = {}  # name -> party_id
        new_count = 0
        merged_count = 0

        # Default position for new nodes (will be arranged by frontend)
        base_x = 100
        base_y = 100

        # Process persons
        for i, person in enumerate(persons):
            name_lower = person.name.lower()

            if name_lower in existing_by_name:
                # Merge: Update existing party with new info if missing
                existing = existing_by_name[name_lower]
                party_id_map[person.name] = existing.id

                # Update fields if they were auto-extracted (don't override manual edits)
                if existing.is_auto_extracted:
                    # Could update description, etc.
                    pass

                merged_count += 1
                logger.debug(f"[PartyExtraction] Merged party: {person.name} -> {existing.id}")
            else:
                # Create new party
                try:
                    party_type = PartyType(person.role)
                except ValueError:
                    party_type = PartyType.THIRD_PARTY

                new_party = self.party_repo.create_party(
                    case_id=case_id,
                    party_type=party_type,
                    name=person.name,
                    alias=None,
                    birth_year=None,
                    occupation=None,
                    position_x=base_x + (i % 4) * 200,
                    position_y=base_y + (i // 4) * 150,
                    is_auto_extracted=True,
                    extraction_confidence=0.85,
                    source_evidence_id=None,  # From fact summary, not specific evidence
                    extra_data={"description": person.description, "side": person.side}
                )

                party_id_map[person.name] = new_party.id
                existing_by_name[name_lower] = new_party
                new_count += 1
                logger.debug(f"[PartyExtraction] Created party: {person.name} -> {new_party.id}")

        # Process relationships
        new_rel_count = 0
        for rel in relationships:
            from_id = party_id_map.get(rel.from_name)
            to_id = party_id_map.get(rel.to_name)

            if not from_id or not to_id:
                logger.warning(
                    f"[PartyExtraction] Skipping relationship: {rel.from_name} -> {rel.to_name} "
                    f"(party not found)"
                )
                continue

            if from_id == to_id:
                continue  # Skip self-references

            # Check if relationship already exists
            existing_rel = self.party_repo.get_relationship_by_parties(
                case_id, from_id, to_id
            )

            if existing_rel:
                logger.debug(f"[PartyExtraction] Relationship already exists: {from_id} -> {to_id}")
                continue

            # Create new relationship
            try:
                rel_type = RelationshipType(rel.type)
            except ValueError:
                rel_type = RelationshipType.MARRIAGE

            self.party_repo.create_relationship(
                case_id=case_id,
                source_party_id=from_id,
                target_party_id=to_id,
                relationship_type=rel_type,
                is_auto_extracted=True,
                extraction_confidence=0.8,
                evidence_text=rel.description,
                notes=None
            )
            new_rel_count += 1
            logger.debug(f"[PartyExtraction] Created relationship: {from_id} -> {to_id} ({rel.type})")

        return ExtractionResult(
            persons=persons,
            relationships=relationships,
            new_parties_count=new_count,
            merged_parties_count=merged_count,
            new_relationships_count=new_rel_count,
            party_id_map=party_id_map
        )
