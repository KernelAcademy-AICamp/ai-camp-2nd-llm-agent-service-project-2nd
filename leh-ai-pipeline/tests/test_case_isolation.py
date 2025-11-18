"""
Case Isolation 테스트 (TDD RED Phase)

Given: 여러 케이스의 데이터가 저장됨
When: 케이스별 조회/삭제/검증 수행
Then: 케이스 간 데이터 격리 보장
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.storage.metadata_store import MetadataStore
from src.storage.vector_store import VectorStore
from src.storage.schemas import EvidenceFile, EvidenceChunk


class TestCaseListAndStats(unittest.TestCase):
    """케이스 목록 및 통계 조회 테스트"""

    def setUp(self):
        """테스트용 임시 데이터베이스 생성"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_metadata.db")
        self.store = MetadataStore(db_path=self.db_path)

    def tearDown(self):
        """임시 디렉토리 정리"""
        # ChromaDB 클라이언트 명시적으로 닫기 (Windows 파일 잠금 해제)
        if hasattr(self, 'vector_store'):
            del self.vector_store

        import gc
        gc.collect()  # 가비지 컬렉션으로 파일 핸들 해제

        import time
        time.sleep(0.1)  # 짧은 대기로 파일 잠금 해제 보장

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_cases_empty(self):
        """Given: 빈 데이터베이스
        When: list_cases() 호출
        Then: 빈 리스트 반환"""
        cases = self.store.list_cases()
        self.assertEqual(cases, [])

    def test_list_cases_multiple(self):
        """Given: 3개 케이스의 파일 저장
        When: list_cases() 호출
        Then: 3개 케이스 ID 반환"""
        # 3개 케이스 생성
        for case_id in ["case_001", "case_002", "case_003"]:
            file = EvidenceFile(
                filename=f"{case_id}_file.txt",
                file_type="text",
                total_messages=10,
                case_id=case_id
            )
            self.store.save_file(file)

        cases = self.store.list_cases()
        self.assertEqual(len(cases), 3)
        self.assertIn("case_001", cases)
        self.assertIn("case_002", cases)
        self.assertIn("case_003", cases)

    def test_list_cases_with_stats(self):
        """Given: 여러 파일/청크가 있는 케이스
        When: list_cases_with_stats() 호출
        Then: 케이스별 파일 수, 청크 수 포함"""
        # case_001: 파일 2개, 청크 5개
        for i in range(2):
            file = EvidenceFile(
                filename=f"file_{i}.txt",
                file_type="text",
                total_messages=3,
                case_id="case_001"
            )
            self.store.save_file(file)

            for j in range(3):
                chunk = EvidenceChunk(
                    file_id=file.file_id,
                    content=f"content {j}",
                    timestamp=datetime.now(),
                    sender="User",
                    case_id="case_001"
                )
                self.store.save_chunk(chunk)

        # case_002: 파일 1개, 청크 2개
        file = EvidenceFile(
            filename="file.txt",
            file_type="text",
            total_messages=2,
            case_id="case_002"
        )
        self.store.save_file(file)

        for j in range(2):
            chunk = EvidenceChunk(
                file_id=file.file_id,
                content=f"content {j}",
                timestamp=datetime.now(),
                sender="User",
                case_id="case_002"
            )
            self.store.save_chunk(chunk)

        stats = self.store.list_cases_with_stats()
        self.assertEqual(len(stats), 2)

        case_001_stats = next(s for s in stats if s["case_id"] == "case_001")
        self.assertEqual(case_001_stats["file_count"], 2)
        self.assertEqual(case_001_stats["chunk_count"], 6)

        case_002_stats = next(s for s in stats if s["case_id"] == "case_002")
        self.assertEqual(case_002_stats["file_count"], 1)
        self.assertEqual(case_002_stats["chunk_count"], 2)

    def test_get_case_stats(self):
        """Given: 특정 케이스 데이터
        When: get_case_stats(case_id) 호출
        Then: 해당 케이스의 통계 반환"""
        file = EvidenceFile(
            filename="file.txt",
            file_type="text",
            total_messages=3,
            case_id="case_123"
        )
        self.store.save_file(file)

        for i in range(3):
            chunk = EvidenceChunk(
                file_id=file.file_id,
                content=f"content {i}",
                timestamp=datetime.now(),
                sender="User",
                case_id="case_123"
            )
            self.store.save_chunk(chunk)

        stats = self.store.get_case_stats("case_123")
        self.assertEqual(stats["case_id"], "case_123")
        self.assertEqual(stats["file_count"], 1)
        self.assertEqual(stats["chunk_count"], 3)


