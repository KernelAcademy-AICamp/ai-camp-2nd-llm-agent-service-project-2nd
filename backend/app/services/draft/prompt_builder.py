"""
Prompt Builder - Constructs GPT-4o prompts for draft generation
Extracted from DraftService for better modularity (Issue #325)
"""

from typing import List, Any

from app.utils.qdrant import get_template_schema_for_prompt


class PromptBuilder:
    """
    Builds GPT-4o prompts for legal document draft generation.
    """

    def __init__(self, rag_orchestrator=None):
        """
        Initialize prompt builder

        Args:
            rag_orchestrator: Optional RAGOrchestrator for context formatting
        """
        self.rag_orchestrator = rag_orchestrator

    def build_draft_prompt(
        self,
        case: Any,
        sections: List[str],
        evidence_context: List[dict],
        legal_context: List[dict],
        precedent_context: List[dict],
        consultation_context: List[dict] = None,
        fact_summary_context: str = "",
        language: str = "ko",
        style: str = "formal",
        force_text_output: bool = False
    ) -> List[dict]:
        """
        Build GPT-4o prompt with evidence, legal, precedent, consultation, and fact summary context

        Args:
            case: Case object
            sections: Sections to generate
            evidence_context: Evidence RAG search results
            legal_context: Legal knowledge RAG search results
            precedent_context: Similar precedent search results
            consultation_context: Consultation RAG search results (Issue #403)
            fact_summary_context: Lawyer-edited fact summary (014-case-fact-summary T025)
            language: Language (ko/en)
            style: Writing style
            force_text_output: Force text output mode (disable JSON) - useful for Gemini

        Returns:
            List of messages for GPT-4o
        """
        # Try to get template schema from Qdrant (skip if force_text_output)
        if force_text_output:
            template_schema = None
        else:
            template_schema = get_template_schema_for_prompt("이혼소장")
        use_json_output = template_schema is not None

        # Build context strings
        if self.rag_orchestrator:
            evidence_context_str = self.rag_orchestrator.format_evidence_context(evidence_context)
            legal_context_str = self.rag_orchestrator.format_legal_context(legal_context)
            precedent_context_str = self.rag_orchestrator.format_precedent_context(precedent_context)
            consultation_context_str = self.rag_orchestrator.format_consultation_context(consultation_context or [])
        else:
            evidence_context_str = self._format_evidence_context(evidence_context)
            legal_context_str = self._format_legal_context(legal_context)
            precedent_context_str = self._format_precedent_context(precedent_context)
            consultation_context_str = self._format_consultation_context(consultation_context or [])

        # System message - define role and constraints
        if use_json_output:
            system_message = self._build_json_system_message(template_schema)
        else:
            system_message = self._build_text_system_message()

        # User message - include case info, evidence, legal, precedent, consultation, and fact summary context
        if use_json_output:
            user_message = self._build_json_user_message(
                case, sections, evidence_context_str, legal_context_str,
                precedent_context_str, consultation_context_str, fact_summary_context, language, style
            )
        else:
            user_message = self._build_text_user_message(
                case, sections, evidence_context_str, legal_context_str,
                precedent_context_str, consultation_context_str, fact_summary_context, language, style
            )

        return [system_message, user_message]

    def _build_json_system_message(self, template_schema: str) -> dict:
        """Build system message for JSON output mode"""
        return {
            "role": "system",
            "content": f"""당신은 대한민국 가정법원에 제출하는 정식 소장(訴狀)을 작성하는 전문 법률가입니다.

[핵심 원칙 - 반드시 준수]
1. 모든 사실관계, 날짜, 발언 내용은 오직 제공된 "증거 자료"에서만 추출하세요
2. 증거에 없는 내용을 임의로 생성하거나 추측하지 마세요
3. 확인되지 않은 정보는 "확인 필요" 또는 "[미확인]"으로 표시하세요

[출력 형식 - 중요!]
- 반드시 아래 JSON 스키마에 맞춰 출력하세요
- 유효한 JSON 형식으로만 응답하세요 (추가 설명 없이 JSON만)
- 각 섹션의 format 객체는 문서 형식 정보입니다 (들여쓰기, 정렬, 줄간격 등)

[JSON 스키마]
{template_schema}

[증거 인용 방식]
- grounds 섹션의 각 paragraph에 evidence_refs 배열로 증거 번호 포함
- 예: "evidence_refs": ["갑 제1호증", "갑 제2호증"]
- 날짜, 시간, 발언 내용은 증거에서 그대로 가져올 것

[금액 산정]
- 위자료: 증거에서 확인된 유책행위 정도 기반
- 지연손해금: 연 12% (소송촉진법 제3조)

[법적 근거]
- grounds 섹션의 "이혼 사유" 부분에 legal_basis 객체로 민법 제840조 인용

※ AI 생성 초안이며 변호사 검토 필수
"""
        }

    def _build_text_system_message(self) -> dict:
        """Build system message for text output mode (fallback)"""
        return {
            "role": "system",
            "content": """당신은 대한민국 가정법원에 제출하는 정식 소장(訴狀)을 작성하는 전문 법률가입니다.

[핵심 원칙 - 반드시 준수]
1. 모든 사실관계, 날짜, 발언 내용은 오직 제공된 "증거 자료"에서만 추출하세요
2. 증거에 없는 내용을 임의로 생성하거나 추측하지 마세요
3. 확인되지 않은 정보는 "확인 필요" 또는 "[미확인]"으로 표시하세요

[출력 형식 - Word 복사용 포맷팅 필수]
- 마크다운, 구분선(===, ---), *, # 기호 사용 금지
- 섹션 제목: 대문자로 "소 장", "청 구 취 지" 형식 (글자 사이 공백)
- 섹션 간: 빈 줄 2개로 구분
- 하위 항목: "1.", "가.", "(1)", "(가)" 형식으로 번호 매기기
- 들여쓰기: 각 수준마다 공백 4칸씩 추가
  - 1수준: 들여쓰기 없음
  - 2수준: 공백 4칸
  - 3수준: 공백 8칸
- 문단 내 줄바꿈: 한 문장이 끝나면 줄바꿈
- 법원명, 작성일: 문서 끝에 중앙 정렬처럼 앞에 공백 20칸 추가

[소장 구조 - 정확히 이 형식으로]

                    소       장

사    건    20__가단_______  이혼 등
원    고    [성명]
            [주소]
피    고    [성명]
            [주소]


                    청 구 취 지

1. 원고와 피고는 이혼한다.
2. 피고는 원고에게 위자료로 금 ______원을 지급하라.
3. 소송비용은 피고가 부담한다.
라는 판결을 구합니다.


                    청 구 원 인

1. 당사자들의 관계
    원고와 피고는 ____년 __월 __일 혼인신고를 마친 부부입니다.

2. 혼인생활의 경과
    가. [구체적 사실]
    나. [구체적 사실]

3. 이혼 사유 (민법 제840조)
    가. 피고의 유책행위
        (1) [증거 기반 사실] [갑 제1호증]
        (2) [증거 기반 사실] [갑 제2호증]

4. 위자료 청구
    피고의 위와 같은 유책행위로 인하여 원고는 정신적 고통을 받았으므로,
    그 위자료로 금 ______원을 청구합니다.


                    입 증 방 법

1. 갑 제1호증    [증거명]
2. 갑 제2호증    [증거명]


                    첨 부 서 류

1. 위 입증방법                    각 1통
2. 소장 부본                      1통


                                    20__. __. __.

                                    원고  [성명]  (인)


                    ____지방법원  귀중


[증거 인용 방식]
- 각 주장에 [갑 제N호증] 형식으로 증거 번호 명시
- 증거의 원문을 직접 인용: "피고는 '...'라고 발언하였다" [갑 제1호증]
- 날짜, 시간, 발언 내용은 증거에서 그대로 가져올 것

[금액 산정]
- 위자료: 증거에서 확인된 유책행위 정도 기반
- 지연손해금: 연 12% (소송촉진법 제3조)

※ AI 생성 초안이며 변호사 검토 필수
"""
        }

    def _build_json_user_message(
        self, case, sections, evidence_str, legal_str, precedent_str, consultation_str, fact_summary_str, language, style
    ) -> dict:
        """Build user message for JSON output mode"""
        # Include fact summary if available (014-case-fact-summary T025)
        fact_summary_section = f"""
**사건 사실관계 요약 (변호사 검토/수정본):**
{fact_summary_str}
""" if fact_summary_str else ""

        # Include consultation context if available (Issue #403)
        consultation_section = f"""
**상담 내역:**
{consultation_str}
""" if consultation_str and consultation_str != "(상담내역 없음)" else ""

        return {
            "role": "user",
            "content": f"""다음 정보를 바탕으로 이혼 소송 소장 초안을 JSON 형식으로 작성해 주세요.

**사건 정보:**
- 사건명: {case.title}
- 사건 설명: {case.description or "N/A"}

**생성할 섹션:**
{", ".join(sections)}
{fact_summary_section}{consultation_section}
**관련 법률 조문:**
{legal_str}

**유사 판례 참고자료:**
{precedent_str}

**증거 자료:**
{evidence_str}

**요청사항:**
- 언어: {language}
- 스타일: {style}
- 사건 사실관계 요약이 제공된 경우, 이를 최우선으로 참조하여 작성하세요
- 상담 내역이 제공된 경우, 의뢰인이 진술한 사실관계를 참조하세요
- 위 법률 조문과 증거를 기반으로 법률적 논리를 구성해 주세요
- 이혼 사유는 반드시 민법 제840조를 인용하여 작성하세요
- 유사 판례를 참고하여 위자료/재산분할 청구 논리를 보강하세요
- 각 주장에 대해 evidence_refs 배열에 증거 번호를 포함해 주세요

위 스키마에 맞는 JSON을 출력하세요. JSON 외의 텍스트는 출력하지 마세요.
"""
        }

    def _build_text_user_message(
        self, case, sections, evidence_str, legal_str, precedent_str, consultation_str, fact_summary_str, language, style
    ) -> dict:
        """Build user message for text output mode"""
        # Include fact summary if available (014-case-fact-summary T025)
        fact_summary_section = f"""
**사건 사실관계 요약 (변호사 검토/수정본):**
{fact_summary_str}
""" if fact_summary_str else ""

        # Include consultation context if available (Issue #403)
        consultation_section = f"""
**상담 내역:**
{consultation_str}
""" if consultation_str and consultation_str != "(상담내역 없음)" else ""

        return {
            "role": "user",
            "content": f"""다음 정보를 바탕으로 이혼 소송 소장 초안을 작성해 주세요.

**사건 정보:**
- 사건명: {case.title}
- 사건 설명: {case.description or "N/A"}

**생성할 섹션:**
{", ".join(sections)}
{fact_summary_section}{consultation_section}
**관련 법률 조문:**
{legal_str}

**유사 판례 참고자료:**
{precedent_str}

**증거 자료:**
{evidence_str}

**요청사항:**
- 언어: {language}
- 스타일: {style}
- 사건 사실관계 요약이 제공된 경우, 이를 최우선으로 참조하여 작성하세요
- 상담 내역이 제공된 경우, 의뢰인이 진술한 사실관계를 참조하세요
- 위 법률 조문과 증거를 기반으로 법률적 논리를 구성해 주세요
- 이혼 사유는 반드시 민법 제840조를 인용하여 작성하세요
- 유사 판례를 참고하여 위자료/재산분할 청구 논리를 보강하세요
- 각 주장에 대해 증거 번호를 명시해 주세요 (예: [갑 제1호증], [갑 제2호증])

소장 초안을 작성해 주세요.
"""
        }

    def build_ai_placeholder_prompt(
        self,
        placeholder_key: str,
        section: str,
        evidence_context: List[dict]
    ) -> List[dict]:
        """
        Build prompt for AI placeholder generation

        Args:
            placeholder_key: Key identifying the placeholder
            section: Section context
            evidence_context: Evidence data for context

        Returns:
            List of messages for GPT-4o
        """
        if self.rag_orchestrator:
            evidence_text = self.rag_orchestrator.format_evidence_context(evidence_context)
        else:
            evidence_text = self._format_evidence_context(evidence_context)

        system_prompt = """당신은 한국 가정법 전문 법률가입니다.
소장의 특정 부분을 작성해야 합니다.
증거 자료를 바탕으로 법적으로 정확하고 간결한 내용을 작성하세요.
- 증거를 인용할 때는 "갑 제N호증"으로 표기
- 민법 제840조 이혼 사유에 맞는 법률 용어 사용
- 문장은 완결형으로, 불필요한 수식어 제외"""

        section_guides = {
            "청구취지_내용": "청구취지를 작성하세요. 원고가 피고에게 요청하는 사항을 명확히 기재.",
            "청구원인_내용": "청구원인을 작성하세요. 이혼 사유와 그 근거를 증거와 함께 서술.",
            "grounds_content": "청구원인의 핵심 내용을 작성하세요.",
            "claims_content": "청구취지의 핵심 내용을 작성하세요."
        }

        guide = section_guides.get(placeholder_key, f"{placeholder_key} 내용을 작성하세요.")

        user_prompt = f"""## 작성 대상
{guide}

## 증거 자료
{evidence_text}

## 지침
- 증거에 기반한 사실만 기술
- 간결하고 법적으로 정확하게 작성
- 2-3문장 이내로 작성"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    # Fallback formatting methods (used when rag_orchestrator is not set)
    def _format_evidence_context(self, evidence_results: List[dict]) -> str:
        """Fallback evidence formatting"""
        if not evidence_results:
            return "(증거 자료 없음)"

        parts = []
        for i, doc in enumerate(evidence_results, 1):
            evidence_id = doc.get("chunk_id") or doc.get("id", f"ev_{i}")
            content = doc.get("document") or doc.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"[갑 제{i}호증] (ID: {evidence_id})\n{content}")
        return "\n\n".join(parts)

    def _format_legal_context(self, legal_results: List[dict]) -> str:
        """Fallback legal context formatting"""
        if not legal_results:
            return "(관련 법률 조문 없음)"

        parts = []
        for doc in legal_results:
            article = doc.get("article_number", "")
            content = doc.get("document", "") or doc.get("text", "")
            if article and content:
                parts.append(f"【{article}】\n{content}")
        return "\n\n".join(parts) if parts else "(관련 법률 조문 없음)"

    def _format_precedent_context(self, precedent_results: List[dict]) -> str:
        """Fallback precedent formatting"""
        if not precedent_results:
            return "(관련 판례 없음)"

        parts = []
        for i, p in enumerate(precedent_results, 1):
            case_ref = p.get("case_ref", "")
            summary = p.get("summary", "")[:200]
            parts.append(f"【판례 {i}】 {case_ref}\n{summary}")
        return "\n\n".join(parts)

    def _format_consultation_context(self, consultation_results: List[dict]) -> str:
        """Fallback consultation formatting (Issue #403)"""
        if not consultation_results:
            return "(상담내역 없음)"

        parts = []
        for i, c in enumerate(consultation_results, 1):
            summary = c.get("summary", "")[:300]
            consultation_date = c.get("date", "")
            consultation_type = c.get("type", "")
            type_labels = {"phone": "전화", "in_person": "대면", "online": "화상"}
            type_str = type_labels.get(consultation_type, consultation_type)
            parts.append(f"[상담 {i}] ({consultation_date}, {type_str})\n{summary}")
        return "\n\n".join(parts)
