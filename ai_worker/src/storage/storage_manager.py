"""
Storage Manager Module
Integrates parsers, vector store, and metadata store
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from .vector_store import VectorStore
from .metadata_store import MetadataStore
from .schemas import EvidenceFile, EvidenceChunk
from ..parsers.kakaotalk import KakaoTalkParser
from ..parsers.text import TextParser


def get_embedding(text: str) -> List[float]:
    """
    텍스트 임베딩 생성 (OpenAI API)

    Args:
        text: 임베딩할 텍스트

    Returns:
        List[float]: 768차원 임베딩 벡터

    Note:
        실제 환경에서는 OpenAI API를 호출합니다.
        테스트 환경에서는 Mock으로 대체됩니다.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        return response.data[0].embedding

    except Exception as e:
        # OpenAI API 실패 시 에러 발생
        raise Exception(f"Embedding generation failed: {e}")


class StorageManager:
    """
    통합 저장소 관리자

    파서, VectorStore, MetadataStore를 통합하여
    파일 처리 및 검색 기능을 제공합니다.
    """

    def __init__(
        self,
        vector_db_path: str = "./data/chromadb",
        metadata_db_path: str = "./data/metadata.db"
    ):
        """
        StorageManager 초기화

        Args:
            vector_db_path: ChromaDB 저장 경로
            metadata_db_path: SQLite 데이터베이스 경로
        """
        self.vector_store = VectorStore(persist_directory=vector_db_path)
        self.metadata_store = MetadataStore(db_path=metadata_db_path)

        # 파서 초기화
        self.parsers = {
            "kakaotalk": KakaoTalkParser(),
            "text": TextParser(),
            "pdf": TextParser()  # PDF도 TextParser 사용
        }

    def process_file(
        self,
        filepath: str,
        case_id: str
    ) -> Dict[str, Any]:
        """
        파일 처리 및 저장

        Given: 파일 경로와 케이스 ID
        When: 파일을 파싱하고 임베딩 생성 후 저장
        Then: 처리 결과 반환

        Args:
            filepath: 처리할 파일 경로
            case_id: 케이스 ID

        Returns:
            Dict: 처리 결과
                - file_id: 파일 ID
                - total_messages: 총 메시지 수
                - chunks_stored: 저장된 청크 수

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            Exception: 임베딩 또는 저장 실패 시
        """
        # 1. 파일 타입 감지 및 파서 선택
        file_type = self._detect_file_type(filepath)
        parser = self.parsers.get(file_type)

        if not parser:
            raise ValueError(f"Unsupported file type: {file_type}")

        # 2. 파일 파싱
        messages = parser.parse(filepath)

        if not messages:
            raise ValueError("No messages found in file")

        # 3. 파일 메타데이터 생성
        file_meta = EvidenceFile(
            filename=Path(filepath).name,
            file_type=file_type,
            total_messages=len(messages),
            case_id=case_id,
            filepath=str(Path(filepath).absolute())
        )

        try:
            # 4. 파일 메타데이터 저장
            self.metadata_store.save_file(file_meta)

            # 5. 각 메시지 처리 및 저장
            chunks_stored = 0
            for message in messages:
                # 청크 메타데이터 생성 (chunk_id 미리 생성)
                chunk = EvidenceChunk(
                    file_id=file_meta.file_id,
                    content=message.content,
                    timestamp=message.timestamp,
                    sender=message.sender,
                    case_id=case_id
                )

                # 임베딩 생성
                embedding = get_embedding(message.content)

                # 벡터 저장 (chunk_id 포함)
                vector_id = self.vector_store.add_evidence(
                    text=message.content,
                    embedding=embedding,
                    metadata={
                        "file_id": file_meta.file_id,
                        "sender": message.sender,
                        "case_id": case_id,
                        "chunk_id": chunk.chunk_id  # 청크 ID 포함
                    }
                )

                # vector_id 설정 후 저장
                chunk.vector_id = vector_id
                self.metadata_store.save_chunk(chunk)
                chunks_stored += 1

            return {
                "file_id": file_meta.file_id,
                "total_messages": len(messages),
                "chunks_stored": chunks_stored
            }

        except Exception as e:
            # 에러 발생 시 롤백
            self._rollback_file(file_meta.file_id)
            raise e

    def search(
        self,
        query: str,
        case_id: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        증거 검색

        Given: 검색 쿼리와 케이스 ID
        When: 임베딩 생성 후 벡터 검색
        Then: 관련 증거 반환

        Args:
            query: 검색 쿼리
            case_id: 케이스 ID
            top_k: 반환할 결과 개수

        Returns:
            List[Dict]: 검색 결과
        """
        # 쿼리 임베딩 생성
        query_embedding = get_embedding(query)

        # 벡터 검색 (케이스 ID로 필터링)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k,
            where={"case_id": case_id}
        )

        # 결과 포맷팅
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result["document"],
                "metadata": result["metadata"],
                "distance": result["distance"]
            })

        return formatted_results

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """
        케이스 요약 정보 조회

        Args:
            case_id: 케이스 ID

        Returns:
            Dict: 요약 정보
        """
        return self.metadata_store.get_case_summary(case_id)

    def get_case_files(self, case_id: str) -> List[EvidenceFile]:
        """
        케이스의 파일 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            List[EvidenceFile]: 파일 목록
        """
        return self.metadata_store.get_files_by_case(case_id)

    def get_case_chunks(self, case_id: str) -> List[EvidenceChunk]:
        """
        케이스의 청크 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            List[EvidenceChunk]: 청크 목록
        """
        return self.metadata_store.get_chunks_by_case(case_id)

    def _detect_file_type(self, filepath: str) -> str:
        """
        파일 타입 감지

        Args:
            filepath: 파일 경로

        Returns:
            str: 파일 타입 (kakaotalk/text/pdf)
        """
        path = Path(filepath)
        extension = path.suffix.lower()

        # 파일명으로 카카오톡 판단
        if "kakao" in path.name.lower():
            return "kakaotalk"

        # 확장자로 판단
        if extension == ".pdf":
            return "pdf"
        else:
            return "text"

    def _rollback_file(self, file_id: str) -> None:
        """
        파일 처리 실패 시 롤백

        Args:
            file_id: 롤백할 파일 ID
        """
        try:
            # 메타데이터 삭제
            self.metadata_store.delete_file(file_id)

            # 청크 삭제
            chunks = self.metadata_store.get_chunks_by_file(file_id)
            for chunk in chunks:
                if chunk.vector_id:
                    # 벡터 삭제
                    self.vector_store.delete_by_id(chunk.vector_id)
                # 청크 메타데이터 삭제
                self.metadata_store.delete_chunk(chunk.chunk_id)

        except Exception:
            # 롤백 실패는 무시 (이미 에러 상태)
            pass
