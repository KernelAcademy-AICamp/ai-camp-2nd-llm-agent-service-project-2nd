"""
Legal Knowledge Vectorizer Module
법률 문서(법령, 판례)를 벡터화하여 저장
"""

from typing import List
from src.storage.vector_store import VectorStore
from src.storage.storage_manager import get_embedding
from src.service_rag.schemas import Statute, CaseLaw


class LegalVectorizer:
    """
    법률 지식 벡터화 엔진

    Given: 법령 또는 판례 객체
    When: vectorize_statute() 또는 vectorize_case_law() 호출
    Then: 벡터 DB에 저장하고 chunk_id 반환

    기능:
    - 법령/판례 텍스트 임베딩 생성
    - 법률 특화 메타데이터 저장
    - VectorStore에 저장
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
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )

    def vectorize_statute(self, statute: Statute) -> str:
        """
        법령 벡터화

        Given: Statute 객체
        When: 법령 내용 임베딩 생성
        Then: VectorStore에 저장하고 chunk_id 반환

        Args:
            statute: 벡터화할 법령

        Returns:
            str: 생성된 chunk_id

        Raises:
            ValueError: 빈 내용인 경우
        """
        if not statute.content or statute.content.strip() == "":
            raise ValueError("Empty content in statute")

        # 임베딩 생성
        embedding = get_embedding(statute.content)

        # 메타데이터 구성
        metadata = {
            "doc_type": "statute",
            "doc_id": statute.statute_id,
            "statute_name": statute.name,
            "article_number": statute.article_number,
            "category": statute.category
        }

        if statute.statute_number:
            metadata["statute_number"] = statute.statute_number

        # VectorStore에 저장
        chunk_id = self.vector_store.add_evidence(
            text=statute.content,
            embedding=embedding,
            metadata=metadata
        )

        return chunk_id

    def vectorize_case_law(self, case_law: CaseLaw) -> str:
        """
        판례 벡터화

        Given: CaseLaw 객체
        When: 판결 요지 임베딩 생성
        Then: VectorStore에 저장하고 chunk_id 반환

        Args:
            case_law: 벡터화할 판례

        Returns:
            str: 생성된 chunk_id

        Raises:
            ValueError: 빈 요지인 경우
        """
        if not case_law.summary or case_law.summary.strip() == "":
            raise ValueError("Empty summary in case law")

        # 임베딩 생성 (판결 요지 사용)
        embedding = get_embedding(case_law.summary)

        # 메타데이터 구성
        metadata = {
            "doc_type": "case_law",
            "doc_id": case_law.case_id,
            "case_number": case_law.case_number,
            "court": case_law.court,
            "decision_date": case_law.decision_date.isoformat(),
            "case_name": case_law.case_name,
            "category": case_law.category
        }

        # VectorStore에 저장
        chunk_id = self.vector_store.add_evidence(
            text=case_law.summary,
            embedding=embedding,
            metadata=metadata
        )

        return chunk_id

    def vectorize_statutes_batch(self, statutes: List[Statute]) -> List[str]:
        """
        여러 법령 일괄 벡터화

        Args:
            statutes: 벡터화할 법령 리스트

        Returns:
            List[str]: 생성된 chunk_id 리스트
        """
        chunk_ids = []
        for statute in statutes:
            chunk_id = self.vectorize_statute(statute)
            chunk_ids.append(chunk_id)
        return chunk_ids

    def vectorize_cases_batch(self, cases: List[CaseLaw]) -> List[str]:
        """
        여러 판례 일괄 벡터화

        Args:
            cases: 벡터화할 판례 리스트

        Returns:
            List[str]: 생성된 chunk_id 리스트
        """
        chunk_ids = []
        for case in cases:
            chunk_id = self.vectorize_case_law(case)
            chunk_ids.append(chunk_id)
        return chunk_ids
