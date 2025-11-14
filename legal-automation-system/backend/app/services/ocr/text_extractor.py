"""
텍스트 추출 및 구조화 모듈
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import Counter
import asyncio

from konlpy.tag import Okt, Komoran, Kkma
from kss import split_sentences
import hanja

from app.core.logging import logger


class TextExtractor:
    """텍스트 추출 및 구조화 처리기"""

    def __init__(self):
        """텍스트 추출기 초기화"""
        # 한국어 형태소 분석기
        self.okt = Okt()
        self.komoran = Komoran()

        # 법률 문서 패턴
        self.legal_patterns = {
            'article': r'제(\d+)조\s*[\(（]([^)）]+)[\)）]',  # 조항
            'paragraph': r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 항
            'item': r'\d+\.',  # 호
            'subitem': r'[가나다라마바사아자차카타파하]\.', # 목
            'date': r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 날짜
            'amount': r'[\d,]+원',  # 금액
            'percentage': r'\d+(\.\d+)?%',  # 퍼센트
            'phone': r'\d{2,3}-\d{3,4}-\d{4}',  # 전화번호
            'registration': r'\d{6}-\d{7}',  # 주민등록번호 패턴
            'business': r'\d{3}-\d{2}-\d{5}',  # 사업자등록번호
        }

    async def extract_structured_text(
        self,
        raw_text: str,
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """
        원시 텍스트에서 구조화된 정보 추출

        Args:
            raw_text: 원시 텍스트
            document_type: 문서 타입

        Returns:
            구조화된 텍스트 정보
        """
        # 기본 정리
        cleaned_text = await self._clean_text(raw_text)

        # 문서 타입별 추출
        if document_type == "contract":
            result = await self._extract_contract_info(cleaned_text)
        elif document_type == "lawsuit":
            result = await self._extract_lawsuit_info(cleaned_text)
        elif document_type == "notice":
            result = await self._extract_notice_info(cleaned_text)
        else:
            result = await self._extract_general_info(cleaned_text)

        # 공통 정보 추가
        result['entities'] = await self._extract_entities(cleaned_text)
        result['key_terms'] = await self._extract_key_terms(cleaned_text)
        result['summary'] = await self._generate_summary(cleaned_text)

        return result

    async def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 한자 변환
        text = hanja.translate(text, 'substitution')

        # 특수문자 정규화
        text = re.sub(r'\s+', ' ', text)  # 다중 공백 제거
        text = re.sub(r'\n{3,}', '\n\n', text)  # 과도한 줄바꿈 제거

        # 유니코드 정규화
        import unicodedata
        text = unicodedata.normalize('NFKC', text)

        return text.strip()

    async def _extract_contract_info(self, text: str) -> Dict[str, Any]:
        """계약서 정보 추출"""
        info = {
            'type': 'contract',
            'parties': [],
            'terms': [],
            'dates': [],
            'amounts': [],
            'clauses': []
        }

        # 계약 당사자 추출
        party_patterns = [
            r'(갑|을|병|정)\s*:\s*([^\n]+)',
            r'(매도인|매수인)\s*:\s*([^\n]+)',
            r'(임대인|임차인)\s*:\s*([^\n]+)',
            r'(사용자|근로자)\s*:\s*([^\n]+)'
        ]

        for pattern in party_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                info['parties'].append({
                    'role': match.group(1),
                    'name': match.group(2).strip()
                })

        # 계약 조건 추출
        clause_pattern = self.legal_patterns['article']
        clauses = re.finditer(clause_pattern, text)

        for match in clauses:
            clause_num = match.group(1)
            clause_title = match.group(2)

            # 조항 내용 추출 (다음 조항까지)
            start = match.end()
            next_clause = re.search(clause_pattern, text[start:])
            end = start + next_clause.start() if next_clause else len(text)

            clause_content = text[start:end].strip()

            info['clauses'].append({
                'number': clause_num,
                'title': clause_title,
                'content': clause_content
            })

        # 날짜 추출
        date_matches = re.finditer(self.legal_patterns['date'], text)
        for match in date_matches:
            info['dates'].append(match.group())

        # 금액 추출
        amount_matches = re.finditer(self.legal_patterns['amount'], text)
        for match in amount_matches:
            info['amounts'].append(match.group())

        # 계약 기간 추출
        period_pattern = r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)부터\s*(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)까지'
        period_matches = re.finditer(period_pattern, text)

        for match in period_matches:
            info['terms'].append({
                'type': 'period',
                'start': match.group(1),
                'end': match.group(2)
            })

        return info

    async def _extract_lawsuit_info(self, text: str) -> Dict[str, Any]:
        """소장 정보 추출"""
        info = {
            'type': 'lawsuit',
            'court': None,
            'case_number': None,
            'plaintiff': [],
            'defendant': [],
            'claims': [],
            'facts': [],
            'evidence': []
        }

        # 법원 정보
        court_pattern = r'([\w\s]+법원)'
        court_match = re.search(court_pattern, text)
        if court_match:
            info['court'] = court_match.group(1)

        # 사건번호
        case_pattern = r'(\d{4}[\w]+\d+)'
        case_match = re.search(case_pattern, text)
        if case_match:
            info['case_number'] = case_match.group(1)

        # 원고/피고
        plaintiff_pattern = r'원\s*고\s*[:：]\s*([^\n]+)'
        defendant_pattern = r'피\s*고\s*[:：]\s*([^\n]+)'

        plaintiff_matches = re.finditer(plaintiff_pattern, text)
        for match in plaintiff_matches:
            info['plaintiff'].append(match.group(1).strip())

        defendant_matches = re.finditer(defendant_pattern, text)
        for match in defendant_matches:
            info['defendant'].append(match.group(1).strip())

        # 청구취지
        claim_section = re.search(r'청구취지(.*?)(?=청구원인|$)', text, re.DOTALL)
        if claim_section:
            info['claims'] = claim_section.group(1).strip()

        # 청구원인
        facts_section = re.search(r'청구원인(.*?)(?=입증|증거|$)', text, re.DOTALL)
        if facts_section:
            info['facts'] = facts_section.group(1).strip()

        return info

    async def _extract_notice_info(self, text: str) -> Dict[str, Any]:
        """내용증명 정보 추출"""
        info = {
            'type': 'notice',
            'sender': None,
            'recipient': None,
            'date': None,
            'subject': None,
            'demands': [],
            'deadline': None
        }

        # 발신인/수신인
        sender_pattern = r'발신인\s*[:：]\s*([^\n]+)'
        recipient_pattern = r'수신인\s*[:：]\s*([^\n]+)'

        sender_match = re.search(sender_pattern, text)
        if sender_match:
            info['sender'] = sender_match.group(1).strip()

        recipient_match = re.search(recipient_pattern, text)
        if recipient_match:
            info['recipient'] = recipient_match.group(1).strip()

        # 제목
        subject_pattern = r'제\s*목\s*[:：]\s*([^\n]+)'
        subject_match = re.search(subject_pattern, text)
        if subject_match:
            info['subject'] = subject_match.group(1).strip()

        # 요구사항
        demand_keywords = ['요구', '요청', '통지', '최고', '촉구']
        for keyword in demand_keywords:
            pattern = rf'{keyword}[^.。]*[.。]'
            demands = re.finditer(pattern, text)
            for match in demands:
                info['demands'].append(match.group().strip())

        # 기한
        deadline_pattern = r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)까지'
        deadline_match = re.search(deadline_pattern, text)
        if deadline_match:
            info['deadline'] = deadline_match.group(1)

        return info

    async def _extract_general_info(self, text: str) -> Dict[str, Any]:
        """일반 문서 정보 추출"""
        info = {
            'type': 'general',
            'sections': [],
            'dates': [],
            'numbers': [],
            'urls': [],
            'emails': []
        }

        # 섹션 분할
        sections = text.split('\n\n')
        for i, section in enumerate(sections):
            if section.strip():
                info['sections'].append({
                    'index': i,
                    'content': section.strip(),
                    'length': len(section)
                })

        # 날짜 추출
        date_matches = re.finditer(self.legal_patterns['date'], text)
        for match in date_matches:
            info['dates'].append(match.group())

        # URL 추출
        url_pattern = r'https?://[^\s]+'
        url_matches = re.finditer(url_pattern, text)
        for match in url_matches:
            info['urls'].append(match.group())

        # 이메일 추출
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_matches = re.finditer(email_pattern, text)
        for match in email_matches:
            info['emails'].append(match.group())

        return info

    async def _extract_entities(self, text: str) -> Dict[str, List]:
        """개체명 인식"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'amounts': [],
            'laws': []
        }

        # 형태소 분석
        try:
            pos_tags = self.komoran.pos(text)

            # 인명 추출 (NNP 고유명사)
            for word, tag in pos_tags:
                if tag == 'NNP':
                    # 인명 패턴 확인
                    if len(word) >= 2 and len(word) <= 4:
                        entities['persons'].append(word)

            # 조직명 패턴
            org_patterns = [
                r'[\w]+회사',
                r'[\w]+법인',
                r'[\w]+협회',
                r'[\w]+조합',
                r'[\w]+은행',
                r'[\w]+법원',
                r'[\w]+검찰청'
            ]

            for pattern in org_patterns:
                orgs = re.finditer(pattern, text)
                for match in orgs:
                    entities['organizations'].append(match.group())

            # 지역명 패턴
            location_patterns = [
                r'[\w]+시',
                r'[\w]+구',
                r'[\w]+동',
                r'[\w]+도',
                r'[\w]+군'
            ]

            for pattern in location_patterns:
                locs = re.finditer(pattern, text)
                for match in locs:
                    entities['locations'].append(match.group())

            # 법률명 패턴
            law_patterns = [
                r'[\w]+법',
                r'[\w]+령',
                r'[\w]+규칙',
                r'[\w]+조례'
            ]

            for pattern in law_patterns:
                laws = re.finditer(pattern, text)
                for match in laws:
                    entities['laws'].append(match.group())

        except Exception as e:
            logger.error(f"Entity extraction error: {e}")

        # 중복 제거
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    async def _extract_key_terms(self, text: str) -> List[str]:
        """핵심 용어 추출"""
        try:
            # 명사 추출
            nouns = self.okt.nouns(text)

            # 2글자 이상만 필터링
            filtered_nouns = [n for n in nouns if len(n) >= 2]

            # 빈도 계산
            noun_counts = Counter(filtered_nouns)

            # 상위 20개 추출
            key_terms = [term for term, count in noun_counts.most_common(20)]

            return key_terms

        except Exception as e:
            logger.error(f"Key term extraction error: {e}")
            return []

    async def _generate_summary(self, text: str, max_sentences: int = 5) -> str:
        """텍스트 요약"""
        try:
            # 문장 분리
            sentences = split_sentences(text)

            if len(sentences) <= max_sentences:
                return text

            # 간단한 추출 요약 (첫 문장과 마지막 문장 포함)
            summary_sentences = []

            # 첫 문장
            if sentences:
                summary_sentences.append(sentences[0])

            # 중간 중요 문장 (길이 기준)
            middle_sentences = sorted(sentences[1:-1], key=len, reverse=True)
            summary_sentences.extend(middle_sentences[:max_sentences-2])

            # 마지막 문장
            if len(sentences) > 1:
                summary_sentences.append(sentences[-1])

            return ' '.join(summary_sentences[:max_sentences])

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return text[:500] + "..."  # 실패 시 앞부분만 반환

    async def validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """추출된 데이터 검증"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # 필수 필드 확인
        if extracted_data.get('type') == 'contract':
            if not extracted_data.get('parties'):
                validation_results['errors'].append("계약 당사자 정보 없음")
                validation_results['valid'] = False

            if not extracted_data.get('clauses'):
                validation_results['warnings'].append("조항 정보 없음")

        elif extracted_data.get('type') == 'lawsuit':
            if not extracted_data.get('plaintiff'):
                validation_results['errors'].append("원고 정보 없음")
                validation_results['valid'] = False

            if not extracted_data.get('defendant'):
                validation_results['errors'].append("피고 정보 없음")
                validation_results['valid'] = False

        # 날짜 형식 검증
        for date in extracted_data.get('dates', []):
            if not re.match(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', date):
                validation_results['warnings'].append(f"비표준 날짜 형식: {date}")

        return validation_results