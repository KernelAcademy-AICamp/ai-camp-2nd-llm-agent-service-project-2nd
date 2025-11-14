"""
LLM 기반 법률 문서 생성 엔진
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
from enum import Enum

from openai import AsyncOpenAI
import anthropic
from jinja2 import Template

from app.core.config import settings
from app.models.document import DocumentType, DocumentStatus
from app.models.template import TemplateCategory


class LLMProvider(Enum):
    """LLM 제공자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class LegalDocumentGenerator:
    """법률 문서 생성 엔진"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.provider = LLMProvider(settings.DEFAULT_LLM_PROVIDER)

    async def generate_document(
        self,
        template: Dict[str, Any],
        user_data: Dict[str, Any],
        document_type: DocumentType,
        language: str = "korean"
    ) -> Dict[str, Any]:
        """
        법률 문서 생성

        Args:
            template: 문서 템플릿
            user_data: 사용자 입력 데이터
            document_type: 문서 타입
            language: 언어

        Returns:
            생성된 문서 정보
        """

        # 1. 템플릿과 사용자 데이터 결합
        filled_template = self._fill_template(template, user_data)

        # 2. LLM을 통한 문서 생성
        system_prompt = self._get_system_prompt(document_type, language)
        user_prompt = self._create_generation_prompt(filled_template, user_data, document_type)

        generated_content = await self._call_llm(system_prompt, user_prompt)

        # 3. 생성된 문서 후처리
        processed_document = self._postprocess_document(generated_content, document_type)

        # 4. 법률 조항 검증 및 추가
        validated_document = await self._validate_legal_compliance(processed_document, document_type)

        # 5. 메타데이터 추가
        final_document = self._add_metadata(validated_document, template, user_data)

        return final_document

    def _fill_template(self, template: Dict[str, Any], user_data: Dict[str, Any]) -> str:
        """템플릿에 사용자 데이터 채우기"""
        template_content = template.get("template_content", "")
        jinja_template = Template(template_content)

        # 기본값 설정
        default_data = {
            "current_date": datetime.now().strftime("%Y년 %m월 %d일"),
            "company_name": user_data.get("company_name", "[회사명]"),
            "representative": user_data.get("representative", "[대표자]"),
            "address": user_data.get("address", "[주소]"),
        }

        # 사용자 데이터와 기본값 병합
        merged_data = {**default_data, **user_data}

        return jinja_template.render(merged_data)

    def _get_system_prompt(self, document_type: DocumentType, language: str) -> str:
        """시스템 프롬프트 생성"""

        prompts = {
            DocumentType.CONTRACT: """
당신은 대한민국 법률 전문가이자 계약서 작성 전문가입니다.
다음 원칙을 준수하여 법적으로 유효하고 명확한 계약서를 작성하세요:

1. 대한민국 민법 및 관련 법령을 준수
2. 계약 당사자의 권리와 의무를 명확히 명시
3. 분쟁 소지가 있는 조항은 명확하게 해석
4. 필수 조항 누락 없이 포함
5. 법률 용어를 정확하게 사용

작성 시 다음 구조를 유지하세요:
- 계약 당사자 정보
- 계약 목적 및 내용
- 권리와 의무
- 계약 기간
- 위약 사항 및 손해배상
- 분쟁 해결 방법
- 기타 특약사항
""",
            DocumentType.LAWSUIT: """
당신은 대한민국 소송 전문 변호사입니다.
민사소송법에 따라 법적으로 완벽한 소장을 작성하세요:

1. 소장 필수 기재사항 모두 포함
2. 청구원인을 논리적이고 명확하게 서술
3. 관련 법령 및 판례 인용
4. 증거자료 목록 첨부
5. 청구취지를 명확하게 기재
""",
            DocumentType.NOTICE: """
당신은 법률 전문가로서 내용증명 작성 전문가입니다.
법적 효력이 있는 내용증명을 작성하세요:

1. 발신인과 수신인 정보 명확히 기재
2. 통지 내용을 구체적이고 명확하게 서술
3. 법적 근거 제시
4. 요구사항과 기한 명시
5. 불이행 시 법적 조치 예고
"""
        }

        base_prompt = prompts.get(document_type, prompts[DocumentType.CONTRACT])

        if language == "english":
            base_prompt = "You are a legal expert. " + base_prompt

        return base_prompt

    def _create_generation_prompt(
        self,
        filled_template: str,
        user_data: Dict[str, Any],
        document_type: DocumentType
    ) -> str:
        """문서 생성 프롬프트 생성"""

        prompt = f"""
다음 정보를 바탕으로 {document_type.value} 문서를 작성해주세요:

[기본 템플릿]
{filled_template}

[추가 정보]
"""

        # 사용자 데이터 추가
        for key, value in user_data.items():
            if value and key not in ["template_id", "user_id"]:
                prompt += f"- {key}: {value}\n"

        prompt += """

