"""
법률 문서 리스크 분석 시스템
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

from app.core.logging import logger
from app.models.document import Document, RiskLevel
from app.services.llm.generator import LLMGenerator
from app.services.rag.retriever import LegalRAGSystem


@dataclass
class RiskFactor:
    """리스크 요소"""
    category: str  # 리스크 카테고리
    severity: float  # 심각도 (0-1)
    description: str  # 설명
    location: Optional[str] = None  # 문서 내 위치
    recommendation: Optional[str] = None  # 권고사항


class RiskAnalyzer:
    """리스크 분석기 기본 클래스"""

    def __init__(self):
        """리스크 분석기 초기화"""
        self.risk_categories = {
            'legal_compliance': '법적 준수성',
            'financial': '재무적 리스크',
            'operational': '운영 리스크',
            'contractual': '계약상 리스크',
            'regulatory': '규제 리스크',
            'reputational': '평판 리스크',
            'security': '보안 리스크'
        }

        # 리스크 가중치
        self.weights = {
            'legal_compliance': 0.25,
            'financial': 0.20,
            'operational': 0.15,
            'contractual': 0.20,
            'regulatory': 0.10,
            'reputational': 0.05,
            'security': 0.05
        }

    def calculate_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """종합 리스크 점수 계산"""
        if not risk_factors:
            return 0.0

        # 카테고리별 점수 계산
        category_scores = {}
        for factor in risk_factors:
            if factor.category not in category_scores:
                category_scores[factor.category] = []
            category_scores[factor.category].append(factor.severity)

        # 가중 평균 계산
        total_score = 0.0
        total_weight = 0.0

        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            weight = self.weights.get(category, 0.1)
            total_score += avg_score * weight
            total_weight += weight

        if total_weight > 0:
            return total_score / total_weight

        return 0.0

    def determine_risk_level(self, risk_score: float) -> RiskLevel:
        """리스크 레벨 결정"""
        if risk_score >= 0.7:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


class DocumentRiskAnalyzer(RiskAnalyzer):
    """법률 문서 리스크 분석기"""

    def __init__(self):
        """문서 리스크 분석기 초기화"""
        super().__init__()
        self.llm_generator = LLMGenerator()
        self.rag_system = LegalRAGSystem()

        # 리스크 패턴
        self.risk_patterns = {
            'ambiguous_terms': {
                'patterns': [
                    r'약\s*\d+',
                    r'대략',
                    r'정도',
                    r'추정',
                    r'예상',
                    r'아마',
                    r'가능한'
                ],
                'severity': 0.3,
                'category': 'contractual',
                'description': '모호한 표현 사용'
            },
            'missing_deadline': {
                'patterns': [
                    r'기한\s*미정',
                    r'추후\s*협의',
                    r'별도\s*통보'
                ],
                'severity': 0.5,
                'category': 'operational',
                'description': '명확한 기한 누락'
            },
            'unfair_clause': {
                'patterns': [
                    r'일방적',
                    r'무조건',
                    r'절대적',
                    r'취소\s*불가',
                    r'환불\s*불가'
                ],
                'severity': 0.7,
                'category': 'legal_compliance',
                'description': '불공정 조항 가능성'
            },
            'liability_imbalance': {
                'patterns': [
                    r'모든\s*책임',
                    r'일체의\s*책임',
                    r'무한\s*책임'
                ],
                'severity': 0.6,
                'category': 'contractual',
                'description': '책임 불균형'
            },
            'personal_data': {
                'patterns': [
                    r'\d{6}-\d{7}',  # 주민등록번호
                    r'\d{3}-\d{2}-\d{5}',  # 사업자등록번호
                    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'  # 이메일
                ],
                'severity': 0.8,
                'category': 'security',
                'description': '개인정보 노출'
            }
        }

    async def analyze_document(
        self,
        document: Document,
        deep_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        문서 리스크 분석

        Args:
            document: 분석할 문서
            deep_analysis: 심층 분석 여부

        Returns:
            리스크 분석 결과
        """
        risk_factors = []

        # 1. 패턴 기반 분석
        pattern_risks = await self._analyze_patterns(document.content)
        risk_factors.extend(pattern_risks)

        # 2. 법적 준수성 분석
        compliance_risks = await self._analyze_legal_compliance(document)
        risk_factors.extend(compliance_risks)

        # 3. 계약 조건 분석
        if document.document_type.value == "contract":
            contract_risks = await self._analyze_contract_terms(document)
            risk_factors.extend(contract_risks)

        # 4. 심층 분석 (LLM 활용)
        if deep_analysis:
            deep_risks = await self._deep_analysis_with_llm(document)
            risk_factors.extend(deep_risks)

        # 종합 점수 계산
        risk_score = self.calculate_risk_score(risk_factors)
        risk_level = self.determine_risk_level(risk_score)

        # 결과 구성
        result = {
            'risk_level': risk_level.value,
            'risk_score': risk_score,
            'risk_factors': [
                {
                    'category': factor.category,
                    'severity': factor.severity,
                    'description': factor.description,
                    'location': factor.location,
                    'recommendation': factor.recommendation
                }
                for factor in risk_factors
            ],
            'summary': await self._generate_risk_summary(risk_factors, risk_level),
            'recommendations': await self._generate_recommendations(risk_factors),
            'analysis_timestamp': datetime.now().isoformat()
        }

        return result

    async def _analyze_patterns(self, content: str) -> List[RiskFactor]:
        """패턴 기반 리스크 분석"""
        risk_factors = []

        for risk_name, risk_config in self.risk_patterns.items():
            for pattern in risk_config['patterns']:
                matches = re.finditer(pattern, content, re.IGNORECASE)

                for match in matches:
                    risk_factor = RiskFactor(
                        category=risk_config['category'],
                        severity=risk_config['severity'],
                        description=risk_config['description'],
                        location=f"Position {match.start()}-{match.end()}: '{match.group()}'",
                        recommendation=f"{risk_config['description']}를 명확히 수정하세요"
                    )
                    risk_factors.append(risk_factor)

        return risk_factors

    async def _analyze_legal_compliance(self, document: Document) -> List[RiskFactor]:
        """법적 준수성 분석"""
        risk_factors = []

        # 관련 법률 조항 검색
        relevant_laws = await self.rag_system.search_laws(
            query=document.content[:500],
            top_k=10,
            category=self._get_law_category(document.document_type.value)
        )

        # 준수 여부 확인
        for law in relevant_laws:
            compliance_check = await self._check_law_compliance(
                document.content,
                law
            )

            if not compliance_check['compliant']:
                risk_factor = RiskFactor(
                    category='legal_compliance',
                    severity=compliance_check['severity'],
                    description=f"{law['law_name']} {law['article_number']} 위반 가능성",
                    recommendation=compliance_check['recommendation']
                )
                risk_factors.append(risk_factor)

        return risk_factors

    async def _analyze_contract_terms(self, document: Document) -> List[RiskFactor]:
        """계약 조건 분석"""
        risk_factors = []
        content = document.content

        # 필수 조항 확인
        required_clauses = [
            '계약 기간',
            '계약 금액',
            '지급 조건',
            '해지 조건',
            '손해배상',
            '분쟁 해결'
        ]

        for clause in required_clauses:
            if clause not in content:
                risk_factor = RiskFactor(
                    category='contractual',
                    severity=0.5,
                    description=f"필수 조항 누락: {clause}",
                    recommendation=f"{clause} 조항을 추가하세요"
                )
                risk_factors.append(risk_factor)

        # 불균형 조항 확인
        imbalance_checks = await self._check_contract_balance(content)
        risk_factors.extend(imbalance_checks)

        return risk_factors

    async def _deep_analysis_with_llm(self, document: Document) -> List[RiskFactor]:
        """LLM을 활용한 심층 분석"""
        risk_factors = []

        try:
            # LLM 프롬프트 구성
            prompt = f"""
            다음 법률 문서의 잠재적 리스크를 분석해주세요:

            문서 타입: {document.document_type.value}
            문서 내용:
            {document.content[:3000]}

            다음 관점에서 분석해주세요:
            1. 법적 리스크
            2. 재무적 리스크
            3. 운영상 리스크
            4. 평판 리스크

            각 리스크에 대해 심각도(0-1)와 권고사항을 제시해주세요.
            """

            # LLM 분석 수행
            analysis = await self.llm_generator.generate(
                prompt=prompt,
                max_tokens=1000
            )

            # 결과 파싱
            parsed_risks = self._parse_llm_risks(analysis)
            risk_factors.extend(parsed_risks)

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")

        return risk_factors

    def _parse_llm_risks(self, llm_output: str) -> List[RiskFactor]:
        """LLM 출력에서 리스크 파싱"""
        risk_factors = []

        # 간단한 파싱 로직 (실제로는 더 정교한 파싱 필요)
        lines = llm_output.split('\n')
        current_category = None
        current_severity = 0.5

        for line in lines:
            if '법적 리스크' in line:
                current_category = 'legal_compliance'
            elif '재무적 리스크' in line:
                current_category = 'financial'
            elif '운영상 리스크' in line:
                current_category = 'operational'
            elif '평판 리스크' in line:
                current_category = 'reputational'
            elif '심각도:' in line:
                try:
                    severity_match = re.search(r'심각도:\s*([\d.]+)', line)
                    if severity_match:
                        current_severity = float(severity_match.group(1))
                except:
                    pass
            elif current_category and len(line.strip()) > 10:
                risk_factor = RiskFactor(
                    category=current_category,
                    severity=current_severity,
                    description=line.strip(),
                    recommendation="전문가 검토 필요"
                )
                risk_factors.append(risk_factor)

        return risk_factors

    async def _check_law_compliance(
        self,
        content: str,
        law: Dict[str, Any]
    ) -> Dict[str, Any]:
        """특정 법률 준수 여부 확인"""
        # 간단한 준수성 체크 로직
        law_content = law.get('text', '')
        compliance = {
            'compliant': True,
            'severity': 0.0,
            'recommendation': ''
        }

        # 금지 사항 확인
        if '금지' in law_content or '불가' in law_content:
            # 문서에 금지된 내용이 있는지 확인
            prohibited_terms = re.findall(r'(\w+)를?\s*금지', law_content)
            for term in prohibited_terms:
                if term in content:
                    compliance['compliant'] = False
                    compliance['severity'] = 0.7
                    compliance['recommendation'] = f"{term} 관련 내용 수정 필요"
                    break

        # 의무 사항 확인
        if '의무' in law_content or '필수' in law_content:
            required_terms = re.findall(r'(\w+)를?\s*의무', law_content)
            for term in required_terms:
                if term not in content:
                    compliance['compliant'] = False
                    compliance['severity'] = 0.5
                    compliance['recommendation'] = f"{term} 관련 내용 추가 필요"
                    break

        return compliance

    async def _check_contract_balance(self, content: str) -> List[RiskFactor]:
        """계약 균형성 확인"""
        risk_factors = []

        # 갑/을의 권리와 의무 분석
        party_a_rights = len(re.findall(r'갑은.*할 수 있', content))
        party_a_duties = len(re.findall(r'갑은.*하여야', content))
        party_b_rights = len(re.findall(r'을은.*할 수 있', content))
        party_b_duties = len(re.findall(r'을은.*하여야', content))

        # 불균형 확인
        if party_a_rights > 0 and party_b_rights > 0:
            balance_ratio = party_a_rights / party_b_rights
            if balance_ratio > 2.0:
                risk_factor = RiskFactor(
                    category='contractual',
                    severity=0.6,
                    description="갑에게 과도하게 유리한 계약",
                    recommendation="을의 권리를 보강하여 균형 맞추기"
                )
                risk_factors.append(risk_factor)
            elif balance_ratio < 0.5:
                risk_factor = RiskFactor(
                    category='contractual',
                    severity=0.6,
                    description="을에게 과도하게 유리한 계약",
                    recommendation="갑의 권리를 보강하여 균형 맞추기"
                )
                risk_factors.append(risk_factor)

        return risk_factors

    def _get_law_category(self, document_type: str) -> str:
        """문서 타입에 따른 법률 카테고리 매핑"""
        mapping = {
            'contract': '민법',
            'lawsuit': '민사소송법',
            'notice': '민법',
            'employment': '근로기준법',
            'real_estate': '부동산법'
        }
        return mapping.get(document_type, '민법')

    async def _generate_risk_summary(
        self,
        risk_factors: List[RiskFactor],
        risk_level: RiskLevel
    ) -> str:
        """리스크 요약 생성"""
        if not risk_factors:
            return "식별된 중요한 리스크가 없습니다."

        # 카테고리별 리스크 수 계산
        category_counts = {}
        for factor in risk_factors:
            category = self.risk_categories.get(factor.category, factor.category)
            category_counts[category] = category_counts.get(category, 0) + 1

        # 요약문 생성
        summary_parts = [
            f"전체 리스크 레벨: {risk_level.value.upper()}",
            f"총 {len(risk_factors)}개의 리스크 요소 발견:"
        ]

        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"- {category}: {count}개")

        # 가장 심각한 리스크
        most_severe = max(risk_factors, key=lambda x: x.severity)
        summary_parts.append(f"\n가장 심각한 리스크: {most_severe.description} (심각도: {most_severe.severity:.2f})")

        return '\n'.join(summary_parts)

    async def _generate_recommendations(self, risk_factors: List[RiskFactor]) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        seen = set()

        # 우선순위별로 정렬
        sorted_factors = sorted(risk_factors, key=lambda x: x.severity, reverse=True)

        for factor in sorted_factors[:10]:  # 상위 10개만
            if factor.recommendation and factor.recommendation not in seen:
                recommendations.append({
                    'priority': 'HIGH' if factor.severity >= 0.7 else 'MEDIUM' if factor.severity >= 0.4 else 'LOW',
                    'recommendation': factor.recommendation,
                    'category': self.risk_categories.get(factor.category, factor.category)
                })
                seen.add(factor.recommendation)

        return recommendations


