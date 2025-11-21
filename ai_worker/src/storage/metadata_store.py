"""
Metadata Store Module
Handles SQLite operations for evidence metadata
"""

import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from .schemas import EvidenceFile, EvidenceChunk


class MetadataStore:
    """
    SQLite 메타데이터 저장소

    증거 파일 및 청크의 메타데이터를 관리합니다.
    """

    def __init__(self, db_path: str = "./data/metadata.db"):
        """
        MetadataStore 초기화

        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 데이터베이스 초기화
        self._init_database()

    def _init_database(self) -> None:
        """데이터베이스 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # evidence_files 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_files (
                file_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                parsed_at TEXT NOT NULL,
                total_messages INTEGER NOT NULL,
                case_id TEXT NOT NULL,
                filepath TEXT
            )
        """)

        # evidence_chunks 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chunks (
                chunk_id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                content TEXT NOT NULL,
                score REAL,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                vector_id TEXT,
                case_id TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES evidence_files(file_id)
            )
        """)

        # 인덱스 생성 (검색 성능 향상)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_files_case_id
            ON evidence_files(case_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_file_id
            ON evidence_chunks(file_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_case_id
            ON evidence_chunks(case_id)
        """)

        conn.commit()
        conn.close()

    # ========== Evidence File Operations ==========

    def save_file(self, file: EvidenceFile) -> None:
        """
        증거 파일 저장

        Args:
            file: EvidenceFile 객체
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evidence_files
            (file_id, filename, file_type, parsed_at, total_messages, case_id, filepath)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            file.file_id,
            file.filename,
            file.file_type,
            file.parsed_at.isoformat(),
            file.total_messages,
            file.case_id,
            file.filepath
        ))

        conn.commit()
        conn.close()

    def get_file(self, file_id: str) -> Optional[EvidenceFile]:
        """
        파일 ID로 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceFile 또는 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_id, filename, file_type, parsed_at, total_messages, case_id, filepath
            FROM evidence_files
            WHERE file_id = ?
        """, (file_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return EvidenceFile(
                file_id=row[0],
                filename=row[1],
                file_type=row[2],
                parsed_at=datetime.fromisoformat(row[3]),
                total_messages=row[4],
                case_id=row[5],
                filepath=row[6]
            )

        return None

    def get_files_by_case(self, case_id: str) -> List[EvidenceFile]:
        """
        케이스 ID로 파일 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceFile 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_id, filename, file_type, parsed_at, total_messages, case_id, filepath
            FROM evidence_files
            WHERE case_id = ?
            ORDER BY parsed_at DESC
        """, (case_id,))

        rows = cursor.fetchall()
        conn.close()

        files = []
        for row in rows:
            files.append(EvidenceFile(
                file_id=row[0],
                filename=row[1],
                file_type=row[2],
                parsed_at=datetime.fromisoformat(row[3]),
                total_messages=row[4],
                case_id=row[5],
                filepath=row[6]
            ))

        return files

    def delete_file(self, file_id: str) -> None:
        """
        파일 삭제

        Args:
            file_id: 삭제할 파일 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM evidence_files WHERE file_id = ?", (file_id,))

        conn.commit()
        conn.close()

    # ========== Evidence Chunk Operations ==========

    def save_chunk(self, chunk: EvidenceChunk) -> None:
        """
        증거 청크 저장

        Args:
            chunk: EvidenceChunk 객체
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evidence_chunks
            (chunk_id, file_id, content, score, timestamp, sender, vector_id, case_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk.chunk_id,
            chunk.file_id,
            chunk.content,
            chunk.score,
            chunk.timestamp.isoformat(),
            chunk.sender,
            chunk.vector_id,
            chunk.case_id
        ))

        conn.commit()
        conn.close()

    def save_chunks(self, chunks: List[EvidenceChunk]) -> None:
        """
        여러 청크 일괄 저장

        Args:
            chunks: EvidenceChunk 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = [
            (
                chunk.chunk_id,
                chunk.file_id,
                chunk.content,
                chunk.score,
                chunk.timestamp.isoformat(),
                chunk.sender,
                chunk.vector_id,
                chunk.case_id
            )
            for chunk in chunks
        ]

        cursor.executemany("""
            INSERT INTO evidence_chunks
            (chunk_id, file_id, content, score, timestamp, sender, vector_id, case_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()
        conn.close()

    def get_chunk(self, chunk_id: str) -> Optional[EvidenceChunk]:
        """
        청크 ID로 조회

        Args:
            chunk_id: 청크 ID

        Returns:
            EvidenceChunk 또는 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, file_id, content, score, timestamp, sender, vector_id, case_id
            FROM evidence_chunks
            WHERE chunk_id = ?
        """, (chunk_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return EvidenceChunk(
                chunk_id=row[0],
                file_id=row[1],
                content=row[2],
                score=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                sender=row[5],
                vector_id=row[6],
                case_id=row[7]
            )

        return None

    def get_chunks_by_file(self, file_id: str) -> List[EvidenceChunk]:
        """
        파일 ID로 청크 목록 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceChunk 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, file_id, content, score, timestamp, sender, vector_id, case_id
            FROM evidence_chunks
            WHERE file_id = ?
            ORDER BY timestamp
        """, (file_id,))

        rows = cursor.fetchall()
        conn.close()

        return self._rows_to_chunks(rows)

    def get_chunks_by_case(self, case_id: str) -> List[EvidenceChunk]:
        """
        케이스 ID로 청크 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceChunk 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, file_id, content, score, timestamp, sender, vector_id, case_id
            FROM evidence_chunks
            WHERE case_id = ?
            ORDER BY timestamp
        """, (case_id,))

        rows = cursor.fetchall()
        conn.close()

        return self._rows_to_chunks(rows)

    def update_chunk_score(self, chunk_id: str, score: float) -> None:
        """
        청크 점수 업데이트

        Args:
            chunk_id: 청크 ID
            score: 새로운 점수
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE evidence_chunks
            SET score = ?
            WHERE chunk_id = ?
        """, (score, chunk_id))

        conn.commit()
        conn.close()

    def delete_chunk(self, chunk_id: str) -> None:
        """
        청크 삭제

        Args:
            chunk_id: 삭제할 청크 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM evidence_chunks WHERE chunk_id = ?", (chunk_id,))

        conn.commit()
        conn.close()

    # ========== Statistics & Aggregation ==========

    def count_files_by_case(self, case_id: str) -> int:
        """케이스별 파일 개수"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM evidence_files WHERE case_id = ?
        """, (case_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def count_chunks_by_case(self, case_id: str) -> int:
        """케이스별 청크 개수"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM evidence_chunks WHERE case_id = ?
        """, (case_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """
        케이스 요약 정보

        Args:
            case_id: 케이스 ID

        Returns:
            요약 정보 딕셔너리
        """
        return {
            "case_id": case_id,
            "file_count": self.count_files_by_case(case_id),
            "chunk_count": self.count_chunks_by_case(case_id)
        }

    def get_case_stats(self, case_id: str) -> Dict[str, Any]:
        """
        케이스 통계 정보 (get_case_summary 별칭)

        Args:
            case_id: 케이스 ID

        Returns:
            통계 정보 딕셔너리
        """
        return self.get_case_summary(case_id)

    # ========== Case Management ==========

    def list_cases(self) -> List[str]:
        """
        전체 케이스 ID 목록 조회

        Returns:
            케이스 ID 리스트 (중복 제거)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT case_id FROM evidence_files
            ORDER BY case_id
        """)

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def list_cases_with_stats(self) -> List[Dict[str, Any]]:
        """
        전체 케이스 ID 목록과 통계 조회

        Returns:
            케이스별 통계 정보 리스트
            [{"case_id": "...", "file_count": N, "chunk_count": M}, ...]
        """
        cases = self.list_cases()
        stats = []

        for case_id in cases:
            stats.append(self.get_case_stats(case_id))

        return stats

    def delete_case(self, case_id: str) -> None:
        """
        케이스 메타데이터 완전 삭제 (cascade)

        Args:
            case_id: 삭제할 케이스 ID

        Note:
            - 해당 케이스의 모든 청크 삭제
            - 해당 케이스의 모든 파일 삭제
            - 벡터는 삭제하지 않음 (delete_case_complete 사용)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. 청크 삭제 (foreign key로 자동 삭제 안 됨)
        cursor.execute("DELETE FROM evidence_chunks WHERE case_id = ?", (case_id,))

        # 2. 파일 삭제
        cursor.execute("DELETE FROM evidence_files WHERE case_id = ?", (case_id,))

        conn.commit()
        conn.close()

    def delete_case_complete(self, case_id: str, vector_store) -> None:
        """
        케이스 완전 삭제 (메타데이터 + 벡터)

        Args:
            case_id: 삭제할 케이스 ID
            vector_store: VectorStore 인스턴스 (벡터 삭제용)

        Note:
            1. 해당 케이스의 모든 청크에서 vector_id 추출
            2. VectorStore에서 벡터 삭제
            3. 메타데이터 삭제
        """
        # 1. 청크의 vector_id 목록 가져오기
        chunks = self.get_chunks_by_case(case_id)
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]

        # 2. 벡터 삭제
        for vector_id in vector_ids:
            try:
                vector_store.delete_by_id(vector_id)
            except Exception:
                # 벡터 삭제 실패는 무시 (이미 삭제되었을 수 있음)
                pass

        # 3. 메타데이터 삭제
        self.delete_case(case_id)

    # ========== Helper Methods ==========

    def _rows_to_chunks(self, rows: List[tuple]) -> List[EvidenceChunk]:
        """SQL 결과를 EvidenceChunk 리스트로 변환"""
        chunks = []
        for row in rows:
            chunks.append(EvidenceChunk(
                chunk_id=row[0],
                file_id=row[1],
                content=row[2],
                score=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                sender=row[5],
                vector_id=row[6],
                case_id=row[7]
            ))
        return chunks
