"""
Precedent Ingester Module
AI Hub 판례 데이터 인제스천

JSON 판례 데이터를 파싱하고 벡터 DB에 저장
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

from src.service_rag.legal_parser import CaseLawParser
from src.service_rag.legal_vectorizer import LegalVectorizer
from src.service_rag.schemas import CaseLaw

logger = logging.getLogger(__name__)


class PrecedentIngester:
    """
    AI Hub 판례 데이터 인제스천 클래스

    Given: JSON 형식 판례 데이터
    When: ingest_batch() 또는 ingest_from_file() 호출
    Then: 판례를 파싱하고 벡터 DB에 저장

    기능:
    - JSON 판례 파싱 (CaseLawParser 사용)
    - 판례 벡터화 (LegalVectorizer 사용)
    - 배치 처리 및 진행 콜백
    - 오류 처리 및 통계
    """

    def __init__(
        self,
        collection_name: str = "legal_knowledge",
        persist_directory: str = "./data/legal_vectors"
    ):
        """
        초기화

        Args:
            collection_name: 벡터 DB 컬렉션명
            persist_directory: 벡터 DB 저장 경로
        """
        self.parser = CaseLawParser()
        self.vectorizer = LegalVectorizer(
            collection_name=collection_name,
            persist_directory=persist_directory
        )

        # 통계
        self._stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

    def ingest_case(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 판례 인제스천

        Args:
            json_data: AI Hub JSON 판례 데이터

        Returns:
            Dict: 인제스천 결과 (chunk_id, case_number, etc.)

        Raises:
            ValueError: 파싱 또는 벡터화 실패 시
        """
        # JSON → CaseLaw 파싱
        case_law = self.parser.parse_json(json_data)

        # 벡터화 및 저장
        chunk_id = self.vectorizer.vectorize_case_law(case_law)

        return {
            'chunk_id': chunk_id,
            'case_id': case_law.case_id,
            'case_number': case_law.case_number,
            'court': case_law.court,
            'case_name': case_law.case_name,
            'category': case_law.category
        }

    def ingest_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        JSON 파일에서 판례 인제스천

        Args:
            file_path: JSON 파일 경로

        Returns:
            List[Dict]: 인제스천 결과 리스트
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 단일 객체면 리스트로 감싸기
        if isinstance(data, dict):
            json_cases = [data]
        else:
            json_cases = data

        return self.ingest_batch(json_cases)

    def ingest_batch(
        self,
        json_cases: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int, Dict], None]] = None,
        skip_errors: bool = False
    ) -> List[Dict[str, Any]]:
        """
        배치 판례 인제스천

        Args:
            json_cases: JSON 판례 데이터 리스트
            progress_callback: 진행 콜백 함수 (current, total, case_info)
            skip_errors: True면 오류 발생 시 해당 항목 건너뛰기

        Returns:
            List[Dict]: 성공한 인제스천 결과 리스트
        """
        results = []
        total = len(json_cases)

        self._stats['total_processed'] = 0
        self._stats['successful'] = 0
        self._stats['failed'] = 0
        self._stats['errors'] = []

        for idx, json_data in enumerate(json_cases, start=1):
            try:
                result = self.ingest_case(json_data)
                results.append(result)

                self._stats['successful'] += 1

                # 진행 콜백 호출
                if progress_callback:
                    progress_callback(idx, total, result)

            except Exception as e:
                self._stats['failed'] += 1
                error_info = {
                    'index': idx,
                    'case_id': json_data.get('info', {}).get('id', 'unknown'),
                    'error': str(e)
                }
                self._stats['errors'].append(error_info)

                logger.warning(f"Failed to ingest case {idx}: {e}")

                if not skip_errors:
                    raise

            finally:
                self._stats['total_processed'] += 1

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        인제스천 통계 반환

        Returns:
            Dict: 통계 정보 (total_processed, successful, failed, errors)
        """
        return self._stats.copy()

    def reset_stats(self):
        """통계 초기화"""
        self._stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