class RiskMitigator:
    """리스크 완화 제안 시스템"""

    def __init__(self):
        """리스크 완화기 초기화"""
        self.mitigation_strategies = {
            'legal_compliance': [
                "법률 전문가 검토 요청",
                "관련 법령 조항 명시적 인용",
                "준법 체크리스트 작성"
            ],
            'financial': [
                "재무 전문가 검토",
                "손실 한도 설정",
                "보험 가입 검토"
            ],
            'operational': [
                "명확한 프로세스 문서화",
                "책임 소재 명확화",
                "백업 계획 수립"
            ],
            'contractual': [
                "계약 조건 재협상",
                "면책 조항 추가",
                "분쟁 해결 조항 강화"
            ]
        }

    async def suggest_mitigations(
        self,
        risk_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """리스크 완화 방안 제안"""
        mitigations = []

        for risk_factor in risk_analysis.get('risk_factors', []):
            category = risk_factor['category']
            severity = risk_factor['severity']

            if severity >= 0.5:  # 중요한 리스크만
                strategies = self.mitigation_strategies.get(category, [])
                for strategy in strategies:
                    mitigations.append({
                        'risk_description': risk_factor['description'],
                        'mitigation_strategy': strategy,
                        'priority': 'HIGH' if severity >= 0.7 else 'MEDIUM',
                        'estimated_effort': self._estimate_effort(strategy)
                    })

        return mitigations

    def _estimate_effort(self, strategy: str) -> str:
        """완화 전략 실행 노력도 추정"""
        if '전문가' in strategy:
            return "HIGH"
        elif '문서화' in strategy or '작성' in strategy:
            return "MEDIUM"
        else:
            return "LOW"