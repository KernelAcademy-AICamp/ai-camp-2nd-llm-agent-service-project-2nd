"""
Draft Generator - 법률 문서 초안 생성기
이혼 소송 관련 법률 문서 초안을 자동 생성하는 모듈
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import OpenAI

from ..service_rag.schemas import (
    LegalTemplate,
    TemplateSection,
    DraftDocument,
    PartyInfo
)
from .analysis_engine import AnalysisResult


# ============================================================
# 기본 이혼 소장 템플릿 (AI Hub 데이터 없이 사용)
# ============================================================

DIVORCE_COMPLAINT_TEMPLATE = LegalTemplate(
    template_id="divorce_complaint_001",
    template_type="divorce_complaint",
    title="이혼 및 위자료 등 청구의 소",
    description="협의이혼 불성립 시 재판상 이혼을 청구하는 소장",
    sections=[
        TemplateSection(
            section_name="사건명",
            content_template="이혼 및 위자료 등 청구의 소",
            required=True,
            order=1
        ),
        TemplateSection(
            section_name="당사자",
            content_template="""
원고: {plaintiff_name}
      주민등록번호: {plaintiff_resident_number}
      주소: {plaintiff_address}
      연락처: {plaintiff_phone}

피고: {defendant_name}
      주민등록번호: {defendant_resident_number}
      주소: {defendant_address}
""",
            required=True,
            order=2
        ),
        TemplateSection(
            section_name="청구취지",
            content_template="""
1. 원고와 피고는 이혼한다.
2. 피고는 원고에게 위자료로 금 {alimony_amount}원을 지급하라.
3. {child_custody_claim}
4. 소송비용은 피고의 부담으로 한다.
라는 판결을 구합니다.
""",
            required=True,
            order=3
        ),
        TemplateSection(
            section_name="청구원인",
            content_template="""
1. 당사자의 관계
   원고와 피고는 {marriage_date}에 혼인신고를 마친 법률상 부부입니다.
   {children_info}

2. 혼인파탄의 경위
   {marriage_breakdown_reason}

3. 이혼 사유 (민법 제840조)
   {divorce_grounds}

4. 위자료 청구 원인
   {alimony_reason}

5. 결론
   이상과 같이 원고와 피고 사이의 혼인관계는 회복할 수 없을 정도로
   파탄되었으므로, 민법 제840조에 따라 이혼을 청구하며, 피고의
   유책행위로 인한 정신적 손해에 대하여 위자료를 청구합니다.
""",
            required=True,
            order=4
        ),
        TemplateSection(
            section_name="입증방법",
            content_template="""
1. 갑 제1호증: 혼인관계증명서
2. 갑 제2호증: 가족관계증명서
{evidence_list}
""",
            required=True,
            order=5
        ),
        TemplateSection(
            section_name="첨부서류",
            content_template="""
1. 위 입증방법 각 1통
2. 소장 부본 1통
3. 송달료 납부서 1통
""",
            required=True,
            order=6
        )
    ],
    placeholders=[
        "plaintiff_name", "plaintiff_resident_number", "plaintiff_address", "plaintiff_phone",
        "defendant_name", "defendant_resident_number", "defendant_address",
        "alimony_amount", "child_custody_claim", "marriage_date", "children_info",
        "marriage_breakdown_reason", "divorce_grounds", "alimony_reason", "evidence_list"
    ],
    example=None
)


# ============================================================
# Few-shot 프롬프트 예시 (AI Hub 판례 데이터 기반 고도화)
# ============================================================

FEW_SHOT_EXAMPLES = """
### 예시 1: 부정행위(외도)를 사유로 한 이혼 청구 (민법 제840조 제1호)
---
[증거 분석 결과]
- 유형: 카카오톡 대화
- 내용: 배우자가 제3자와 "보고싶어", "사랑해" 등의 메시지 교환
- 증거점수: 8.5/10
- 민법 제840조 해당 사유: 제1호 (배우자의 부정한 행위)

[대법원 판례 참조 - 2004다1899]
"간통에까지 이르지 않았다 하더라도 배우자 있는 부녀와 민법 제840조 제1호 소정의
부정한 행위, 즉, 부부 사이의 정조의무에 위반하는 것으로서 성적 신의성실의무에
위반하는 행위 또는 부부의 정조의무에 충실하지 않는 일체의 행위에 이름으로써
혼인관계의 파탄에 책임이 있는 경우 제3자는 이로 인하여 정신적 손해를 입은
배우자에 대하여 그 손해를 배상할 의무가 있다."

