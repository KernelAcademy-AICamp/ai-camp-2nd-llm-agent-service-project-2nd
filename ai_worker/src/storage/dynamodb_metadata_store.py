"""
DynamoDB Metadata Store Module
Production-ready metadata storage using AWS DynamoDB
"""

import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from .schemas import EvidenceFile, EvidenceChunk


class DynamoDBMetadataStore:
    """
    DynamoDB 메타데이터 저장소

    AWS DynamoDB를 사용하여 증거 파일 및 청크의 메타데이터를 관리합니다.
    MetadataStore와 동일한 인터페이스를 제공합니다.
    """

    def __init__(
        self,
        table_name: str = None,
        region_name: str = None
    ):
        """
        DynamoDBMetadataStore 초기화

        Args:
            table_name: DynamoDB 테이블 이름 (기본값: 환경변수)
            region_name: AWS 리전 (기본값: 환경변수)
        """
        self.table_name = table_name or os.getenv(
            "DYNAMODB_TABLE_EVIDENCE_METADATA",
            "leh-evidence-metadata"
        )
        self.region_name = region_name or os.getenv("AWS_REGION", "ap-northeast-2")

        # DynamoDB 클라이언트 생성
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
        self.table = self.dynamodb.Table(self.table_name)

    # ========== Evidence File Operations ==========

    def save_file(self, file: EvidenceFile) -> None:
        """
        증거 파일 저장

        Args:
            file: EvidenceFile 객체
        """
        item = {
            "PK": f"FILE#{file.file_id}",
            "SK": f"META#{file.case_id}",
            "GSI1PK": f"CASE#{file.case_id}",
            "GSI1SK": f"FILE#{file.parsed_at.isoformat()}",
            "file_id": file.file_id,
            "filename": file.filename,
            "file_type": file.file_type,
            "parsed_at": file.parsed_at.isoformat(),
            "total_messages": file.total_messages,
            "case_id": file.case_id,
            "filepath": file.filepath or "",
            "entity_type": "FILE"
        }

        self.table.put_item(Item=item)

    def get_file(self, file_id: str) -> Optional[EvidenceFile]:
        """
        파일 ID로 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceFile 또는 None
        """
        # 파일 ID로만 조회 (GSI 필요할 수 있음)
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"FILE#{file_id}")
        )

        items = response.get("Items", [])
        if not items:
            return None

        item = items[0]
        return self._item_to_evidence_file(item)

    def get_files_by_case(self, case_id: str) -> List[EvidenceFile]:
        """
        케이스 ID로 파일 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceFile 리스트
        """
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CASE#{case_id}") &
                                   Key("GSI1SK").begins_with("FILE#"),
            ScanIndexForward=False  # 최신순 정렬
        )

        files = []
        for item in response.get("Items", []):
            if item.get("entity_type") == "FILE":
                files.append(self._item_to_evidence_file(item))

        return files

    def delete_file(self, file_id: str) -> None:
        """
        파일 삭제

        Args:
            file_id: 삭제할 파일 ID
        """
        # 먼저 파일 정보 조회하여 SK 확인
        file = self.get_file(file_id)
        if file:
            self.table.delete_item(
                Key={
                    "PK": f"FILE#{file_id}",
                    "SK": f"META#{file.case_id}"
                }
            )

    # ========== Evidence Chunk Operations ==========

    def save_chunk(self, chunk: EvidenceChunk) -> None:
        """
        증거 청크 저장

        Args:
            chunk: EvidenceChunk 객체
        """
        item = {
            "PK": f"CHUNK#{chunk.chunk_id}",
            "SK": f"FILE#{chunk.file_id}",
            "GSI1PK": f"CASE#{chunk.case_id}",
            "GSI1SK": f"CHUNK#{chunk.timestamp.isoformat()}",
            "GSI2PK": f"FILE#{chunk.file_id}",
            "GSI2SK": f"CHUNK#{chunk.timestamp.isoformat()}",
            "chunk_id": chunk.chunk_id,
            "file_id": chunk.file_id,
            "content": chunk.content,
            "score": Decimal(str(chunk.score)) if chunk.score else None,
            "timestamp": chunk.timestamp.isoformat(),
            "sender": chunk.sender,
            "vector_id": chunk.vector_id or "",
            "case_id": chunk.case_id,
            "entity_type": "CHUNK"
        }

        # None 값 제거 (DynamoDB는 None을 허용하지 않음)
        item = {k: v for k, v in item.items() if v is not None}

        self.table.put_item(Item=item)

    def save_chunks(self, chunks: List[EvidenceChunk]) -> None:
        """
        여러 청크 일괄 저장

        Args:
            chunks: EvidenceChunk 리스트
        """
        with self.table.batch_writer() as batch:
            for chunk in chunks:
                item = {
                    "PK": f"CHUNK#{chunk.chunk_id}",
                    "SK": f"FILE#{chunk.file_id}",
                    "GSI1PK": f"CASE#{chunk.case_id}",
                    "GSI1SK": f"CHUNK#{chunk.timestamp.isoformat()}",
                    "GSI2PK": f"FILE#{chunk.file_id}",
                    "GSI2SK": f"CHUNK#{chunk.timestamp.isoformat()}",
                    "chunk_id": chunk.chunk_id,
                    "file_id": chunk.file_id,
                    "content": chunk.content,
                    "score": Decimal(str(chunk.score)) if chunk.score else None,
                    "timestamp": chunk.timestamp.isoformat(),
                    "sender": chunk.sender,
                    "vector_id": chunk.vector_id or "",
                    "case_id": chunk.case_id,
                    "entity_type": "CHUNK"
                }
                item = {k: v for k, v in item.items() if v is not None}
                batch.put_item(Item=item)

    def get_chunk(self, chunk_id: str) -> Optional[EvidenceChunk]:
        """
        청크 ID로 조회

        Args:
            chunk_id: 청크 ID

        Returns:
            EvidenceChunk 또는 None
        """
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"CHUNK#{chunk_id}")
        )

        items = response.get("Items", [])
        if not items:
            return None

        return self._item_to_evidence_chunk(items[0])

    def get_chunks_by_file(self, file_id: str) -> List[EvidenceChunk]:
        """
        파일 ID로 청크 목록 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceChunk 리스트
        """
        response = self.table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("GSI2PK").eq(f"FILE#{file_id}") &
                                   Key("GSI2SK").begins_with("CHUNK#")
        )

        chunks = []
        for item in response.get("Items", []):
            if item.get("entity_type") == "CHUNK":
                chunks.append(self._item_to_evidence_chunk(item))

        return chunks

    def get_chunks_by_case(self, case_id: str) -> List[EvidenceChunk]:
        """
        케이스 ID로 청크 목록 조회

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceChunk 리스트
        """
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CASE#{case_id}") &
                                   Key("GSI1SK").begins_with("CHUNK#")
        )

        chunks = []
        for item in response.get("Items", []):
            if item.get("entity_type") == "CHUNK":
                chunks.append(self._item_to_evidence_chunk(item))

        return chunks

    def update_chunk_score(self, chunk_id: str, score: float) -> None:
        """
        청크 점수 업데이트

        Args:
            chunk_id: 청크 ID
            score: 새로운 점수
        """
        # 먼저 청크 조회하여 SK 확인
        chunk = self.get_chunk(chunk_id)
        if chunk:
            self.table.update_item(
                Key={
                    "PK": f"CHUNK#{chunk_id}",
                    "SK": f"FILE#{chunk.file_id}"
                },
                UpdateExpression="SET score = :score",
                ExpressionAttributeValues={
                    ":score": Decimal(str(score))
                }
            )

    def delete_chunk(self, chunk_id: str) -> None:
        """
        청크 삭제

        Args:
            chunk_id: 삭제할 청크 ID
        """
        chunk = self.get_chunk(chunk_id)
        if chunk:
            self.table.delete_item(
                Key={
                    "PK": f"CHUNK#{chunk_id}",
                    "SK": f"FILE#{chunk.file_id}"
                }
            )

    # ========== Statistics & Aggregation ==========

    def count_files_by_case(self, case_id: str) -> int:
        """케이스별 파일 개수"""
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CASE#{case_id}") &
                                   Key("GSI1SK").begins_with("FILE#"),
            Select="COUNT"
        )
        return response.get("Count", 0)

    def count_chunks_by_case(self, case_id: str) -> int:
        """케이스별 청크 개수"""
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CASE#{case_id}") &
                                   Key("GSI1SK").begins_with("CHUNK#"),
            Select="COUNT"
        )
        return response.get("Count", 0)

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
        """get_case_summary 별칭"""
        return self.get_case_summary(case_id)

    # ========== Case Management ==========

    def list_cases(self) -> List[str]:
        """
        전체 케이스 ID 목록 조회

        Returns:
            케이스 ID 리스트 (중복 제거)
        """
        # Scan으로 모든 케이스 ID 추출 (대규모 데이터에서는 비효율적)
        # 프로덕션에서는 별도의 케이스 관리 테이블 권장
        response = self.table.scan(
            FilterExpression="entity_type = :type",
            ExpressionAttributeValues={":type": "FILE"},
            ProjectionExpression="case_id"
        )

        case_ids = set()
        for item in response.get("Items", []):
            case_ids.add(item.get("case_id"))

        return sorted(list(case_ids))

    def delete_case(self, case_id: str) -> None:
        """
        케이스 메타데이터 완전 삭제

        Args:
            case_id: 삭제할 케이스 ID
        """
        # 1. 케이스의 모든 청크 삭제
        chunks = self.get_chunks_by_case(case_id)
        for chunk in chunks:
            self.delete_chunk(chunk.chunk_id)

        # 2. 케이스의 모든 파일 삭제
        files = self.get_files_by_case(case_id)
        for file in files:
            self.delete_file(file.file_id)

    def delete_case_complete(self, case_id: str, vector_store) -> None:
        """
        케이스 완전 삭제 (메타데이터 + 벡터)

        Args:
            case_id: 삭제할 케이스 ID
            vector_store: VectorStore 인스턴스 (벡터 삭제용)
        """
        # 1. 청크의 vector_id 목록 가져오기
        chunks = self.get_chunks_by_case(case_id)
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]

        # 2. 벡터 삭제
        for vector_id in vector_ids:
            try:
                vector_store.delete_by_id(vector_id)
            except Exception:
                pass

        # 3. 메타데이터 삭제
        self.delete_case(case_id)

    # ========== Helper Methods ==========

    def _item_to_evidence_file(self, item: Dict[str, Any]) -> EvidenceFile:
        """DynamoDB 아이템을 EvidenceFile로 변환"""
        return EvidenceFile(
            file_id=item.get("file_id"),
            filename=item.get("filename"),
            file_type=item.get("file_type"),
            parsed_at=datetime.fromisoformat(item.get("parsed_at")),
            total_messages=int(item.get("total_messages", 0)),
            case_id=item.get("case_id"),
            filepath=item.get("filepath") or None
        )

    def _item_to_evidence_chunk(self, item: Dict[str, Any]) -> EvidenceChunk:
        """DynamoDB 아이템을 EvidenceChunk로 변환"""
        score = item.get("score")
        if isinstance(score, Decimal):
            score = float(score)

        return EvidenceChunk(
            chunk_id=item.get("chunk_id"),
            file_id=item.get("file_id"),
            content=item.get("content"),
            score=score,
            timestamp=datetime.fromisoformat(item.get("timestamp")),
            sender=item.get("sender"),
            vector_id=item.get("vector_id") or None,
            case_id=item.get("case_id")
        )
