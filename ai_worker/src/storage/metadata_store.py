"""
Metadata Store Module - DynamoDB Implementation
Handles evidence metadata storage for AWS Lambda environment

Architecture:
- File/Evidence metadata → DynamoDB (leh_evidence table)
- Chunk metadata → Stored as Qdrant payload (handled by VectorStore)
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from .schemas import EvidenceFile, EvidenceChunk

logger = logging.getLogger(__name__)


class DuplicateError(Exception):
    """Raised when attempting to create a duplicate record."""
    pass


class MetadataStore:
    """
    DynamoDB 메타데이터 저장소

    증거 파일의 메타데이터를 AWS DynamoDB에 저장합니다.
    Lambda 환경에서 영구 저장을 위해 SQLite 대신 DynamoDB 사용.

    Table Schema:
    - Table: leh_evidence (from DDB_EVIDENCE_TABLE env)
    - PK: evidence_id (HASH)
    - GSI: case_id-index (case_id as HASH)
    """

    def __init__(
        self,
        table_name: str = None,
        region: str = None,
        db_path: str = None  # Deprecated: kept for backwards compatibility
    ):
        """
        MetadataStore 초기화

        Args:
            table_name: DynamoDB 테이블명 (기본값: 환경변수 DDB_EVIDENCE_TABLE)
            region: AWS 리전 (기본값: 환경변수 AWS_REGION)
            db_path: Deprecated - ignored (was used for SQLite)
        """
        # Note: db_path is ignored - DynamoDB handles persistence
        if db_path:
            logger.warning(
                "db_path is deprecated and ignored. "
                "MetadataStore now uses DynamoDB."
            )
        self.db_path = db_path  # Keep for test compatibility

        # Use DDB_EVIDENCE_TABLE (unified with Backend), fallback to legacy DYNAMODB_TABLE
        self.table_name = table_name or os.environ.get('DDB_EVIDENCE_TABLE') or os.environ.get('DYNAMODB_TABLE', 'leh_evidence')
        self.region = region or os.environ.get('AWS_REGION', 'ap-northeast-2')
        self._client = None

    @property
    def client(self):
        """Lazy initialization of DynamoDB client"""
        if self._client is None:
            self._client = boto3.client('dynamodb', region_name=self.region)
        return self._client

    # ========== Serialization Helpers ==========

    def _serialize_value(self, value) -> Dict:
        """Convert Python value to DynamoDB type"""
        if value is None:
            return {'NULL': True}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, str):
            return {'S': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, datetime):
            return {'S': value.isoformat()}
        elif isinstance(value, list):
            if not value:
                return {'L': []}
            return {'L': [self._serialize_value(v) for v in value]}
        elif isinstance(value, dict):
            return {'M': {k: self._serialize_value(v) for k, v in value.items()}}
        else:
            return {'S': str(value)}

    def _deserialize_value(self, dynamodb_value: Dict):
        """Convert DynamoDB type to Python value"""
        if 'NULL' in dynamodb_value:
            return None
        elif 'BOOL' in dynamodb_value:
            return dynamodb_value['BOOL']
        elif 'S' in dynamodb_value:
            return dynamodb_value['S']
        elif 'N' in dynamodb_value:
            num_str = dynamodb_value['N']
            return float(num_str) if '.' in num_str else int(num_str)
        elif 'L' in dynamodb_value:
            return [self._deserialize_value(v) for v in dynamodb_value['L']]
        elif 'M' in dynamodb_value:
            return {k: self._deserialize_value(v) for k, v in dynamodb_value['M'].items()}
        elif 'SS' in dynamodb_value:
            return list(dynamodb_value['SS'])
        elif 'NS' in dynamodb_value:
            return [float(n) if '.' in n else int(n) for n in dynamodb_value['NS']]
        else:
            return None

    def _serialize_item(self, data: Dict) -> Dict:
        """Convert Python dict to DynamoDB item format"""
        return {k: self._serialize_value(v) for k, v in data.items()}

    def _deserialize_item(self, item: Dict) -> Dict:
        """Convert DynamoDB item to Python dict"""
        return {k: self._deserialize_value(v) for k, v in item.items()}

    # ========== Evidence File Operations ==========

    def save_file(self, file: EvidenceFile) -> None:
        """
        증거 파일 메타데이터 저장

        Args:
            file: EvidenceFile 객체
        """
        item_data = {
            'evidence_id': file.file_id,  # Use file_id as evidence_id (PK)
            'file_id': file.file_id,
            'filename': file.filename,
            'file_type': file.file_type,
            'parsed_at': file.parsed_at.isoformat(),
            'total_messages': file.total_messages,
            'case_id': file.case_id,
            'filepath': file.filepath,
            'record_type': 'file',  # Distinguish from other record types
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'processed'  # AI Worker completed processing
        }

        try:
            self.client.put_item(
                TableName=self.table_name,
                Item=self._serialize_item(item_data)
            )
            logger.info(f"Saved file metadata: {file.file_id}")
        except ClientError as e:
            logger.error(f"DynamoDB put_item error for file {file.file_id}: {e}")
            raise

    def update_evidence_status(
        self,
        evidence_id: str,
        status: str = "processed",
        ai_summary: Optional[str] = None,
        article_840_tags: Optional[dict] = None,
        qdrant_id: Optional[str] = None,
        case_id: Optional[str] = None,
        filename: Optional[str] = None,
        s3_key: Optional[str] = None,
        file_type: Optional[str] = None,
        content: Optional[str] = None
    ) -> None:
        """
        Backend가 생성한 evidence 레코드의 상태 업데이트 (또는 생성)

        AI Worker가 파일 처리 완료 후 Backend 레코드를 UPDATE합니다.
        Backend보다 AI Worker가 먼저 실행될 수 있으므로, 필수 필드도 함께 저장합니다.
        - status: pending → processed
        - 분석 결과 필드 추가 (ai_summary, article_840_tags, qdrant_id)
        - 필수 필드 추가 (case_id, filename, s3_key) - Backend가 늦게 저장해도 조회 가능

        Args:
            evidence_id: Backend에서 생성한 evidence ID (예: ev_abc123)
            status: 새 상태 (기본값: "processed")
            ai_summary: AI 생성 요약
            article_840_tags: 민법 840조 태그 딕셔너리
            qdrant_id: Qdrant에 저장된 벡터 ID
            case_id: 사건 ID (조회용 GSI 키)
            filename: 원본 파일명
            s3_key: S3 저장 경로
            file_type: 파일 타입 (document, image, audio 등)
            content: 파싱된 원문 텍스트 (STT/OCR 결과)
        """
        update_expression = "SET #status = :status, processed_at = :processed_at"
        expression_names = {"#status": "status"}
        expression_values = {
            ":status": {"S": status},
            ":processed_at": {"S": datetime.now(timezone.utc).isoformat()}
        }

        if ai_summary is not None:
            update_expression += ", ai_summary = :ai_summary"
            expression_values[":ai_summary"] = {"S": ai_summary}

        if article_840_tags is not None:
            update_expression += ", article_840_tags = :tags"
            expression_values[":tags"] = self._serialize_value(article_840_tags)

        if qdrant_id is not None:
            update_expression += ", qdrant_id = :qdrant_id"
            expression_values[":qdrant_id"] = {"S": qdrant_id}

        # 필수 필드들 (Backend보다 먼저 실행될 경우를 대비)
        if case_id is not None:
            update_expression += ", case_id = :case_id"
            expression_values[":case_id"] = {"S": case_id}

        if filename is not None:
            update_expression += ", filename = :filename, original_filename = :original_filename"
            expression_values[":filename"] = {"S": filename}
            expression_values[":original_filename"] = {"S": filename}

        if s3_key is not None:
            update_expression += ", s3_key = :s3_key"
            expression_values[":s3_key"] = {"S": s3_key}

        if file_type is not None:
            update_expression += ", #type = :file_type"
            expression_names["#type"] = "type"
            expression_values[":file_type"] = {"S": file_type}

        if content is not None:
            update_expression += ", content = :content"
            expression_values[":content"] = {"S": content}

        try:
            self.client.update_item(
                TableName=self.table_name,
                Key={"evidence_id": {"S": evidence_id}},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"Updated evidence status: {evidence_id} → {status}")
        except ClientError as e:
            logger.error(f"DynamoDB update_item error for {evidence_id}: {e}")
            raise

    # ========== Idempotency & Duplicate Check Methods ==========

    def check_hash_exists(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a file with the given hash already exists.

        Uses a GSI on file_hash field to efficiently query.
        Falls back to scan if GSI doesn't exist.

        Args:
            file_hash: SHA-256 hash of the file

        Returns:
            Dict with existing evidence info if found, None otherwise
        """
        try:
            # Try GSI first (file_hash-index)
            try:
                response = self.client.query(
                    TableName=self.table_name,
                    IndexName='file_hash-index',
                    KeyConditionExpression='file_hash = :hash',
                    ExpressionAttributeValues={
                        ':hash': {'S': file_hash}
                    },
                    Limit=1
                )
                if response.get('Items'):
                    return self._deserialize_item(response['Items'][0])
            except ClientError as e:
                # GSI might not exist, fall back to scan
                if e.response['Error']['Code'] == 'ValidationException':
                    logger.warning("file_hash-index GSI not found, using scan fallback")
                    response = self.client.scan(
                        TableName=self.table_name,
                        FilterExpression='file_hash = :hash',
                        ExpressionAttributeValues={
                            ':hash': {'S': file_hash}
                        },
                        Limit=1
                    )
                    if response.get('Items'):
                        return self._deserialize_item(response['Items'][0])
                else:
                    raise

            return None

        except ClientError as e:
            logger.error(f"DynamoDB error checking hash {file_hash[:16]}...: {e}")
            return None

    def check_s3_key_exists(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Check if evidence for given S3 key already exists.

        Uses a GSI on s3_key field.

        Args:
            s3_key: S3 object key

        Returns:
            Dict with existing evidence info if found, None otherwise
        """
        try:
            # Try GSI first (s3_key-index)
            try:
                response = self.client.query(
                    TableName=self.table_name,
                    IndexName='s3_key-index',
                    KeyConditionExpression='s3_key = :key',
                    ExpressionAttributeValues={
                        ':key': {'S': s3_key}
                    },
                    Limit=1
                )
                if response.get('Items'):
                    return self._deserialize_item(response['Items'][0])
            except ClientError as e:
                # GSI might not exist, fall back to scan
                if e.response['Error']['Code'] == 'ValidationException':
                    logger.warning("s3_key-index GSI not found, using scan fallback")
                    response = self.client.scan(
                        TableName=self.table_name,
                        FilterExpression='s3_key = :key',
                        ExpressionAttributeValues={
                            ':key': {'S': s3_key}
                        },
                        Limit=1
                    )
                    if response.get('Items'):
                        return self._deserialize_item(response['Items'][0])
                else:
                    raise

            return None

        except ClientError as e:
            logger.error(f"DynamoDB error checking s3_key {s3_key}: {e}")
            return None

    def check_evidence_processed(self, evidence_id: str) -> bool:
        """
        Check if evidence has already been processed.

        Args:
            evidence_id: Evidence ID to check

        Returns:
            True if already processed, False otherwise
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': evidence_id}},
                ProjectionExpression='#status',
                ExpressionAttributeNames={'#status': 'status'}
            )

            item = response.get('Item')
            if item and item.get('status', {}).get('S') == 'processed':
                return True
            return False

        except ClientError as e:
            logger.error(f"DynamoDB error checking evidence {evidence_id}: {e}")
            return False

    def save_file_if_not_exists(
        self,
        file: EvidenceFile,
        file_hash: str
    ) -> bool:
        """
        Save evidence file metadata only if it doesn't already exist.

        Uses DynamoDB conditional write to prevent duplicates.

        Args:
            file: EvidenceFile object
            file_hash: SHA-256 hash of the file

        Returns:
            True if saved, False if already exists

        Raises:
            DuplicateError: If record already exists
        """
        item_data = {
            'evidence_id': file.file_id,
            'file_id': file.file_id,
            'filename': file.filename,
            'file_type': file.file_type,
            'parsed_at': file.parsed_at.isoformat(),
            'total_messages': file.total_messages,
            'case_id': file.case_id,
            'filepath': file.filepath,
            'file_hash': file_hash,  # Add hash for duplicate detection
            'record_type': 'file',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'processed'
        }

        try:
            self.client.put_item(
                TableName=self.table_name,
                Item=self._serialize_item(item_data),
                ConditionExpression='attribute_not_exists(evidence_id)'
            )
            logger.info(f"Saved file metadata: {file.file_id} (hash: {file_hash[:16]}...)")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Evidence {file.file_id} already exists, skipping")
                raise DuplicateError(f"Evidence {file.file_id} already exists")
            logger.error(f"DynamoDB put_item error for file {file.file_id}: {e}")
            raise

    def update_evidence_with_hash(
        self,
        evidence_id: str,
        file_hash: str,
        status: str = "processed",
        ai_summary: Optional[str] = None,
        article_840_tags: Optional[dict] = None,
        qdrant_id: Optional[str] = None,
        case_id: Optional[str] = None,
        filename: Optional[str] = None,
        s3_key: Optional[str] = None,
        file_type: Optional[str] = None,
        content: Optional[str] = None,
        skip_if_processed: bool = True
    ) -> bool:
        """
        Update evidence with hash and processing results.

        Uses conditional write to prevent re-processing if skip_if_processed=True.

        Args:
            evidence_id: Evidence ID
            file_hash: SHA-256 hash of the file
            status: New status
            ai_summary: AI-generated summary
            article_840_tags: Legal tags
            qdrant_id: Qdrant vector ID
            case_id: Case ID
            filename: Original filename
            s3_key: S3 object key
            file_type: File type
            content: Parsed content
            skip_if_processed: If True, don't update if already processed

        Returns:
            True if updated, False if skipped (already processed)
        """
        update_expression = "SET #status = :status, processed_at = :processed_at, file_hash = :hash"
        expression_names = {"#status": "status"}
        expression_values = {
            ":status": {"S": status},
            ":processed_at": {"S": datetime.now(timezone.utc).isoformat()},
            ":hash": {"S": file_hash}
        }

        # Build update expression with optional fields
        if ai_summary is not None:
            update_expression += ", ai_summary = :ai_summary"
            expression_values[":ai_summary"] = {"S": ai_summary}

        if article_840_tags is not None:
            update_expression += ", article_840_tags = :tags"
            expression_values[":tags"] = self._serialize_value(article_840_tags)

        if qdrant_id is not None:
            update_expression += ", qdrant_id = :qdrant_id"
            expression_values[":qdrant_id"] = {"S": qdrant_id}

        if case_id is not None:
            update_expression += ", case_id = :case_id"
            expression_values[":case_id"] = {"S": case_id}

        if filename is not None:
            update_expression += ", filename = :filename, original_filename = :original_filename"
            expression_values[":filename"] = {"S": filename}
            expression_values[":original_filename"] = {"S": filename}

        if s3_key is not None:
            update_expression += ", s3_key = :s3_key"
            expression_values[":s3_key"] = {"S": s3_key}

        if file_type is not None:
            update_expression += ", #type = :file_type"
            expression_names["#type"] = "type"
            expression_values[":file_type"] = {"S": file_type}

        if content is not None:
            update_expression += ", content = :content"
            expression_values[":content"] = {"S": content}

        try:
            update_kwargs = {
                "TableName": self.table_name,
                "Key": {"evidence_id": {"S": evidence_id}},
                "UpdateExpression": update_expression,
                "ExpressionAttributeNames": expression_names,
                "ExpressionAttributeValues": expression_values
            }

            # Add condition to skip if already processed
            if skip_if_processed:
                update_kwargs["ConditionExpression"] = "#status <> :processed_status"
                expression_values[":processed_status"] = {"S": "processed"}

            self.client.update_item(**update_kwargs)
            logger.info(f"Updated evidence: {evidence_id} → {status} (hash: {file_hash[:16]}...)")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.info(f"Evidence {evidence_id} already processed, skipping")
                return False
            logger.error(f"DynamoDB update_item error for {evidence_id}: {e}")
            raise

    def get_file(self, file_id: str) -> Optional[EvidenceFile]:
        """
        파일 ID로 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceFile 또는 None
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': file_id}}
            )

            item = response.get('Item')
            if not item:
                return None

            data = self._deserialize_item(item)
            return EvidenceFile(
                file_id=data.get('file_id', data.get('evidence_id')),
                filename=data.get('filename', ''),
                file_type=data.get('file_type', ''),
                parsed_at=datetime.fromisoformat(data['parsed_at']) if data.get('parsed_at') else datetime.now(),
                total_messages=data.get('total_messages', 0),
                case_id=data.get('case_id', ''),
                filepath=data.get('filepath')
            )
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for file {file_id}: {e}")
            raise

    def get_files_by_case(self, case_id: str) -> List[EvidenceFile]:
        """
        케이스 ID로 파일 목록 조회 (GSI 사용)

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceFile 리스트
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName='case_id-index',
                KeyConditionExpression='case_id = :case_id',
                FilterExpression='record_type = :record_type',
                ExpressionAttributeValues={
                    ':case_id': {'S': case_id},
                    ':record_type': {'S': 'file'}
                }
            )

            files = []
            for item in response.get('Items', []):
                data = self._deserialize_item(item)
                files.append(EvidenceFile(
                    file_id=data.get('file_id', data.get('evidence_id')),
                    filename=data.get('filename', ''),
                    file_type=data.get('file_type', ''),
                    parsed_at=datetime.fromisoformat(data['parsed_at']) if data.get('parsed_at') else datetime.now(),
                    total_messages=data.get('total_messages', 0),
                    case_id=data.get('case_id', ''),
                    filepath=data.get('filepath')
                ))

            # Sort by parsed_at descending
            files.sort(key=lambda x: x.parsed_at, reverse=True)
            return files

        except ClientError as e:
            logger.error(f"DynamoDB query error for case {case_id}: {e}")
            raise

    def delete_file(self, file_id: str) -> None:
        """
        파일 메타데이터 삭제

        Args:
            file_id: 삭제할 파일 ID
        """
        try:
            self.client.delete_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': file_id}}
            )
            logger.info(f"Deleted file metadata: {file_id}")
        except ClientError as e:
            logger.error(f"DynamoDB delete_item error for file {file_id}: {e}")
            raise

    # ========== Evidence Chunk Operations ==========
    # Note: Chunks are primarily stored in Qdrant with metadata as payload.
    # These methods provide backward compatibility but recommend using VectorStore.

    def save_chunk(self, chunk: EvidenceChunk) -> None:
        """
        증거 청크 메타데이터 저장

        Note: 청크는 Qdrant에 벡터와 함께 저장하는 것을 권장합니다.
              이 메서드는 backward compatibility를 위해 유지됩니다.

        Args:
            chunk: EvidenceChunk 객체
        """
        item_data = {
            'evidence_id': f"chunk_{chunk.chunk_id}",  # Prefix to distinguish
            'chunk_id': chunk.chunk_id,
            'file_id': chunk.file_id,
            'content': chunk.content,
            'score': chunk.score,
            'timestamp': chunk.timestamp.isoformat(),
            'sender': chunk.sender,
            'vector_id': chunk.vector_id,
            'case_id': chunk.case_id,
            'record_type': 'chunk',
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        try:
            self.client.put_item(
                TableName=self.table_name,
                Item=self._serialize_item(item_data)
            )
        except ClientError as e:
            logger.error(f"DynamoDB put_item error for chunk {chunk.chunk_id}: {e}")
            raise

    def save_chunks(self, chunks: List[EvidenceChunk]) -> None:
        """
        여러 청크 일괄 저장
        
        Note: BatchWriteItem 권한이 없을 경우 개별 PutItem으로 fallback
        
        Args:
            chunks: EvidenceChunk 리스트
        """
        for chunk in chunks:
            item_data = {
                'evidence_id': f"chunk_{chunk.chunk_id}",
                'chunk_id': chunk.chunk_id,
                'file_id': chunk.file_id,
                'content': chunk.content,
                'score': chunk.score,
                'timestamp': chunk.timestamp.isoformat(),
                'sender': chunk.sender,
                'vector_id': chunk.vector_id,
                'case_id': chunk.case_id,
                'record_type': 'chunk',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            try:
                self.client.put_item(
                    TableName=self.table_name,
                    Item=self._serialize_item(item_data)
                )
            except ClientError as e:
                logger.error(f"DynamoDB put_item error for chunk {chunk.chunk_id}: {e}")
                raise

    def get_chunk(self, chunk_id: str) -> Optional[EvidenceChunk]:
        """
        청크 ID로 조회

        Args:
            chunk_id: 청크 ID

        Returns:
            EvidenceChunk 또는 None
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': f"chunk_{chunk_id}"}}
            )

            item = response.get('Item')
            if not item:
                return None

            data = self._deserialize_item(item)
            return EvidenceChunk(
                chunk_id=data.get('chunk_id'),
                file_id=data.get('file_id'),
                content=data.get('content', ''),
                score=data.get('score'),
                timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
                sender=data.get('sender', ''),
                vector_id=data.get('vector_id'),
                case_id=data.get('case_id', '')
            )
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for chunk {chunk_id}: {e}")
            raise

    def get_chunks_by_file(self, file_id: str) -> List[EvidenceChunk]:
        """
        파일 ID로 청크 목록 조회

        Args:
            file_id: 파일 ID

        Returns:
            EvidenceChunk 리스트
        """
        try:
            # Use scan with filter (not efficient, consider GSI for file_id if needed)
            response = self.client.scan(
                TableName=self.table_name,
                FilterExpression='file_id = :file_id AND record_type = :record_type',
                ExpressionAttributeValues={
                    ':file_id': {'S': file_id},
                    ':record_type': {'S': 'chunk'}
                }
            )

            chunks = []
            for item in response.get('Items', []):
                data = self._deserialize_item(item)
                chunks.append(EvidenceChunk(
                    chunk_id=data.get('chunk_id'),
                    file_id=data.get('file_id'),
                    content=data.get('content', ''),
                    score=data.get('score'),
                    timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
                    sender=data.get('sender', ''),
                    vector_id=data.get('vector_id'),
                    case_id=data.get('case_id', '')
                ))

            # Sort by timestamp
            chunks.sort(key=lambda x: x.timestamp)
            return chunks

        except ClientError as e:
            logger.error(f"DynamoDB scan error for file {file_id}: {e}")
            raise

    def get_chunks_by_case(self, case_id: str) -> List[EvidenceChunk]:
        """
        케이스 ID로 청크 목록 조회 (GSI 사용)

        Args:
            case_id: 케이스 ID

        Returns:
            EvidenceChunk 리스트
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName='case_id-index',
                KeyConditionExpression='case_id = :case_id',
                FilterExpression='record_type = :record_type',
                ExpressionAttributeValues={
                    ':case_id': {'S': case_id},
                    ':record_type': {'S': 'chunk'}
                }
            )

            chunks = []
            for item in response.get('Items', []):
                data = self._deserialize_item(item)
                chunks.append(EvidenceChunk(
                    chunk_id=data.get('chunk_id'),
                    file_id=data.get('file_id'),
                    content=data.get('content', ''),
                    score=data.get('score'),
                    timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
                    sender=data.get('sender', ''),
                    vector_id=data.get('vector_id'),
                    case_id=data.get('case_id', '')
                ))

            # Sort by timestamp
            chunks.sort(key=lambda x: x.timestamp)
            return chunks

        except ClientError as e:
            logger.error(f"DynamoDB query error for case {case_id}: {e}")
            raise

    def update_chunk_score(self, chunk_id: str, score: float) -> None:
        """
        청크 점수 업데이트

        Args:
            chunk_id: 청크 ID
            score: 새로운 점수
        """
        try:
            self.client.update_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': f"chunk_{chunk_id}"}},
                UpdateExpression='SET score = :score',
                ExpressionAttributeValues={':score': {'N': str(score)}}
            )
        except ClientError as e:
            logger.error(f"DynamoDB update_item error for chunk {chunk_id}: {e}")
            raise

    def delete_chunk(self, chunk_id: str) -> None:
        """
        청크 메타데이터 삭제

        Args:
            chunk_id: 삭제할 청크 ID
        """
        try:
            self.client.delete_item(
                TableName=self.table_name,
                Key={'evidence_id': {'S': f"chunk_{chunk_id}"}}
            )
        except ClientError as e:
            logger.error(f"DynamoDB delete_item error for chunk {chunk_id}: {e}")
            raise

    # ========== Statistics & Aggregation ==========

    def count_files_by_case(self, case_id: str) -> int:
        """케이스별 파일 개수"""
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName='case_id-index',
                KeyConditionExpression='case_id = :case_id',
                FilterExpression='record_type = :record_type',
                ExpressionAttributeValues={
                    ':case_id': {'S': case_id},
                    ':record_type': {'S': 'file'}
                },
                Select='COUNT'
            )
            return response.get('Count', 0)
        except ClientError as e:
            logger.error(f"DynamoDB count error for case {case_id}: {e}")
            return 0

    def count_chunks_by_case(self, case_id: str) -> int:
        """케이스별 청크 개수"""
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName='case_id-index',
                KeyConditionExpression='case_id = :case_id',
                FilterExpression='record_type = :record_type',
                ExpressionAttributeValues={
                    ':case_id': {'S': case_id},
                    ':record_type': {'S': 'chunk'}
                },
                Select='COUNT'
            )
            return response.get('Count', 0)
        except ClientError as e:
            logger.error(f"DynamoDB count error for case {case_id}: {e}")
            return 0

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """케이스 요약 정보"""
        return {
            "case_id": case_id,
            "file_count": self.count_files_by_case(case_id),
            "chunk_count": self.count_chunks_by_case(case_id)
        }

    def get_case_stats(self, case_id: str) -> Dict[str, Any]:
        """케이스 통계 정보 (get_case_summary 별칭)"""
        return self.get_case_summary(case_id)

    # ========== Case Management ==========

    def list_cases(self) -> List[str]:
        """
        전체 케이스 ID 목록 조회

        Returns:
            케이스 ID 리스트 (중복 제거)
        """
        try:
            # Scan all items and extract unique case_ids
            response = self.client.scan(
                TableName=self.table_name,
                ProjectionExpression='case_id',
                FilterExpression='record_type = :record_type',
                ExpressionAttributeValues={':record_type': {'S': 'file'}}
            )

            case_ids = set()
            for item in response.get('Items', []):
                if 'case_id' in item:
                    case_ids.add(item['case_id']['S'])

            return sorted(list(case_ids))

        except ClientError as e:
            logger.error(f"DynamoDB scan error for list_cases: {e}")
            return []

    def list_cases_with_stats(self) -> List[Dict[str, Any]]:
        """전체 케이스 ID 목록과 통계 조회"""
        cases = self.list_cases()
        return [self.get_case_stats(case_id) for case_id in cases]

    def delete_case(self, case_id: str) -> None:
        """
        케이스 메타데이터 완전 삭제

        Args:
            case_id: 삭제할 케이스 ID

        Note:
            - 해당 케이스의 모든 파일 및 청크 메타데이터 삭제
            - 벡터는 삭제하지 않음 (delete_case_complete 사용)
        """
        try:
            # Query all items for this case
            response = self.client.query(
                TableName=self.table_name,
                IndexName='case_id-index',
                KeyConditionExpression='case_id = :case_id',
                ExpressionAttributeValues={':case_id': {'S': case_id}},
                ProjectionExpression='evidence_id'
            )

            # Delete each item
            for item in response.get('Items', []):
                evidence_id = item['evidence_id']['S']
                self.client.delete_item(
                    TableName=self.table_name,
                    Key={'evidence_id': {'S': evidence_id}}
                )

            logger.info(f"Deleted all metadata for case: {case_id}")

        except ClientError as e:
            logger.error(f"DynamoDB delete_case error for case {case_id}: {e}")
            raise

    def delete_case_complete(self, case_id: str, vector_store) -> None:
        """
        케이스 완전 삭제 (메타데이터 + 벡터)

        Args:
            case_id: 삭제할 케이스 ID
            vector_store: VectorStore 인스턴스 (벡터 삭제용)
        """
        # 1. Get chunk vector_ids before deleting metadata
        chunks = self.get_chunks_by_case(case_id)
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]

        # 2. Delete vectors from VectorStore
        for vector_id in vector_ids:
            try:
                vector_store.delete_by_id(vector_id)
            except Exception:
                pass  # Ignore if already deleted

        # 3. Delete metadata
        self.delete_case(case_id)