[청구원인 작성 예시]
피고는 2023년 3월경부터 OOO(이하 '상간자')과 부정한 관계를 맺어왔습니다.
원고는 피고의 휴대전화에서 상간자와 주고받은 카카오톡 메시지를 발견하였는데,
해당 대화에는 "보고싶어", "사랑해" 등 연인 사이에서나 할 수 있는 애정 표현이
다수 포함되어 있었습니다. 이러한 피고의 행위는 부부 사이의 정조의무 및 성적
신의성실의무에 위반하는 것으로서, 민법 제840조 제1호에서 규정하는 '배우자의
부정한 행위'에 해당합니다(대법원 2005. 5. 13. 선고 2004다1899 판결 참조).

### 예시 2: 악의의 유기를 사유로 한 이혼 청구 (민법 제840조 제2호)
---
[증거 분석 결과]
- 유형: 카카오톡 대화, 통화 녹음
- 내용: 배우자가 가출 후 연락 두절, 생활비 미지급
- 증거점수: 7.5/10
- 민법 제840조 해당 사유: 제2호 (배우자의 악의의 유기)

[대법원 판례 참조]
"주거지 문을 잠그고 피고를 집에 들어오지 못하게 한 후 가출신고를 하는 등으로
피고를 유기한 원고의 잘못으로 인하여 더 이상 회복하기 어려울 정도로 파탄에
이르렀다고 보이는바, 이는 민법 제840조 제2호, 3호, 6호의 이혼 사유에 해당한다."

"10년 이상 뚜렷한 이유 없이 원고와의 성관계를 거부한 점, 이에 대해 문제제기하는
원고와 진지한 대화 나누기를 회피한 점, 2003년경 이후 거의 집에 오지 않음으로써
원고와 자녀들을 사실상 유기한 점"

[청구원인 작성 예시]
피고는 2023년 5월경부터 정당한 이유 없이 가정에 돌아오지 않고 있으며,
원고와 자녀들의 생활비를 지급하지 않고 있습니다. 원고가 수차례 연락을
시도하였으나 피고는 "이혼하자"라는 메시지만 보낸 채 모든 연락을 거부하고
있습니다. 피고의 이러한 행위는 정당한 이유 없이 동거, 부양, 협조의 의무를
이행하지 않는 것으로서, 민법 제840조 제2호의 '악의의 유기'에 해당합니다.

### 예시 3: 심히 부당한 대우를 사유로 한 이혼 청구 (민법 제840조 제3호)
---
[증거 분석 결과]
- 유형: 통화 녹음, 진단서
- 내용: 욕설, 폭언, 폭행 등의 행위
- 증거점수: 8.0/10
- 민법 제840조 해당 사유: 제3호 (배우자로부터 심히 부당한 대우)

[대법원 판례 참조 - 2003므1890]
"민법 제840조 제3호 소정의 이혼사유인 '배우자로부터 심히 부당한 대우를 받았을 때'란
혼인관계의 지속을 강요하는 것이 참으로 가혹하다고 여겨질 정도의 폭행이나 학대
또는 모욕을 받았을 경우를 의미한다."

"경제적인 어려움이 닥치자 이를 모두 피고의 탓으로 돌리면서 피고를 폭행하는 등
부당한 대우를 한 잘못이 경합되어 초래되었다고 할 것인바, 피고의 위와 같은 잘못은
민법 제840조 제3호, 제6호에 정한 재판상 이혼사유에 해당한다."

[청구원인 작성 예시]
피고는 혼인 기간 중 원고에게 지속적으로 욕설과 폭언을 하였습니다. 특히
2023년 4월경에는 원고에게 폭력을 행사하여 상해를 가하였고, 이로 인해 원고는
OO병원에서 '전치 2주의 타박상' 진단을 받았습니다. 피고의 이러한 행위는
혼인관계의 지속을 강요하는 것이 참으로 가혹하다고 여겨질 정도의 폭행 및
학대에 해당하므로, 민법 제840조 제3호에서 규정하는 '심히 부당한 대우'에
해당합니다(대법원 2004. 2. 27. 선고 2003므1890 판결 참조).

