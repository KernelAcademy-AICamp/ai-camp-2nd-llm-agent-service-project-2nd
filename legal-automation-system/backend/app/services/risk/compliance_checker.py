"""
법률 준수성 검사 시스템
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.core.logging import logger
from app.models.document import Document
from app.services.rag.retriever import LegalRAGSystem


class ComplianceChecker:
    """법률 준수성 검사기"""

    def __init__(self):
        """준수성 검사기 초기화"""
        self.rag_system = LegalRAGSystem()

        # 준수성 체크 항목
        self.compliance_rules = {
            '개인정보보호': {
                'laws': ['개인정보보호법', '정보통신망법'],
                'required_elements': [
                    '개인정보 수집 동의',
                    '개인정보 이용 목적',
                    '개인정보 보유 기간',
                    '개인정보 제3자 제공',
                    '개인정보 파기'
                ],
                'prohibited_practices': [
                    '무단 수집',
                    '목적 외 이용',
                    '과도한 수집'
                ]
            },
            '전자상거래': {
                'laws': ['전자상거래법', '소비자기본법'],
                'required_elements': [
                    '청약철회',
                    '반품/환불',
                    '배송정보',
                    '판매자 정보'
                ],
                'prohibited_practices': [
                    '허위광고',
                    '기만행위',
                    '부당한 약관'
                ]
            },
            '근로계약': {
                'laws': ['근로기준법', '최저임금법'],
                'required_elements': [
                    '근로시간',
                    '임금',
                    '휴일/휴가',
                    '근로조건'
                ],
                'prohibited_practices': [
                    '최저임금 미달',
                    '부당해고',
                    '차별대우'
                ]
            },
            '부동산거래': {
                'laws': ['부동산거래신고법', '공인중개사법'],
                'required_elements': [
                    '매매가격',
                    '계약일자',
                    '소재지',
                    '권리관계'
                ],
                'prohibited_practices': [
                    '이중계약',
                    '허위매물',
                    '불법중개'
                ]
            },
            '금융거래': {
                'laws': ['금융실명법', '전자금융거래법'],
                'required_elements': [
                    '실명확인',
                    '거래내역',
                    '수수료',
                    '이자율'
                ],
                'prohibited_practices': [
                    '불법대출',
                    '고금리',
                    '불공정거래'
                ]
            }
        }

    async def check_compliance(
        self,
        document: Document,
        check_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        문서의 법률 준수성 검사

        Args:
            document: 검사할 문서
            check_categories: 검사할 카테고리 (None이면 전체)

        Returns:
            준수성 검사 결과
        """
        results = {
            'overall_compliance': True,
            'compliance_score': 100.0,
            'categories': {},
            'violations': [],
            'warnings': [],
            'recommendations': []
        }

        # 검사할 카테고리 결정
        categories_to_check = check_categories or list(self.compliance_rules.keys())

        # 문서 타입에 따른 관련 카테고리 자동 선택
        if not check_categories:
            categories_to_check = self._get_relevant_categories(document)

        # 각 카테고리별 검사
        for category in categories_to_check:
            if category in self.compliance_rules:
                category_result = await self._check_category_compliance(
                    document,
                    category
                )
                results['categories'][category] = category_result

                # 위반 사항 수집
                if category_result['violations']:
                    results['violations'].extend(category_result['violations'])
                    results['overall_compliance'] = False

                # 경고 사항 수집
                if category_result['warnings']:
                    results['warnings'].extend(category_result['warnings'])

        # 전체 준수 점수 계산
        results['compliance_score'] = self._calculate_compliance_score(results)

        # 권고사항 생성
        results['recommendations'] = await self._generate_recommendations(results)

        # 상세 보고서 생성
        results['detailed_report'] = await self._generate_detailed_report(results)

        return results

    async def _check_category_compliance(
        self,
        document: Document,
        category: str
    ) -> Dict[str, Any]:
        """카테고리별 준수성 검사"""
        rules = self.compliance_rules[category]
        result = {
            'category': category,
            'compliant': True,
            'score': 100.0,
            'violations': [],
            'warnings': [],
            'missing_elements': [],
            'prohibited_found': []
        }

        content = document.content

        # 필수 요소 확인
        for element in rules['required_elements']:
            if not self._check_element_present(content, element):
                result['missing_elements'].append(element)
                result['violations'].append({
                    'type': 'missing_required',
                    'description': f"필수 요소 누락: {element}",
                    'severity': 'HIGH',
                    'law_reference': rules['laws'][0]
                })
                result['compliant'] = False

        # 금지 사항 확인
        for practice in rules['prohibited_practices']:
            if self._check_prohibited_practice(content, practice):
                result['prohibited_found'].append(practice)
                result['violations'].append({
                    'type': 'prohibited_practice',
                    'description': f"금지된 내용 포함: {practice}",
                    'severity': 'CRITICAL',
                    'law_reference': rules['laws'][0]
                })
                result['compliant'] = False

        # 관련 법률 조항 확인
        law_compliance = await self._check_specific_laws(content, rules['laws'])
        result['law_compliance'] = law_compliance

        # 점수 계산
        result['score'] = self._calculate_category_score(result)

        return result

    def _check_element_present(self, content: str, element: str) -> bool:
        """필수 요소 존재 여부 확인"""
        # 요소에 대한 다양한 표현 확인
        variations = self._get_element_variations(element)

        for variation in variations:
            if re.search(variation, content, re.IGNORECASE):
                return True

        return False

    def _check_prohibited_practice(self, content: str, practice: str) -> bool:
        """금지 사항 포함 여부 확인"""
        # 금지 사항에 대한 패턴 확인
        patterns = self._get_prohibited_patterns(practice)

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _get_element_variations(self, element: str) -> List[str]:
        """필수 요소의 다양한 표현 반환"""
        variations_map = {
            '개인정보 수집 동의': [
                r'개인정보\s*수집.*동의',
                r'정보\s*수집.*동의',
                r'개인정보.*활용.*동의'
            ],
            '개인정보 이용 목적': [
                r'개인정보.*이용\s*목적',
                r'수집.*목적',
                r'정보.*활용.*목적'
            ],
            '청약철회': [
                r'청약\s*철회',
                r'구매\s*취소',
                r'주문\s*취소'
            ],
            '근로시간': [
                r'근로\s*시간',
                r'근무\s*시간',
                r'업무\s*시간'
            ],
            '임금': [
                r'임금',
                r'급여',
                r'보수'
            ]
        }

        return variations_map.get(element, [element])

    def _get_prohibited_patterns(self, practice: str) -> List[str]:
        """금지 사항 패턴 반환"""
        patterns_map = {
            '무단 수집': [
                r'동의\s*없이.*수집',
                r'무단.*수집',
                r'임의로.*수집'
            ],
            '목적 외 이용': [
                r'목적\s*외.*이용',
                r'다른.*목적.*사용',
                r'제3자.*제공'
            ],
            '최저임금 미달': [
                r'최저임금.*미만',
                r'최저임금.*이하',
                r'[\d,]+원(?!.*이상)'  # 구체적 금액 체크
            ],
            '부당해고': [
                r'즉시.*해고',
                r'일방적.*해고',
                r'통보.*없.*해고'
            ]
        }

        return patterns_map.get(practice, [practice])

    async def _check_specific_laws(
        self,
        content: str,
        laws: List[str]
    ) -> Dict[str, Any]:
        """특정 법률 준수 확인"""
        law_compliance = {}

        for law_name in laws:
            # 관련 법률 조항 검색
            relevant_articles = await self.rag_system.search_laws(
                query=content[:500],
                top_k=5,
                category=law_name
            )

            compliance_issues = []
            for article in relevant_articles:
                # 조항별 준수 확인
                if self._violates_article(content, article):
                    compliance_issues.append({
                        'article': article['article_number'],
                        'title': article.get('article_title', ''),
                        'violation': self._describe_violation(content, article)
                    })

            law_compliance[law_name] = {
                'compliant': len(compliance_issues) == 0,
                'issues': compliance_issues
            }

        return law_compliance

    def _violates_article(self, content: str, article: Dict[str, Any]) -> bool:
        """특정 조항 위반 여부 확인"""
        article_text = article.get('text', '')

        # 금지 규정 확인
        if '금지' in article_text or '하여서는 아니 된다' in article_text:
            # 금지된 행위가 문서에 있는지 확인
            prohibited_actions = re.findall(r'(\w+)를?\s*금지', article_text)
            for action in prohibited_actions:
                if action in content:
                    return True

        # 의무 규정 확인
        if '하여야 한다' in article_text or '의무' in article_text:
            # 의무 사항이 문서에 없는지 확인
            required_actions = re.findall(r'(\w+)를?\s*하여야', article_text)
            for action in required_actions:
                if action not in content:
                    return True

        return False

    def _describe_violation(self, content: str, article: Dict[str, Any]) -> str:
        """위반 사항 설명"""
        article_title = article.get('article_title', '')
        article_number = article.get('article_number', '')

        return f"{article_number} {article_title} 위반 가능성"

    def _get_relevant_categories(self, document: Document) -> List[str]:
        """문서 타입에 따른 관련 카테고리 결정"""
        type_category_map = {
            'contract': ['근로계약', '전자상거래'],
            'employment': ['근로계약'],
            'real_estate': ['부동산거래'],
            'financial': ['금융거래'],
            'privacy': ['개인정보보호']
        }

        doc_type = document.document_type.value
        categories = type_category_map.get(doc_type, [])

        # 문서 내용 기반 카테고리 추가
        content = document.content
        if '개인정보' in content:
            categories.append('개인정보보호')
        if '근로' in content or '고용' in content:
            categories.append('근로계약')
        if '부동산' in content or '임대' in content:
            categories.append('부동산거래')

        return list(set(categories))

    def _calculate_category_score(self, category_result: Dict[str, Any]) -> float:
        """카테고리별 준수 점수 계산"""
        score = 100.0

        # 위반 사항별 감점
        for violation in category_result['violations']:
            if violation['severity'] == 'CRITICAL':
                score -= 30
            elif violation['severity'] == 'HIGH':
                score -= 20
            elif violation['severity'] == 'MEDIUM':
                score -= 10
            else:
                score -= 5

        # 경고 사항별 감점
        score -= len(category_result['warnings']) * 3

        return max(0, score)

    def _calculate_compliance_score(self, results: Dict[str, Any]) -> float:
        """전체 준수 점수 계산"""
        if not results['categories']:
            return 100.0

        total_score = 0
        for category_result in results['categories'].values():
            total_score += category_result['score']

        return total_score / len(results['categories'])

    async def _generate_recommendations(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """권고사항 생성"""
        recommendations = []

        # 위반 사항에 대한 권고
        for violation in results['violations']:
            recommendation = {
                'priority': 'URGENT' if violation['severity'] == 'CRITICAL' else 'HIGH',
                'category': violation.get('category', 'General'),
                'issue': violation['description'],
                'action': self._get_remediation_action(violation),
                'law_reference': violation.get('law_reference', '')
            }
            recommendations.append(recommendation)

        # 경고 사항에 대한 권고
        for warning in results['warnings']:
            recommendation = {
                'priority': 'MEDIUM',
                'category': warning.get('category', 'General'),
                'issue': warning['description'],
                'action': self._get_improvement_action(warning)
            }
            recommendations.append(recommendation)

        return sorted(recommendations, key=lambda x: self._priority_order(x['priority']))

    def _get_remediation_action(self, violation: Dict[str, Any]) -> str:
        """위반 사항 개선 조치"""
        if violation['type'] == 'missing_required':
            return f"{violation['description'].replace('필수 요소 누락: ', '')} 조항을 추가하세요"
        elif violation['type'] == 'prohibited_practice':
            return f"{violation['description'].replace('금지된 내용 포함: ', '')} 관련 내용을 제거하거나 수정하세요"
        else:
            return "법률 전문가의 검토를 받으세요"

    def _get_improvement_action(self, warning: Dict[str, Any]) -> str:
        """경고 사항 개선 조치"""
        return f"{warning['description']}를 개선하는 것을 권장합니다"

    def _priority_order(self, priority: str) -> int:
        """우선순위 순서"""
        order = {
            'URGENT': 0,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3
        }
        return order.get(priority, 4)

    async def _generate_detailed_report(self, results: Dict[str, Any]) -> str:
        """상세 준수성 보고서 생성"""
        report_parts = [
            "=== 법률 준수성 검사 보고서 ===",
            f"\n검사 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"전체 준수 여부: {'준수' if results['overall_compliance'] else '미준수'}",
            f"준수 점수: {results['compliance_score']:.1f}/100",
            "\n--- 카테고리별 결과 ---"
        ]

        for category, category_result in results['categories'].items():
            report_parts.append(f"\n[{category}]")
            report_parts.append(f"  준수 여부: {'준수' if category_result['compliant'] else '미준수'}")
            report_parts.append(f"  점수: {category_result['score']:.1f}/100")

            if category_result['violations']:
                report_parts.append("  위반 사항:")
                for violation in category_result['violations']:
                    report_parts.append(f"    - {violation['description']}")

            if category_result['missing_elements']:
                report_parts.append("  누락된 필수 요소:")
                for element in category_result['missing_elements']:
                    report_parts.append(f"    - {element}")

        if results['recommendations']:
            report_parts.append("\n--- 권고사항 ---")
            for i, rec in enumerate(results['recommendations'][:5], 1):
                report_parts.append(f"{i}. [{rec['priority']}] {rec['action']}")

        return '\n'.join(report_parts)


class ComplianceMonitor:
    """준수성 모니터링 시스템"""

    def __init__(self):
        """모니터 초기화"""
        self.checker = ComplianceChecker()
        self.monitoring_history = []

    async def continuous_monitoring(
        self,
        document_id: int,
        interval_hours: int = 24
    ):
        """지속적 준수성 모니터링"""
        while True:
            try:
                # 문서 로드 및 검사
                # document = await load_document(document_id)
                # result = await self.checker.check_compliance(document)

                # 결과 저장
                # self.monitoring_history.append({
                #     'timestamp': datetime.now(),
                #     'document_id': document_id,
                #     'result': result
                # })

                # 변화 감지
                if len(self.monitoring_history) > 1:
                    changes = self._detect_changes(
                        self.monitoring_history[-2]['result'],
                        self.monitoring_history[-1]['result']
                    )

                    if changes:
                        await self._alert_changes(changes)

                # 대기
                await asyncio.sleep(interval_hours * 3600)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(3600)  # 에러 시 1시간 대기

    def _detect_changes(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """준수성 변화 감지"""
        changes = []

        # 점수 변화
        score_diff = current['compliance_score'] - previous['compliance_score']
        if abs(score_diff) > 5:
            changes.append({
                'type': 'score_change',
                'previous': previous['compliance_score'],
                'current': current['compliance_score'],
                'diff': score_diff
            })

        # 새로운 위반 사항
        prev_violations = set(v['description'] for v in previous['violations'])
        curr_violations = set(v['description'] for v in current['violations'])
        new_violations = curr_violations - prev_violations

        if new_violations:
            changes.append({
                'type': 'new_violations',
                'violations': list(new_violations)
            })

        return changes

    async def _alert_changes(self, changes: List[Dict[str, Any]]):
        """변화 알림"""
        for change in changes:
            logger.info(f"Compliance change detected: {change}")