위 정보를 바탕으로:
1. 법적으로 유효한 문서를 작성하세요
2. 누락된 필수 조항이 있다면 추가하세요
3. 애매한 표현은 명확하게 수정하세요
4. 대한민국 법령에 맞게 작성하세요

최종 문서:
"""

        return prompt

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """LLM API 호출"""

        if self.provider == LLMProvider.OPENAI:
            return await self._call_openai(system_prompt, user_prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI API 호출"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Anthropic Claude API 호출"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=settings.LLM_MAX_TOKENS
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def _postprocess_document(self, content: str, document_type: DocumentType) -> str:
        """생성된 문서 후처리"""

        # 1. 불필요한 공백 제거
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        # 2. 문서 형식 정리
        if document_type == DocumentType.CONTRACT:
            content = self._format_contract(content)
        elif document_type == DocumentType.LAWSUIT:
            content = self._format_lawsuit(content)
        elif document_type == DocumentType.NOTICE:
            content = self._format_notice(content)

        # 3. 날짜 형식 통일
        content = self._standardize_dates(content)

        # 4. 법률 용어 검증
        content = self._validate_legal_terms(content)

        return content

    def _format_contract(self, content: str) -> str:
        """계약서 형식 정리"""
        # 계약서 제목 강조
        if "계약서" in content[:50]:
            lines = content.split('\n')
            lines[0] = f"【 {lines[0].strip()} 】"
            content = '\n'.join(lines)

        # 조항 번호 정리
        content = re.sub(r'제(\d+)조', r'제\1조', content)
        content = re.sub(r'제 (\d+) 조', r'제\1조', content)

        return content

    def _format_lawsuit(self, content: str) -> str:
        """소장 형식 정리"""
        # 소장 헤더 추가
        if "소    장" not in content[:30]:
            content = "소    장\n\n" + content

        # 당사자 표시 정리
        content = re.sub(r'원\s*고', '원  고', content)
        content = re.sub(r'피\s*고', '피  고', content)

        return content

    def _format_notice(self, content: str) -> str:
        """내용증명 형식 정리"""
        # 내용증명 제목 추가
        if "내용증명" not in content[:30]:
            content = "내 용 증 명\n\n" + content

        return content

    def _standardize_dates(self, content: str) -> str:
        """날짜 형식 표준화"""
        # YYYY-MM-DD → YYYY년 MM월 DD일
        pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        replacement = r'\1년 \2월 \3일'
        content = re.sub(pattern, replacement, content)

        return content

    def _validate_legal_terms(self, content: str) -> str:
        """법률 용어 검증 및 수정"""
        legal_terms = {
            "계약자": "계약당사자",
            "위반시": "위반 시",
            "손해 배상": "손해배상",
            "계약 해지": "계약해지",
        }

        for wrong, correct in legal_terms.items():
            content = content.replace(wrong, correct)

        return content

    async def _validate_legal_compliance(
        self,
        content: str,
        document_type: DocumentType
    ) -> str:
        """법률 준수 검증"""

        # 필수 조항 체크
        required_clauses = self._get_required_clauses(document_type)

        for clause in required_clauses:
            if clause not in content:
                # 누락된 조항 추가
                content = await self._add_missing_clause(content, clause, document_type)

        # 금지 조항 체크
        prohibited_terms = self._get_prohibited_terms()
        for term in prohibited_terms:
            content = content.replace(term, "")

        return content

    def _get_required_clauses(self, document_type: DocumentType) -> List[str]:
        """필수 조항 목록"""
        clauses = {
            DocumentType.CONTRACT: [
                "계약 당사자",
                "계약 목적",
                "계약 기간",
                "대금 지급",
                "계약 해지",
                "손해배상",
                "관할법원"
            ],
            DocumentType.LAWSUIT: [
                "원고",
                "피고",
                "청구취지",
                "청구원인",
                "입증방법",
                "첨부서류"
            ],
            DocumentType.NOTICE: [
                "발신인",
                "수신인",
                "통지 내용",
                "요구사항",
                "회신 기한"
            ]
        }

        return clauses.get(document_type, [])

    def _get_prohibited_terms(self) -> List[str]:
        """금지 용어 목록"""
        return [
            "절대적",
            "무조건",
            "영구히",
            "일체의 책임을 지지 않는다"
        ]

    async def _add_missing_clause(
        self,
        content: str,
        clause: str,
        document_type: DocumentType
    ) -> str:
        """누락된 조항 추가"""

        # 조항별 기본 내용
        default_clauses = {
            "관할법원": "\n\n제○조 (관할법원) 이 계약과 관련하여 발생하는 모든 분쟁은 [관할법원]을 제1심 관할법원으로 한다.",
            "손해배상": "\n\n제○조 (손해배상) 당사자 일방이 이 계약을 위반하여 상대방에게 손해를 발생시킨 경우, 그 손해를 배상하여야 한다.",
            "계약 해지": "\n\n제○조 (계약해지) 당사자 일방이 이 계약상의 의무를 위반한 경우, 상대방은 서면으로 계약해지를 통지할 수 있다."
        }

        if clause in default_clauses:
            content += default_clauses[clause]

        return content

    def _add_metadata(
        self,
        content: str,
        template: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """문서 메타데이터 추가"""

        return {
            "content": content,
            "metadata": {
                "template_id": template.get("id"),
                "template_name": template.get("name"),
                "created_at": datetime.now().isoformat(),
                "document_type": user_data.get("document_type"),
                "user_id": user_data.get("user_id"),
                "generation_model": settings.DEFAULT_LLM_MODEL,
                "word_count": len(content.split()),
                "estimated_reading_time": len(content.split()) // 200  # 분
            },
            "validation": {
                "legal_compliance": True,
                "required_clauses_present": True,
                "risk_assessment_needed": True
            }
        }


class ContractGenerator(LegalDocumentGenerator):
    """계약서 전문 생성기"""

    async def generate_employment_contract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """근로계약서 생성"""
        template = self._get_employment_template()
        return await self.generate_document(
            template,
            data,
            DocumentType.CONTRACT,
            "korean"
        )

    async def generate_lease_contract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """임대차계약서 생성"""
        template = self._get_lease_template()
        return await self.generate_document(
            template,
            data,
            DocumentType.CONTRACT,
            "korean"
        )

    async def generate_sales_contract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """매매계약서 생성"""
        template = self._get_sales_template()
        return await self.generate_document(
            template,
            data,
            DocumentType.CONTRACT,
            "korean"
        )

    def _get_employment_template(self) -> Dict[str, Any]:
        """근로계약서 템플릿"""
        return {
            "id": "employment_001",
            "name": "standard_employment_contract",
            "template_content": """
