"""
Vector Store Module
Handles ChromaDB operations for vector embeddings
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid


class VectorStore:
    """
    ChromaDB 벡터 저장소 래퍼

    로컬 ChromaDB를 사용하여 증거 벡터 임베딩을 저장하고 검색합니다.
    """

    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        VectorStore 초기화

        Args:
            persist_directory: ChromaDB 저장 디렉토리
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # ChromaDB 클라이언트 생성
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        # 컬렉션 생성 또는 가져오기
        self.collection = self.client.get_or_create_collection(
            name="leh_evidence",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )

    def add_evidence(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """
        단일 증거 추가

        Args:
            text: 증거 텍스트
            embedding: 벡터 임베딩 (768차원)
            metadata: 메타데이터 (chunk_id, file_id, case_id 등)

        Returns:
            str: 생성된 벡터 ID
        """
        vector_id = str(uuid.uuid4())

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[vector_id]
        )

        return vector_id

    def add_evidences(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        여러 증거 일괄 추가

        Args:
            texts: 증거 텍스트 리스트
            embeddings: 벡터 임베딩 리스트
            metadatas: 메타데이터 리스트

        Returns:
            List[str]: 생성된 벡터 ID 리스트
        """
        vector_ids = [str(uuid.uuid4()) for _ in texts]

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=vector_ids
        )

        return vector_ids

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색

        Args:
            query_embedding: 쿼리 임베딩
            n_results: 반환할 결과 개수
            where: 메타데이터 필터 (선택)

        Returns:
            List[Dict]: 검색 결과
                - distance: 유사도 거리
                - metadata: 메타데이터
                - document: 원본 텍스트
                - id: 벡터 ID
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        # 결과 변환
        formatted_results = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i] if 'metadatas' in results else {},
                    "document": results['documents'][0][i] if 'documents' in results else ""
                })

        return formatted_results

    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 벡터 조회

        Args:
            vector_id: 벡터 ID

        Returns:
            Dict: 벡터 정보 (metadata, document)
        """
        result = self.collection.get(
            ids=[vector_id],
            include=["metadatas", "documents"]
        )

        if result and result['ids']:
            return {
                "id": result['ids'][0],
                "metadata": result['metadatas'][0] if result['metadatas'] else {},
                "document": result['documents'][0] if result['documents'] else ""
            }

        return None

    def delete_by_id(self, vector_id: str) -> None:
        """
        ID로 벡터 삭제

        Args:
            vector_id: 삭제할 벡터 ID
        """
        self.collection.delete(ids=[vector_id])

    def count(self) -> int:
        """
        컬렉션 내 벡터 개수 반환

        Returns:
            int: 벡터 개수
        """
        return self.collection.count()

    def clear(self) -> None:
        """컬렉션 전체 삭제 (모든 벡터 제거)"""
        # 모든 ID를 가져와서 삭제
        all_data = self.collection.get()
        if all_data and all_data['ids']:
            self.collection.delete(ids=all_data['ids'])

    # ========== Case Isolation Methods ==========

    def count_by_case(self, case_id: str) -> int:
        """
        케이스별 벡터 개수 반환

        Args:
            case_id: 케이스 ID

        Returns:
            int: 해당 케이스의 벡터 개수
        """
        results = self.collection.get(
            where={"case_id": case_id}
        )

        if results and results['ids']:
            return len(results['ids'])

        return 0

    def delete_by_case(self, case_id: str) -> int:
        """
        케이스별 벡터 삭제

        Args:
            case_id: 삭제할 케이스 ID

        Returns:
            int: 삭제된 벡터 개수
        """
        # 케이스의 모든 벡터 ID 가져오기
        results = self.collection.get(
            where={"case_id": case_id}
        )

        if results and results['ids']:
            vector_ids = results['ids']
            self.collection.delete(ids=vector_ids)
            return len(vector_ids)

        return 0

    def verify_case_isolation(self, case_id: str) -> bool:
        """
        케이스 격리 검증

        Given: 특정 케이스 ID
        When: 해당 케이스의 벡터 검색
        Then: 모든 결과가 동일한 case_id를 가지는지 확인

        Args:
            case_id: 검증할 케이스 ID

        Returns:
            bool: 격리되어 있으면 True, 아니면 False
        """
        # 케이스의 모든 벡터 가져오기
        results = self.collection.get(
            where={"case_id": case_id},
            include=["metadatas"]
        )

        if not results or not results['ids']:
            # 벡터가 없으면 격리됨 (True)
            return True

        # 모든 메타데이터의 case_id가 일치하는지 확인
        if results['metadatas']:
            for metadata in results['metadatas']:
                if metadata.get('case_id') != case_id:
                    return False

        return True