### 예시 4: 혼인을 계속하기 어려운 중대한 사유 (민법 제840조 제6호)
---
[증거 분석 결과]
- 유형: 카카오톡 대화, 기타 증거
- 내용: 장기간 별거, 혼인관계 회복 불가
- 증거점수: 7.0/10
- 민법 제840조 해당 사유: 제6호 (기타 혼인을 계속하기 어려운 중대한 사유)

[대법원 판례 참조 - 2000므1561]
"피고가 혼인 이후 원고에게 폭력을 행사하고 계속적으로 수차에 걸쳐 각종 범죄행위를
저질러 징역형을 선고받고 복역중에 있음으로 인하여 정상적인 혼인관계를 유지할 수
없음을 이유로 한 것인데 이러한 경우에는 민법 제840조 제6호 소정의 '기타 혼인을
계속할 수 없는 중대한 사유'가 현재까지도 계속 존재하는 것으로 보아야 한다."

[청구원인 작성 예시]
원고와 피고는 2020년경부터 사실상 별거 상태에 있으며, 피고의 계속적인 비협조와
무관심으로 인하여 부부로서의 실체가 없는 상태입니다. 혼인관계 회복을 위한
원고의 수차례 노력에도 불구하고 피고는 이에 응하지 않았고, 이로 인해
원고와 피고 사이의 혼인관계는 더 이상 회복하기 어려울 정도로 파탄에
이르렀습니다. 이는 민법 제840조 제6호에서 규정하는 '기타 혼인을 계속하기
어려운 중대한 사유'에 해당합니다.
"""


class DraftGenerator:
    """
    법률 문서 초안 생성기

    분석된 증거를 바탕으로 이혼 소장 등 법률 문서 초안을 자동 생성합니다.
    GPT-4와 Few-shot 프롬프트를 활용하여 적절한 법적 표현을 생성합니다.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정하세요.")

        self.client = OpenAI(api_key=self.api_key)
        self.templates = {
            "divorce_complaint": DIVORCE_COMPLAINT_TEMPLATE
        }

    def generate_divorce_complaint(
        self,
        analysis_result: AnalysisResult,
        plaintiff: PartyInfo,
        defendant: PartyInfo,
        marriage_date: str,
        children_info: str = "슬하에 자녀가 없습니다.",
        alimony_amount: int = 30000000,
        child_custody_claim: str = "해당 없음"
    ) -> DraftDocument:
        """
        이혼 소장 초안 생성

        Args:
            analysis_result: 증거 분석 결과
            plaintiff: 원고(청구인) 정보
            defendant: 피고(상대방) 정보
            marriage_date: 혼인일
            children_info: 자녀 정보
            alimony_amount: 위자료 청구액
            child_custody_claim: 양육권 관련 청구 (있는 경우)

        Returns:
            DraftDocument: 생성된 소장 초안
        """
        # 1. 증거 분석 결과에서 핵심 정보 추출
        evidence_summary = self._extract_evidence_summary(analysis_result)

        # 2. GPT-4로 청구원인 및 이혼 사유 생성
        legal_reasoning = self._generate_legal_reasoning(evidence_summary)

        # 3. 증거 목록 생성
        evidence_list = self._format_evidence_list(analysis_result)

        # 4. 템플릿에 값 채우기
        template = self.templates["divorce_complaint"]

        content = self._fill_template(
            template=template,
            values={
                "plaintiff_name": plaintiff.name,
                "plaintiff_resident_number": plaintiff.resident_number or "추후 보완",
                "plaintiff_address": plaintiff.address,
                "plaintiff_phone": plaintiff.phone or "추후 보완",
                "defendant_name": defendant.name,
                "defendant_resident_number": defendant.resident_number or "추후 보완",
                "defendant_address": defendant.address,
                "alimony_amount": f"{alimony_amount:,}",
                "child_custody_claim": child_custody_claim,
                "marriage_date": marriage_date,
                "children_info": children_info,
                "marriage_breakdown_reason": legal_reasoning.get("breakdown_reason", ""),
                "divorce_grounds": legal_reasoning.get("legal_grounds", ""),
                "alimony_reason": legal_reasoning.get("alimony_reason", ""),
                "evidence_list": evidence_list
            }
        )

        # 5. DraftDocument 생성
        return DraftDocument(
            document_type="divorce_complaint",
            title=template.title,
            content=content,
            legal_grounds=legal_reasoning.get("applicable_articles", []),
            evidence_references=[f"evidence_{i}" for i in range(len(analysis_result.high_value_messages))],
            case_id=analysis_result.case_id,
            created_at=datetime.now().isoformat(),
            metadata={
                "template_id": template.template_id,
                "average_evidence_score": analysis_result.average_score,
                "total_evidence_count": analysis_result.total_messages,
                "high_value_evidence_count": len(analysis_result.high_value_messages)
            }
        )

    def _extract_evidence_summary(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """분석 결과에서 핵심 증거 정보 추출"""
        high_value_evidence = []

        for msg in analysis_result.high_value_messages[:10]:  # 상위 10개
            # ScoringResult 속성에 맞게 수정
            high_value_evidence.append({
                "content": msg.reasoning[:200] if msg.reasoning else "",  # 200자까지
                "score": msg.score,
                "matched_keywords": msg.matched_keywords,
                "article_840_tags": msg.matched_keywords  # 키워드를 태그로 사용
            })

        return {
            "case_id": analysis_result.case_id,
            "total_messages": analysis_result.total_messages,
            "average_score": analysis_result.average_score,
            "high_value_evidence": high_value_evidence,
            "risk_assessment": {
                "level": analysis_result.risk_assessment.risk_level.value if hasattr(analysis_result.risk_assessment.risk_level, 'value') else str(analysis_result.risk_assessment.risk_level),
                "primary_concerns": getattr(analysis_result.risk_assessment, 'primary_concerns', []) or getattr(analysis_result.risk_assessment, 'risk_factors', []),
                "recommendations": getattr(analysis_result.risk_assessment, 'recommendations', [])
            },
            "summary": analysis_result.summary
        }

    def _generate_legal_reasoning(self, evidence_summary: Dict[str, Any]) -> Dict[str, Any]:
        """GPT-4를 사용하여 법적 논거 생성"""

        # 증거에서 민법 제840조 태그 수집
        article_tags = set()
        for evidence in evidence_summary.get("high_value_evidence", []):
            tags = evidence.get("article_840_tags", [])
            article_tags.update(tags)

        system_prompt = f"""당신은 대한민국 가사법 전문 변호사입니다.
주어진 증거 분석 결과를 바탕으로 이혼 소장의 '청구원인' 부분을 작성해야 합니다.

다음 원칙을 준수하세요:
1. 민법 제840조의 이혼 사유를 명확히 적시
2. 증거와 법적 요건의 연결을 논리적으로 설명
3. 객관적이고 법률적인 표현 사용
4. 감정적 표현 지양, 사실 중심 기술

민법 제840조 (재판상 이혼원인):
1. 배우자에 부정한 행위가 있었을 때
2. 배우자가 악의로 다른 일방을 유기한 때
3. 배우자 또는 그 직계존속으로부터 심히 부당한 대우를 받았을 때
4. 자기의 직계존속이 배우자로부터 심히 부당한 대우를 받았을 때
5. 배우자의 생사가 3년 이상 분명하지 아니한 때
6. 기타 혼인을 계속하기 어려운 중대한 사유가 있을 때

{FEW_SHOT_EXAMPLES}
"""

        user_prompt = f"""다음 증거 분석 결과를 바탕으로 이혼 소장의 청구원인을 작성해주세요.

[증거 분석 결과]
- 전체 증거 수: {evidence_summary['total_messages']}건
- 평균 증거 점수: {evidence_summary['average_score']:.1f}/10
- 해당 민법 제840조 사유: {', '.join(article_tags) if article_tags else '분석 필요'}

[주요 증거 내용]
"""
        for i, ev in enumerate(evidence_summary.get("high_value_evidence", [])[:5], 1):
            user_prompt += f"""
{i}. 증거점수: {ev['score']:.1f}/10
   내용: {ev['content']}
   관련 조항: {', '.join(ev.get('article_840_tags', [])) or '미분류'}
"""

        user_prompt += """

위 내용을 바탕으로 다음 형식으로 작성해주세요:

1. 혼인파탄 경위 (breakdown_reason):
[배우자의 행위와 혼인 파탄 과정을 시간순으로 기술]

2. 이혼 사유 (legal_grounds):
[민법 제840조 해당 호수와 함께 법적 요건 충족 여부 설명]

3. 위자료 청구 원인 (alimony_reason):
[정신적 손해와 배우자의 유책성 기술]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            generated_text = response.choices[0].message.content

            # 응답 파싱
            result = self._parse_legal_reasoning(generated_text)
            result["applicable_articles"] = list(article_tags) if article_tags else ["제840조 제6호"]

            return result

        except Exception as e:
            # API 오류 시 기본 템플릿 반환
            return {
                "breakdown_reason": "[증거 분석 결과를 바탕으로 혼인파탄 경위를 기술해주세요]",
                "legal_grounds": f"위 사실관계는 민법 제840조에서 규정하는 재판상 이혼 사유에 해당합니다.",
                "alimony_reason": "[피고의 유책행위로 인한 정신적 손해를 기술해주세요]",
                "applicable_articles": list(article_tags) if article_tags else ["제840조 제6호"],
                "error": str(e)
            }

    def _parse_legal_reasoning(self, text: str) -> Dict[str, str]:
        """GPT 응답에서 각 섹션 파싱"""
        result = {
            "breakdown_reason": "",
            "legal_grounds": "",
            "alimony_reason": ""
        }

        sections = {
            "혼인파탄 경위": "breakdown_reason",
            "breakdown_reason": "breakdown_reason",
            "이혼 사유": "legal_grounds",
            "legal_grounds": "legal_grounds",
            "위자료 청구": "alimony_reason",
            "alimony_reason": "alimony_reason"
        }

        current_section = None
        current_content = []

        for line in text.split('\n'):
            line = line.strip()

            # 새 섹션 시작 확인
            section_found = False
            for key, value in sections.items():
                if key in line.lower() or key in line:
                    if current_section and current_content:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = value
                    current_content = []
                    section_found = True
                    break

            if not section_found and current_section:
                # 섹션 번호 제거 (1., 2., 3. 등)
                if line and not line.startswith(('1.', '2.', '3.')):
                    current_content.append(line)
                elif line.startswith(('1.', '2.', '3.')) and ':' not in line:
                    current_content.append(line)

        # 마지막 섹션 저장
        if current_section and current_content:
            result[current_section] = '\n'.join(current_content).strip()

        # 파싱 실패 시 전체 텍스트 사용
        if not any(result.values()):
            result["breakdown_reason"] = text

        return result

    def _format_evidence_list(self, analysis_result: AnalysisResult) -> str:
        """증거 목록 포맷팅"""
        evidence_lines = []

        for i, msg in enumerate(analysis_result.high_value_messages[:10], 3):
            # ScoringResult에서는 metadata가 없으므로 기본 유형 사용
            # 키워드 기반으로 증거 유형 추론
            keywords = getattr(msg, 'matched_keywords', [])
            keywords_str = ' '.join(keywords).lower()

            if any(k in keywords_str for k in ['대화', '메시지', '카톡']):
                evidence_type = "카카오톡 대화 내역"
            elif any(k in keywords_str for k in ['녹음', '통화']):
                evidence_type = "통화 녹음 녹취록"
            elif any(k in keywords_str for k in ['사진', '이미지']):
                evidence_type = "사진"
            elif any(k in keywords_str for k in ['영상', '동영상']):
                evidence_type = "영상"
            else:
                evidence_type = "카카오톡 대화 내역"  # 기본값

            evidence_lines.append(f"{i}. 갑 제{i}호증: {evidence_type}")

        return '\n'.join(evidence_lines)

    def _fill_template(self, template: LegalTemplate, values: Dict[str, str]) -> str:
        """템플릿에 값 채우기"""
        content_parts = []

        # 제목
        content_parts.append(f"# {template.title}\n")
        content_parts.append(f"---\n")

        # 각 섹션 처리
        sorted_sections = sorted(template.sections, key=lambda x: x.order)

        for section in sorted_sections:
            content_parts.append(f"\n## {section.section_name}\n")

            # 플레이스홀더 치환
            section_content = section.content_template
            for key, value in values.items():
                placeholder = "{" + key + "}"
                section_content = section_content.replace(placeholder, str(value))

            content_parts.append(section_content)

        # 날짜 및 서명란
        today = datetime.now()
        content_parts.append(f"""

---

{today.year}년 {today.month}월 {today.day}일

위 원고 {values.get('plaintiff_name', '___________')} (인)

OO가정법원 귀중
""")

        return '\n'.join(content_parts)

    def get_available_templates(self) -> List[str]:
        """사용 가능한 템플릿 목록 반환"""
        return list(self.templates.keys())

    def add_template(self, template: LegalTemplate) -> None:
        """새 템플릿 추가"""
        self.templates[template.template_type] = template