근 로 계 약 서

사용자(이하 "갑"이라 함) {{ employer_name }}과(와) 근로자(이하 "을"이라 함) {{ employee_name }}은(는) 다음과 같이 근로계약을 체결한다.

제1조 (근로계약기간)
{{ start_date }}부터 {{ end_date }}까지로 한다.

제2조 (근무장소)
{{ work_location }}

제3조 (업무내용)
{{ job_description }}

제4조 (근로시간)
1. 근로시간은 휴게시간을 제외하고 1일 {{ work_hours }}시간, 1주 {{ weekly_hours }}시간으로 한다.
2. 업무의 시작시각은 {{ start_time }}, 종료시각은 {{ end_time }}으로 한다.

제5조 (임금)
1. 월급: {{ monthly_salary }}원
2. 상여금: {{ bonus }}
3. 임금지급일: 매월 {{ pay_day }}일

제6조 (휴일 및 휴가)
근로기준법에서 정하는 바에 따른다.
"""
        }

    def _get_lease_template(self) -> Dict[str, Any]:
        """임대차계약서 템플릿"""
        return {
            "id": "lease_001",
            "name": "standard_lease_contract",
            "template_content": """
부동산 임대차 계약서

임대인 {{ lessor_name }}(이하 "갑"이라 함)과 임차인 {{ lessee_name }}(이하 "을"이라 함)은 다음과 같이 임대차계약을 체결한다.

제1조 (임대차 목적물)
소재지: {{ property_address }}
면적: {{ property_area }}

제2조 (임대차 기간)
{{ start_date }}부터 {{ end_date }}까지 {{ lease_period }}

제3조 (보증금 및 차임)
1. 보증금: {{ deposit }}원
2. 월차임: {{ monthly_rent }}원
3. 지불방법: 매월 {{ pay_day }}일 선불

제4조 (임대차 목적물의 사용)
"을"은 임대차 목적물을 {{ usage_purpose }}의 목적으로만 사용하여야 한다.
"""
        }

    def _get_sales_template(self) -> Dict[str, Any]:
        """매매계약서 템플릿"""
        return {
            "id": "sales_001",
            "name": "standard_sales_contract",
            "template_content": """
매 매 계 약 서

매도인 {{ seller_name }}(이하 "갑"이라 함)과 매수인 {{ buyer_name }}(이하 "을"이라 함)은 다음과 같이 매매계약을 체결한다.

제1조 (매매목적물)
품명: {{ item_name }}
수량: {{ quantity }}
규격: {{ specifications }}

제2조 (매매대금)
총 매매대금: {{ total_price }}원

제3조 (대금지급방법)
1. 계약금: {{ down_payment }}원 (계약시)
2. 잔금: {{ balance }}원 ({{ balance_date }})

제4조 (인도)
"갑"은 {{ delivery_date }}까지 매매목적물을 "을"에게 인도한다.
"""
        }