class TestCaseCompleteDeletion(unittest.TestCase):
    """케이스 완전 삭제 테스트"""

    def setUp(self):
        """테스트용 임시 데이터베이스 생성"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_metadata.db")
        self.vector_path = str(Path(self.temp_dir) / "test_chromadb")
        self.metadata_store = MetadataStore(db_path=self.db_path)
        self.vector_store = VectorStore(persist_directory=self.vector_path)

    def tearDown(self):
        """임시 디렉토리 정리"""
        # ChromaDB 클라이언트 명시적으로 닫기 (Windows 파일 잠금 해제)
        if hasattr(self, 'vector_store'):
            del self.vector_store

        import gc
        gc.collect()  # 가비지 컬렉션으로 파일 핸들 해제

        import time
        time.sleep(0.1)  # 짧은 대기로 파일 잠금 해제 보장

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_delete_case_metadata_only(self):
        """Given: 케이스의 파일과 청크
        When: delete_case_metadata(case_id) 호출
        Then: 해당 케이스의 모든 메타데이터 삭제"""
        # 데이터 생성
        file = EvidenceFile(
            filename="file.txt",
            file_type="text",
            total_messages=2,
            case_id="case_to_delete"
        )
        self.metadata_store.save_file(file)

        for i in range(2):
            chunk = EvidenceChunk(
                file_id=file.file_id,
                content=f"content {i}",
                timestamp=datetime.now(),
                sender="User",
                case_id="case_to_delete"
            )
            self.metadata_store.save_chunk(chunk)

        # 삭제 전 확인
        files = self.metadata_store.get_files_by_case("case_to_delete")
        chunks = self.metadata_store.get_chunks_by_case("case_to_delete")
        self.assertEqual(len(files), 1)
        self.assertEqual(len(chunks), 2)

        # 케이스 삭제
        self.metadata_store.delete_case("case_to_delete")

        # 삭제 후 확인
        files = self.metadata_store.get_files_by_case("case_to_delete")
        chunks = self.metadata_store.get_chunks_by_case("case_to_delete")
        self.assertEqual(len(files), 0)
        self.assertEqual(len(chunks), 0)

    def test_delete_case_with_vectors(self):
        """Given: 케이스의 메타데이터 + 벡터
        When: delete_case_complete(case_id) 호출
        Then: 메타데이터와 벡터 모두 삭제"""
        # 메타데이터 생성
        file = EvidenceFile(
            filename="file.txt",
            file_type="text",
            total_messages=2,
            case_id="case_with_vectors"
        )
        self.metadata_store.save_file(file)

        # 벡터 추가
        vector_ids = []
        for i in range(2):
            vector_id = self.vector_store.add_evidence(
                text=f"content {i}",
                embedding=[0.1] * 768,
                metadata={"case_id": "case_with_vectors", "file_id": file.file_id}
            )
            vector_ids.append(vector_id)

            chunk = EvidenceChunk(
                file_id=file.file_id,
                content=f"content {i}",
                timestamp=datetime.now(),
                sender="User",
                case_id="case_with_vectors",
                vector_id=vector_id
            )
            self.metadata_store.save_chunk(chunk)

        # 삭제 전 벡터 존재 확인
        for vector_id in vector_ids:
            vector = self.vector_store.get_by_id(vector_id)
            self.assertIsNotNone(vector)

        # 완전 삭제 (메타데이터 + 벡터)
        self.metadata_store.delete_case_complete(
            case_id="case_with_vectors",
            vector_store=self.vector_store
        )

        # 메타데이터 삭제 확인
        files = self.metadata_store.get_files_by_case("case_with_vectors")
        chunks = self.metadata_store.get_chunks_by_case("case_with_vectors")
        self.assertEqual(len(files), 0)
        self.assertEqual(len(chunks), 0)

        # 벡터 삭제 확인
        for vector_id in vector_ids:
            vector = self.vector_store.get_by_id(vector_id)
            self.assertIsNone(vector)

    def test_delete_case_preserves_other_cases(self):
        """Given: 2개 케이스 존재
        When: 하나의 케이스 삭제
        Then: 다른 케이스는 영향 받지 않음"""
        # case_001 생성
        file1 = EvidenceFile(
            filename="file1.txt",
            file_type="text",
            total_messages=1,
            case_id="case_001"
        )
        self.metadata_store.save_file(file1)

        chunk1 = EvidenceChunk(
            file_id=file1.file_id,
            content="case_001 content",
            timestamp=datetime.now(),
            sender="User",
            case_id="case_001"
        )
        self.metadata_store.save_chunk(chunk1)

        # case_002 생성
        file2 = EvidenceFile(
            filename="file2.txt",
            file_type="text",
            total_messages=1,
            case_id="case_002"
        )
        self.metadata_store.save_file(file2)

        chunk2 = EvidenceChunk(
            file_id=file2.file_id,
            content="case_002 content",
            timestamp=datetime.now(),
            sender="User",
            case_id="case_002"
        )
        self.metadata_store.save_chunk(chunk2)

        # case_001 삭제
        self.metadata_store.delete_case("case_001")

        # case_001 삭제 확인
        files1 = self.metadata_store.get_files_by_case("case_001")
        chunks1 = self.metadata_store.get_chunks_by_case("case_001")
        self.assertEqual(len(files1), 0)
        self.assertEqual(len(chunks1), 0)

        # case_002 보존 확인
        files2 = self.metadata_store.get_files_by_case("case_002")
        chunks2 = self.metadata_store.get_chunks_by_case("case_002")
        self.assertEqual(len(files2), 1)
        self.assertEqual(len(chunks2), 1)
        self.assertEqual(chunks2[0].content, "case_002 content")


class TestCaseIsolationVerification(unittest.TestCase):
    """케이스 격리 검증 테스트"""

    def setUp(self):
        """테스트용 임시 데이터베이스 생성"""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_path = str(Path(self.temp_dir) / "test_chromadb")
        self.vector_store = VectorStore(persist_directory=self.vector_path)

    def tearDown(self):
        """임시 디렉토리 정리"""
        # ChromaDB 클라이언트 명시적으로 닫기 (Windows 파일 잠금 해제)
        if hasattr(self, 'vector_store'):
            del self.vector_store

        import gc
        gc.collect()  # 가비지 컬렉션으로 파일 핸들 해제

        import time
        time.sleep(0.1)  # 짧은 대기로 파일 잠금 해제 보장

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_only_returns_same_case(self):
        """Given: 2개 케이스의 벡터 존재
        When: case_001로 검색
        Then: case_001 결과만 반환"""
        # case_001 벡터
        self.vector_store.add_evidence(
            text="case 001 content",
            embedding=[0.1] * 768,
            metadata={"case_id": "case_001"}
        )

        # case_002 벡터
        self.vector_store.add_evidence(
            text="case 002 content",
            embedding=[0.1] * 768,
            metadata={"case_id": "case_002"}
        )

        # case_001 검색
        results = self.vector_store.search(
            query_embedding=[0.1] * 768,
            n_results=10,
            where={"case_id": "case_001"}
        )

        # 결과 확인
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result["metadata"]["case_id"], "case_001")

    def test_verify_case_isolation(self):
        """Given: 여러 케이스의 벡터
        When: verify_case_isolation(case_id) 호출
        Then: 격리 여부 검증 결과 반환"""
        # 3개 케이스 생성
        for case_id in ["case_A", "case_B", "case_C"]:
            for i in range(3):
                self.vector_store.add_evidence(
                    text=f"{case_id} content {i}",
                    embedding=[float(ord(case_id[-1]) - ord('A')) / 10 + i * 0.01] * 768,
                    metadata={"case_id": case_id}
                )

        # case_A 격리 검증
        is_isolated = self.vector_store.verify_case_isolation("case_A")
        self.assertTrue(is_isolated)

    def test_detect_case_leakage(self):
        """Given: 잘못된 case_id를 가진 벡터 (데이터 누수)
        When: verify_case_isolation() 호출
        Then: False 반환 (격리 실패)"""
        # 정상 벡터
        self.vector_store.add_evidence(
            text="case X content",
            embedding=[0.5] * 768,
            metadata={"case_id": "case_X", "file_id": "file_1"}
        )

        # 잘못된 벡터 (file_id는 case_X인데 metadata에 case_Y)
        # 실제로는 이런 상황이 발생하면 안 됨
        self.vector_store.add_evidence(
            text="leaked content",
            embedding=[0.5] * 768,
            metadata={"case_id": "case_Y", "file_id": "file_1"}  # file_1은 case_X 소속
        )

        # 이 테스트는 VectorStore의 where 필터가 제대로 작동하는지 확인
        results = self.vector_store.search(
            query_embedding=[0.5] * 768,
            n_results=10,
            where={"case_id": "case_X"}
        )

        # case_X 검색 시 case_Y 데이터가 나오면 안 됨
        for result in results:
            self.assertEqual(result["metadata"]["case_id"], "case_X")

    def test_count_by_case(self):
        """Given: 각 케이스별 다른 개수의 벡터
        When: count_by_case(case_id) 호출
        Then: 케이스별 벡터 개수 반환"""
        # case_001: 5개
        for i in range(5):
            self.vector_store.add_evidence(
                text=f"case_001 content {i}",
                embedding=[0.1] * 768,
                metadata={"case_id": "case_001"}
            )

        # case_002: 3개
        for i in range(3):
            self.vector_store.add_evidence(
                text=f"case_002 content {i}",
                embedding=[0.2] * 768,
                metadata={"case_id": "case_002"}
            )

        count1 = self.vector_store.count_by_case("case_001")
        count2 = self.vector_store.count_by_case("case_002")

        self.assertEqual(count1, 5)
        self.assertEqual(count2, 3)


if __name__ == '__main__':
    unittest.main()
