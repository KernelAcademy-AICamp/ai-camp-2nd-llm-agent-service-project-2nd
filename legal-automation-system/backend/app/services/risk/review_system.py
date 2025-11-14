"""
법률 문서 검토 시스템
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import asyncio

from app.core.logging import logger
from app.models.document import Document
from app.services.llm.generator import LLMGenerator
from app.services.risk.risk_analyzer import DocumentRiskAnalyzer
from app.services.risk.compliance_checker import ComplianceChecker


@dataclass
class ReviewComment:
    """검토 코멘트"""
    section: str  # 문서 섹션
    line_number: Optional[int]  # 라인 번호
    comment_type: str  # error, warning, suggestion, info
    comment: str  # 코멘트 내용
    suggested_change: Optional[str] = None  # 제안 수정 내용
    reference: Optional[str] = None  # 참조 법령


class ReviewSystem:
    """문서 검토 시스템"""

    def __init__(self):
        """검토 시스템 초기화"""
        self.risk_analyzer = DocumentRiskAnalyzer()
        self.compliance_checker = ComplianceChecker()
        self.llm_generator = LLMGenerator()

        # 검토 체크리스트
        self.review_checklist = {
            'structure': [
                '문서 구조의 논리성',
                '조항 번호 체계',
                '참조 일관성',
                '형식 준수'
            ],
            'content': [
                '용어 정의 명확성',
                '모호한 표현 제거',
                '상충 조항 확인',
                '누락 내용 확인'
            ],
            'legal': [
                '관련 법령 준수',
                '필수 조항 포함',
                '금지 사항 확인',
                '법적 효력'
            ],
            'business': [
                '사업 목적 부합',
                '리스크 수준',
                '이익 균형',
                '실행 가능성'
            ]
        }

    async def review_document(
        self,
        document: Document,
        review_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        문서 종합 검토

        Args:
            document: 검토할 문서
            review_depth: 검토 깊이 (quick, standard, thorough)

        Returns:
            검토 결과
        """
        review_result = {
            'document_id': document.id,
            'review_date': datetime.now().isoformat(),
            'review_depth': review_depth,
            'overall_status': 'pending',
            'score': 0,
            'comments': [],
            'risk_analysis': {},
            'compliance_check': {},
            'recommendations': [],
            'approval_recommendation': None
        }

        try:
            # 1. 구조 검토
            structure_review = await self._review_structure(document)
            review_result['structure_review'] = structure_review
            review_result['comments'].extend(structure_review['comments'])

            # 2. 내용 검토
            content_review = await self._review_content(document)
            review_result['content_review'] = content_review
            review_result['comments'].extend(content_review['comments'])

            # 3. 법률적 검토
            if review_depth in ['standard', 'thorough']:
                legal_review = await self._review_legal_aspects(document)
                review_result['legal_review'] = legal_review
                review_result['comments'].extend(legal_review['comments'])

                # 리스크 분석
                risk_analysis = await self.risk_analyzer.analyze_document(
                    document,
                    deep_analysis=(review_depth == 'thorough')
                )
                review_result['risk_analysis'] = risk_analysis

                # 준수성 검사
                compliance_check = await self.compliance_checker.check_compliance(document)
                review_result['compliance_check'] = compliance_check

            # 4. 비즈니스 검토
            if review_depth == 'thorough':
                business_review = await self._review_business_aspects(document)
                review_result['business_review'] = business_review
                review_result['comments'].extend(business_review['comments'])

            # 5. 종합 평가
            review_result = await self._synthesize_review(review_result)

            # 6. 개선 권고사항 생성
            review_result['recommendations'] = await self._generate_recommendations(review_result)

            # 7. 승인 권고
            review_result['approval_recommendation'] = self._make_approval_recommendation(review_result)

        except Exception as e:
            logger.error(f"Document review error: {e}")
            review_result['overall_status'] = 'error'
            review_result['error'] = str(e)

        return review_result

    async def _review_structure(self, document: Document) -> Dict[str, Any]:
        """문서 구조 검토"""
        review = {
            'status': 'pass',
            'score': 100,
            'comments': [],
            'issues': []
        }

        content_lines = document.content.split('\n')

        # 조항 번호 체계 확인
        article_numbers = re.findall(r'제(\d+)조', document.content)
        if article_numbers:
            # 순차성 확인
            for i in range(1, len(article_numbers)):
                if int(article_numbers[i]) != int(article_numbers[i-1]) + 1:
                    comment = ReviewComment(
                        section='structure',
                        line_number=None,
                        comment_type='warning',
                        comment=f"조항 번호 불연속: 제{article_numbers[i-1]}조 다음 제{article_numbers[i]}조",
                        suggested_change="조항 번호를 순차적으로 수정"
                    )
                    review['comments'].append(comment)
                    review['score'] -= 10

        # 문서 구조 완성도 확인
        required_sections = self._get_required_sections(document.document_type.value)
        for section in required_sections:
            if section not in document.content:
                comment = ReviewComment(
                    section='structure',
                    line_number=None,
                    comment_type='error',
                    comment=f"필수 섹션 누락: {section}",
                    suggested_change=f"{section} 섹션을 추가하세요"
                )
                review['comments'].append(comment)
                review['score'] -= 15
                review['status'] = 'fail'

        # 형식 일관성 확인
        format_issues = self._check_format_consistency(content_lines)
        if format_issues:
            review['issues'].extend(format_issues)
            review['score'] -= len(format_issues) * 5

        return review

    async def _review_content(self, document: Document) -> Dict[str, Any]:
        """문서 내용 검토"""
        review = {
            'status': 'pass',
            'score': 100,
            'comments': [],
            'ambiguous_terms': [],
            'conflicts': []
        }

        # 모호한 표현 검색
        ambiguous_patterns = [
            (r'약\s*\d+', '구체적인 수치로 명시'),
            (r'적절한', '구체적인 기준 제시'),
            (r'상당한', '명확한 기준 제시'),
            (r'합리적인', '객관적 기준 제시'),
            (r'가능한\s*한', '명확한 조건 제시')
        ]

        for pattern, suggestion in ambiguous_patterns:
            matches = re.finditer(pattern, document.content)
            for match in matches:
                comment = ReviewComment(
                    section='content',
                    line_number=self._get_line_number(document.content, match.start()),
                    comment_type='warning',
                    comment=f"모호한 표현: '{match.group()}'",
                    suggested_change=suggestion
                )
                review['comments'].append(comment)
                review['ambiguous_terms'].append(match.group())
                review['score'] -= 3

        # 상충 조항 확인
        conflicts = await self._detect_conflicts(document.content)
        if conflicts:
            review['conflicts'] = conflicts
            for conflict in conflicts:
                comment = ReviewComment(
                    section='content',
                    line_number=None,
                    comment_type='error',
                    comment=f"조항 간 상충: {conflict['description']}",
                    suggested_change="상충하는 조항을 조정하세요"
                )
                review['comments'].append(comment)
                review['score'] -= 20
                review['status'] = 'fail'

        # 용어 일관성 확인
        term_inconsistencies = self._check_term_consistency(document.content)
        for inconsistency in term_inconsistencies:
            comment = ReviewComment(
                section='content',
                line_number=None,
                comment_type='suggestion',
                comment=f"용어 불일치: {inconsistency}",
                suggested_change="일관된 용어 사용"
            )
            review['comments'].append(comment)
            review['score'] -= 2

        return review

    async def _review_legal_aspects(self, document: Document) -> Dict[str, Any]:
        """법률적 측면 검토"""
        review = {
            'status': 'pass',
            'score': 100,
            'comments': [],
            'legal_issues': []
        }

        # LLM을 활용한 법률 검토
        legal_analysis = await self._llm_legal_review(document)

        # 법률 이슈 처리
        for issue in legal_analysis.get('issues', []):
            comment = ReviewComment(
                section='legal',
                line_number=None,
                comment_type='error' if issue['severity'] == 'high' else 'warning',
                comment=issue['description'],
                suggested_change=issue.get('suggestion', ''),
                reference=issue.get('law_reference', '')
            )
            review['comments'].append(comment)
            review['legal_issues'].append(issue)

            if issue['severity'] == 'high':
                review['score'] -= 20
                review['status'] = 'fail'
            else:
                review['score'] -= 10

        return review

    async def _review_business_aspects(self, document: Document) -> Dict[str, Any]:
        """비즈니스 측면 검토"""
        review = {
            'status': 'pass',
            'score': 100,
            'comments': [],
            'business_risks': []
        }

        # 계약 조건의 사업적 타당성
        if document.document_type.value == 'contract':
            # 지불 조건 확인
            payment_terms = re.findall(r'지급.*?(?=\.|$)', document.content)
            if not payment_terms:
                comment = ReviewComment(
                    section='business',
                    line_number=None,
                    comment_type='warning',
                    comment="지급 조건이 명시되지 않음",
                    suggested_change="명확한 지급 조건 추가"
                )
                review['comments'].append(comment)
                review['score'] -= 15

            # 책임 한계 확인
            if '책임 한계' not in document.content and '손해배상' not in document.content:
                comment = ReviewComment(
                    section='business',
                    line_number=None,
                    comment_type='warning',
                    comment="책임 한계 조항 부재",
                    suggested_change="책임 한계 및 손해배상 조항 추가 검토"
                )
                review['comments'].append(comment)
                review['business_risks'].append('unlimited_liability')
                review['score'] -= 10

        return review

    async def _detect_conflicts(self, content: str) -> List[Dict[str, Any]]:
        """조항 간 상충 감지"""
        conflicts = []

        # 기간 관련 상충
        period_matches = re.findall(r'(\d+)개월', content)
        if len(set(period_matches)) > 1:
            conflicts.append({
                'type': 'period_conflict',
                'description': f"서로 다른 기간 명시: {', '.join(set(period_matches))}개월"
            })

        # 책임 관련 상충
        if '전적인 책임' in content and '공동 책임' in content:
            conflicts.append({
                'type': 'responsibility_conflict',
                'description': "전적인 책임과 공동 책임이 동시에 명시됨"
            })

        return conflicts

    def _check_term_consistency(self, content: str) -> List[str]:
        """용어 일관성 확인"""
        inconsistencies = []

        # 동일 의미의 다른 표현 확인
        term_pairs = [
            ('계약자', '계약당사자'),
            ('임대인', '임대주'),
            ('임차인', '세입자'),
            ('매도인', '판매자'),
            ('매수인', '구매자')
        ]

        for term1, term2 in term_pairs:
            if term1 in content and term2 in content:
                inconsistencies.append(f"'{term1}'와 '{term2}' 혼용")

        return inconsistencies

    def _check_format_consistency(self, lines: List[str]) -> List[str]:
        """형식 일관성 확인"""
        issues = []

        # 번호 형식 일관성
        numbering_styles = set()
        for line in lines:
            if re.match(r'^\d+\.', line):
                numbering_styles.add('decimal')
            elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                numbering_styles.add('circled')
            elif re.match(r'^[가나다라마바사아자차]\.', line):
                numbering_styles.add('korean')

        if len(numbering_styles) > 1:
            issues.append(f"번호 형식 불일치: {', '.join(numbering_styles)}")

        return issues

    async def _llm_legal_review(self, document: Document) -> Dict[str, Any]:
        """LLM을 활용한 법률 검토"""
        try:
            prompt = f"""
            다음 법률 문서를 검토하고 법적 이슈를 식별해주세요:

            문서 타입: {document.document_type.value}
            문서 내용:
            {document.content[:2000]}

            검토 항목:
            1. 법적 효력 문제
            2. 필수 조항 누락
            3. 위법 가능성
            4. 불공정 조항

            각 이슈에 대해 심각도(high/medium/low)와 개선 방안을 제시해주세요.
            """

            response = await self.llm_generator.generate(prompt=prompt)

            # 응답 파싱
            issues = self._parse_legal_issues(response)

            return {'issues': issues}

        except Exception as e:
            logger.error(f"LLM legal review error: {e}")
            return {'issues': []}

    def _parse_legal_issues(self, llm_response: str) -> List[Dict[str, Any]]:
        """LLM 응답에서 법률 이슈 파싱"""
        issues = []

        # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
        lines = llm_response.split('\n')
        current_issue = {}

        for line in lines:
            if '심각도:' in line:
                severity = 'high' if 'high' in line.lower() else 'medium' if 'medium' in line.lower() else 'low'
                current_issue['severity'] = severity
            elif '이슈:' in line or '문제:' in line:
                current_issue['description'] = line.split(':', 1)[1].strip() if ':' in line else line
            elif '개선:' in line or '제안:' in line:
                current_issue['suggestion'] = line.split(':', 1)[1].strip() if ':' in line else line
                if current_issue.get('description'):
                    issues.append(current_issue)
                    current_issue = {}

        return issues

    def _get_required_sections(self, document_type: str) -> List[str]:
        """문서 타입별 필수 섹션"""
        sections_map = {
            'contract': ['계약 당사자', '계약 내용', '계약 기간', '계약 금액'],
            'lawsuit': ['원고', '피고', '청구취지', '청구원인'],
            'notice': ['발신인', '수신인', '통지 내용', '날짜']
        }

        return sections_map.get(document_type, [])

    def _get_line_number(self, content: str, position: int) -> int:
        """위치에서 라인 번호 계산"""
        return content[:position].count('\n') + 1

    async def _synthesize_review(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """검토 결과 종합"""
        total_score = 0
        total_weight = 0
        critical_issues = 0

        # 각 검토 영역 점수 종합
        review_areas = ['structure_review', 'content_review', 'legal_review', 'business_review']
        weights = {'structure_review': 0.2, 'content_review': 0.3, 'legal_review': 0.4, 'business_review': 0.1}

        for area in review_areas:
            if area in review_result:
                score = review_result[area]['score']
                weight = weights.get(area, 0.25)
                total_score += score * weight
                total_weight += weight

                if review_result[area]['status'] == 'fail':
                    critical_issues += 1

        # 최종 점수
        review_result['score'] = total_score / total_weight if total_weight > 0 else 0

        # 전체 상태 결정
        if critical_issues > 0:
            review_result['overall_status'] = 'rejected'
        elif review_result['score'] >= 80:
            review_result['overall_status'] = 'approved'
        elif review_result['score'] >= 60:
            review_result['overall_status'] = 'conditional'
        else:
            review_result['overall_status'] = 'rejected'

        return review_result

    async def _generate_recommendations(self, review_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """개선 권고사항 생성"""
        recommendations = []

        # 코멘트 기반 권고사항
        priority_map = {'error': 1, 'warning': 2, 'suggestion': 3, 'info': 4}

        for comment_dict in review_result.get('comments', []):
            if isinstance(comment_dict, ReviewComment):
                comment = comment_dict
            else:
                continue

            if comment.suggested_change:
                recommendations.append({
                    'priority': priority_map.get(comment.comment_type, 4),
                    'section': comment.section,
                    'issue': comment.comment,
                    'recommendation': comment.suggested_change,
                    'reference': comment.reference
                })

        # 우선순위별 정렬
        recommendations.sort(key=lambda x: x['priority'])

        return recommendations[:10]  # 상위 10개만

    def _make_approval_recommendation(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """승인 권고 생성"""
        status = review_result['overall_status']
        score = review_result['score']

        if status == 'approved':
            return {
                'decision': 'approve',
                'confidence': 'high',
                'reason': f"문서가 모든 검토 기준을 충족함 (점수: {score:.1f}/100)",
                'conditions': []
            }
        elif status == 'conditional':
            conditions = [rec['recommendation'] for rec in review_result['recommendations'][:3]]
            return {
                'decision': 'conditional_approve',
                'confidence': 'medium',
                'reason': f"일부 개선이 필요하나 승인 가능 (점수: {score:.1f}/100)",
                'conditions': conditions
            }
        else:
            critical_issues = [c.comment for c in review_result['comments']
                             if isinstance(c, ReviewComment) and c.comment_type == 'error'][:3]
            return {
                'decision': 'reject',
                'confidence': 'high',
                'reason': f"중요한 문제 발견으로 승인 불가 (점수: {score:.1f}/100)",
                'critical_issues': critical_issues
            }


class LegalReviewer:
    """법률 전문 검토자"""

    def __init__(self):
        """법률 검토자 초기화"""
        self.review_system = ReviewSystem()
        self.specialized_checks = {
            'contract': self._review_contract_specific,
            'lawsuit': self._review_lawsuit_specific,
            'notice': self._review_notice_specific
        }

    async def expert_review(
        self,
        document: Document,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """전문가 수준 검토"""
        # 기본 검토
        base_review = await self.review_system.review_document(document, review_depth='thorough')

        # 문서 타입별 특화 검토
        doc_type = document.document_type.value
        if doc_type in self.specialized_checks:
            specialized = await self.specialized_checks[doc_type](document)
            base_review['specialized_review'] = specialized

        # 포커스 영역 심화 검토
        if focus_areas:
            for area in focus_areas:
                if area == 'tax':
                    base_review['tax_review'] = await self._review_tax_implications(document)
                elif area == 'international':
                    base_review['intl_review'] = await self._review_international_aspects(document)

        return base_review

    async def _review_contract_specific(self, document: Document) -> Dict[str, Any]:
        """계약서 특화 검토"""
        return {
            'contract_type': self._identify_contract_type(document.content),
            'party_balance': self._assess_party_balance(document.content),
            'termination_clarity': self._check_termination_clarity(document.content),
            'payment_terms': self._analyze_payment_terms(document.content)
        }

    async def _review_lawsuit_specific(self, document: Document) -> Dict[str, Any]:
        """소장 특화 검토"""
        return {
            'claim_clarity': self._assess_claim_clarity(document.content),
            'evidence_sufficiency': self._check_evidence_references(document.content),
            'jurisdiction': self._verify_jurisdiction(document.content)
        }

    async def _review_notice_specific(self, document: Document) -> Dict[str, Any]:
        """내용증명 특화 검토"""
        return {
            'notice_effectiveness': self._assess_notice_effectiveness(document.content),
            'deadline_clarity': self._check_deadline_clarity(document.content),
            'legal_basis': self._verify_legal_basis(document.content)
        }

    async def _review_tax_implications(self, document: Document) -> Dict[str, Any]:
        """세무 관련 검토"""
        # 세무 관련 조항 분석
        return {'tax_issues': [], 'recommendations': []}

    async def _review_international_aspects(self, document: Document) -> Dict[str, Any]:
        """국제 거래 관련 검토"""
        # 국제 거래 조항 분석
        return {'international_issues': [], 'applicable_laws': []}

    # 헬퍼 메서드들
    def _identify_contract_type(self, content: str) -> str:
        if '매매' in content:
            return 'sales'
        elif '임대' in content:
            return 'lease'
        elif '고용' in content or '근로' in content:
            return 'employment'
        return 'general'

    def _assess_party_balance(self, content: str) -> str:
        # 당사자 간 균형 평가 로직
        return 'balanced'

    def _check_termination_clarity(self, content: str) -> bool:
        return '해지' in content or '종료' in content

    def _analyze_payment_terms(self, content: str) -> Dict[str, Any]:
        return {'payment_schedule': [], 'penalties': []}

    def _assess_claim_clarity(self, content: str) -> str:
        return 'clear' if '청구취지' in content else 'unclear'

    def _check_evidence_references(self, content: str) -> bool:
        return '증거' in content or '입증' in content

    def _verify_jurisdiction(self, content: str) -> bool:
        return '관할' in content

    def _assess_notice_effectiveness(self, content: str) -> str:
        return 'effective' if '통지' in content else 'ineffective'

    def _check_deadline_clarity(self, content: str) -> bool:
        return bool(re.search(r'\d+일\s*이내', content))

    def _verify_legal_basis(self, content: str) -> bool:
        return bool(re.search(r'제\d+조', content))