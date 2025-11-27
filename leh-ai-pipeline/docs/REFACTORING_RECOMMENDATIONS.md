# 리팩토링 및 개선 권장사항

**작성일**: 2025-11-19
**작성자**: Team L (AI/Data)
**목적**: leh-ai-pipeline 개선 및 프로덕션 전환 로드맵

---

## 📋 목차

1. [우선순위 매트릭스](#1-우선순위-매트릭스)
2. [Phase 1: AWS 통합 (최우선)](#2-phase-1-aws-통합-최우선)
3. [Phase 2: 기능 보완](#3-phase-2-기능-보완)
4. [Phase 3: 성능 최적화](#4-phase-3-성능-최적화)
5. [Phase 4: 코드 품질 개선](#5-phase-4-코드-품질-개선)
6. [Phase 5: Backend 통합](#6-phase-5-backend-통합)

---

## 1. 우선순위 매트릭스

| 우선순위 | 작업 | 중요도 | 긴급도 | 예상 기간 | 담당 |
|---------|------|--------|--------|----------|------|
| **P0** | AWS S3 통합 | 🔴 높음 | 🔴 높음 | 3일 | L |
| **P0** | DynamoDB 통합 | 🔴 높음 | 🔴 높음 | 3일 | L |
| **P0** | OpenSearch 통합 | 🔴 높음 | 🔴 높음 | 4일 | L |
| **P0** | Lambda Worker 구성 | 🔴 높음 | 🔴 높음 | 3일 | L, H |
| **P1** | 화자 분리 (Diarization) | 🟡 중간 | 🔴 높음 | 2일 | L |
| **P1** | Soft Delete 구현 | 🟡 중간 | 🟡 중간 | 1일 | L |
| **P1** | 배치 임베딩 | 🟡 중간 | 🟡 중간 | 1일 | L |
| **P2** | 감정 분석 모듈 | 🟡 중간 | 🟢 낮음 | 2일 | L |
| **P2** | 관계 패턴 분석 | 🟡 중간 | 🟢 낮음 | 3일 | L |
| **P2** | 성능 모니터링 | 🟡 중간 | 🟢 낮음 | 2일 | L, H |
| **P3** | 코드 리팩토링 | 🟢 낮음 | 🟢 낮음 | 5일 | L |

---

## 2. Phase 1: AWS 통합 (최우선)

**목표**: 로컬 개발 환경 → AWS 프로덕션 환경 전환
**예상 기간**: 2주
**담당**: Team L + Team H (인프라)

### 2.1 S3 Storage Adapter

**현재 문제**:
```python
# 로컬 파일 시스템 사용
filepath = "./evidence/file.txt"
```

**개선안**:
```python
# storage/s3_adapter.py

import boto3
from typing import BinaryIO, Optional
from pathlib import Path

class S3StorageAdapter:
    """
    S3 저장소 어댑터

    Given: 파일 업로드/다운로드 요청
    When: S3 API 호출
    Then: 결과 반환
    """

    def __init__(self, bucket_name: str, region: str = "ap-northeast-2"):
        """
        초기화

        Args:
            bucket_name: S3 버킷 이름 (예: leh-evidence)
            region: AWS 리전
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)

    def upload_file(
        self,
        file_path: str,
        case_id: str,
        evidence_id: str
    ) -> str:
        """
        S3에 파일 업로드

        Args:
            file_path: 로컬 파일 경로
            case_id: 케이스 ID
            evidence_id: 증거 ID

        Returns:
            str: S3 key (예: cases/case_001/raw/ev_123.txt)
        """
        # S3 key 생성
        file_ext = Path(file_path).suffix
        s3_key = f"cases/{case_id}/raw/{evidence_id}{file_ext}"

        # 업로드
        self.s3_client.upload_file(
            Filename=file_path,
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',  # 암호화
                'Metadata': {
                    'case_id': case_id,
                    'evidence_id': evidence_id
                }
            }
        )

        return s3_key

    def download_file(self, s3_key: str, local_path: str) -> str:
        """
        S3에서 파일 다운로드

        Args:
            s3_key: S3 키
            local_path: 로컬 저장 경로

        Returns:
            str: 다운로드된 파일 경로
        """
        self.s3_client.download_file(
            Bucket=self.bucket_name,
            Key=s3_key,
            Filename=local_path
        )

        return local_path

    def generate_presigned_url(
        self,
        case_id: str,
        evidence_id: str,
        file_ext: str,
        expiration: int = 3600
    ) -> str:
        """
        Presigned URL 생성 (Frontend 업로드용)

        Args:
            case_id: 케이스 ID
            evidence_id: 증거 ID
            file_ext: 파일 확장자 (예: .txt, .jpg)
            expiration: 유효 기간 (초, 기본 1시간)

        Returns:
            str: Presigned URL
        """
        s3_key = f"cases/{case_id}/raw/{evidence_id}{file_ext}"

        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )

        return presigned_url
```

**통합 예시**:
```python
# storage_manager.py 수정

class StorageManager:
    def __init__(
        self,
        s3_adapter: Optional[S3StorageAdapter] = None,
        vector_store: Optional[VectorStore] = None,
        metadata_store: Optional[MetadataStore] = None
    ):
        """
        로컬/프로덕션 환경 자동 전환

        - s3_adapter가 있으면 프로덕션 모드
        - 없으면 로컬 개발 모드
        """
        self.s3_adapter = s3_adapter
        self.local_mode = s3_adapter is None
        # ...

    def process_file(self, filepath: str, case_id: str):
        """파일 처리"""

        # 1. S3에 업로드 (프로덕션 모드)
        if not self.local_mode:
            s3_key = self.s3_adapter.upload_file(
                file_path=filepath,
                case_id=case_id,
                evidence_id=file_meta.file_id
            )
            file_meta.filepath = s3_key  # S3 key 저장
        else:
            file_meta.filepath = filepath  # 로컬 경로 저장

        # 2. 파싱 및 저장 (기존 로직)
        # ...
```

---

### 2.2 DynamoDB Metadata Store

**현재 문제**:
```python
# SQLite 사용 (단일 서버 전용)
metadata_store = MetadataStore(db_path="./data/metadata.db")
```

**개선안**:
```python
# storage/dynamodb_store.py

import boto3
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class DynamoDBMetadataStore:
    """
    DynamoDB 메타데이터 저장소

    Table: leh_evidence
    Partition Key: case_id (String)
    Sort Key: evidence_id (String)
    """

    def __init__(self, table_name: str = "leh_evidence", region: str = "ap-northeast-2"):
        """
        초기화

        Args:
            table_name: DynamoDB 테이블 이름
            region: AWS 리전
        """
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = dynamodb.Table(table_name)

    def insert_file(self, file_meta: EvidenceFile) -> None:
        """
        파일 메타데이터 저장

        Args:
            file_meta: EvidenceFile 객체
        """
        item = {
            'case_id': file_meta.case_id,  # Partition Key
            'evidence_id': f"FILE#{file_meta.file_id}",  # Sort Key
            'type': 'FILE',
            'filename': file_meta.filename,
            'file_type': file_meta.file_type,
            'parsed_at': file_meta.parsed_at.isoformat(),
            'total_messages': file_meta.total_messages,
            'filepath': file_meta.filepath or ""
        }

        self.table.put_item(Item=item)

    def insert_chunk(self, chunk: EvidenceChunk) -> None:
        """
        청크 메타데이터 저장

        Args:
            chunk: EvidenceChunk 객체
        """
        item = {
            'case_id': chunk.case_id,  # Partition Key
            'evidence_id': f"CHUNK#{chunk.chunk_id}",  # Sort Key
            'type': 'CHUNK',
            'file_id': chunk.file_id,
            'content': chunk.content,
            'score': Decimal(str(chunk.score)) if chunk.score else None,
            'timestamp': chunk.timestamp.isoformat(),
            'sender': chunk.sender,
            'vector_id': chunk.vector_id or ""
        }

        self.table.put_item(Item=item)

    def get_chunks_by_case(self, case_id: str) -> List[EvidenceChunk]:
        """
        케이스별 청크 조회

        Args:
            case_id: 케이스 ID

        Returns:
            List[EvidenceChunk]: 청크 리스트
        """
        response = self.table.query(
            KeyConditionExpression='case_id = :case_id AND begins_with(evidence_id, :prefix)',
            ExpressionAttributeValues={
                ':case_id': case_id,
                ':prefix': 'CHUNK#'
            }
        )

        chunks = []
        for item in response['Items']:
            chunk = EvidenceChunk(
                chunk_id=item['evidence_id'].replace('CHUNK#', ''),
                file_id=item['file_id'],
                content=item['content'],
                score=float(item['score']) if item.get('score') else None,
                timestamp=datetime.fromisoformat(item['timestamp']),
                sender=item['sender'],
                vector_id=item.get('vector_id'),
                case_id=item['case_id']
            )
            chunks.append(chunk)

        return chunks

    def delete_case(self, case_id: str, soft_delete: bool = True) -> int:
        """
        케이스 삭제 (Soft Delete 또는 Hard Delete)

        Args:
            case_id: 케이스 ID
            soft_delete: True면 deleted_at 필드 추가, False면 실제 삭제

        Returns:
            int: 삭제된 아이템 수
        """
        if soft_delete:
            # Soft Delete: deleted_at 필드 추가
            deleted_at = datetime.now().isoformat()

            # 케이스의 모든 아이템 조회
            response = self.table.query(
                KeyConditionExpression='case_id = :case_id',
                ExpressionAttributeValues={':case_id': case_id}
            )

            # deleted_at 필드 업데이트
            for item in response['Items']:
                self.table.update_item(
                    Key={
                        'case_id': item['case_id'],
                        'evidence_id': item['evidence_id']
                    },
                    UpdateExpression='SET deleted_at = :deleted_at',
                    ExpressionAttributeValues={':deleted_at': deleted_at}
                )

            return len(response['Items'])

        else:
            # Hard Delete: 실제 삭제
            response = self.table.query(
                KeyConditionExpression='case_id = :case_id',
                ExpressionAttributeValues={':case_id': case_id}
            )

            with self.table.batch_writer() as batch:
                for item in response['Items']:
                    batch.delete_item(
                        Key={
                            'case_id': item['case_id'],
                            'evidence_id': item['evidence_id']
                        }
                    )

            return len(response['Items'])
```

---

### 2.3 OpenSearch Vector Store

**현재 문제**:
```python
# ChromaDB 사용 (로컬 전용)
vector_store = VectorStore(persist_directory="./data/chromadb")
```

**개선안**:
```python
# storage/opensearch_store.py

from opensearchpy import OpenSearch, helpers
from typing import List, Dict, Any, Optional
import numpy as np

class OpenSearchVectorStore:
    """
    OpenSearch 벡터 저장소

    사건별 독립 인덱스: case_rag_{case_id}
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        auth: Optional[tuple] = None
    ):
        """
        초기화

        Args:
            host: OpenSearch 호스트
            port: OpenSearch 포트
            auth: (username, password) 튜플
        """
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True
        )

    def create_case_index(self, case_id: str, dimension: int = 768) -> None:
        """
        사건별 인덱스 생성

        Args:
            case_id: 케이스 ID
            dimension: 임베딩 차원 (기본 768, text-embedding-3-small)
        """
        index_name = f"case_rag_{case_id}"

        # 인덱스 설정
        index_body = {
            'settings': {
                'index': {
                    'knn': True,  # k-NN 활성화
                    'knn.algo_param.ef_search': 100
                }
            },
            'mappings': {
                'properties': {
                    'case_id': {'type': 'keyword'},
                    'evidence_id': {'type': 'keyword'},
                    'content': {'type': 'text'},
                    'timestamp': {'type': 'date'},
                    'sender': {'type': 'keyword'},
                    'vector': {
                        'type': 'knn_vector',
                        'dimension': dimension,
                        'method': {
                            'name': 'hnsw',  # HNSW 알고리즘
                            'space_type': 'cosinesimil',
                            'engine': 'nmslib'
                        }
                    }
                }
            }
        }

        # 인덱스 생성
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=index_body)

    def add(
        self,
        case_id: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        벡터 추가

        Args:
            case_id: 케이스 ID
            documents: 문서 리스트
            embeddings: 임베딩 벡터 리스트
            metadatas: 메타데이터 리스트

        Returns:
            List[str]: 문서 ID 리스트
        """
        index_name = f"case_rag_{case_id}"

        # 인덱스 존재 확인
        if not self.client.indices.exists(index=index_name):
            self.create_case_index(case_id, dimension=len(embeddings[0]))

        # 벡터 추가 (Bulk API)
        actions = []
        doc_ids = []

        for i, (doc, emb, meta) in enumerate(zip(documents, embeddings, metadatas)):
            doc_id = f"{case_id}_{meta.get('evidence_id', i)}"
            doc_ids.append(doc_id)

            action = {
                '_index': index_name,
                '_id': doc_id,
                '_source': {
                    'case_id': case_id,
                    'evidence_id': meta.get('evidence_id'),
                    'content': doc,
                    'timestamp': meta.get('timestamp'),
                    'sender': meta.get('sender'),
                    'vector': emb
                }
            }
            actions.append(action)

        # Bulk Insert
        helpers.bulk(self.client, actions)

        return doc_ids

    def search(
        self,
        case_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        벡터 검색

        Args:
            case_id: 케이스 ID
            query_embedding: 쿼리 임베딩
            top_k: 검색 결과 수

        Returns:
            List[SearchResult]: 검색 결과
        """
        index_name = f"case_rag_{case_id}"

        # k-NN 검색 쿼리
        query = {
            'size': top_k,
            'query': {
                'bool': {
                    'must': [
                        {
                            'knn': {
                                'vector': {
                                    'vector': query_embedding,
                                    'k': top_k
                                }
                            }
                        },
                        {
                            'term': {
                                'case_id': case_id  # case_id 필터링
                            }
                        }
                    ]
                }
            }
        }

        # 검색 실행
        response = self.client.search(index=index_name, body=query)

        # 결과 변환
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            result = SearchResult(
                chunk_id=hit['_id'],
                file_id=source.get('evidence_id', ''),
                content=source['content'],
                distance=1 - hit['_score'],  # Score → Distance 변환
                timestamp=datetime.fromisoformat(source['timestamp']),
                sender=source['sender'],
                case_id=source['case_id'],
                metadata={}
            )
            results.append(result)

        return results

    def delete_case_index(self, case_id: str) -> None:
        """
        사건 인덱스 삭제

        Args:
            case_id: 케이스 ID
        """
        index_name = f"case_rag_{case_id}"

        if self.client.indices.exists(index=index_name):
            self.client.indices.delete(index=index_name)
```

---

### 2.4 Lambda Worker 구성

**목표**: S3 Event → Lambda 자동 실행

**구현**:
```python
# lambda_function.py

import json
import os
import tempfile
from typing import Dict, Any
from src.storage.s3_adapter import S3StorageAdapter
from src.storage.dynamodb_store import DynamoDBMetadataStore
from src.storage.opensearch_store import OpenSearchVectorStore
from src.storage.storage_manager import StorageManager

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Handler (S3 Event Trigger)

    Given: S3 업로드 이벤트
    When: AI 파이프라인 실행
    Then: DynamoDB + OpenSearch에 결과 저장

    Event 구조:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "leh-evidence"},
                "object": {"key": "cases/case_001/raw/ev_123.txt"}
            }
        }]
    }
    """
    try:
        # 1. S3 Event 파싱
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']

        # S3 key에서 case_id, evidence_id 추출
        # 예: cases/case_001/raw/ev_123.txt
        parts = s3_key.split('/')
        case_id = parts[1]  # case_001
        evidence_id = parts[3].split('.')[0]  # ev_123

        # 2. 컴포넌트 초기화
        s3_adapter = S3StorageAdapter(bucket_name=bucket_name)
        metadata_store = DynamoDBMetadataStore()
        vector_store = OpenSearchVectorStore()

        # 3. S3에서 파일 다운로드 (임시 디렉토리)
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, os.path.basename(s3_key))
            s3_adapter.download_file(s3_key=s3_key, local_path=local_path)

            # 4. AI 파이프라인 실행
            manager = StorageManager(
                s3_adapter=s3_adapter,
                metadata_store=metadata_store,
                vector_store=vector_store
            )

            result = manager.process_file(
                filepath=local_path,
                case_id=case_id
            )

        # 5. 성공 응답
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'case_id': case_id,
                'evidence_id': evidence_id,
                'result': result
            })
        }

    except Exception as e:
        # 6. 에러 처리
        print(f"Error processing S3 event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error',
                'error': str(e)
            })
        }
```

**배포 (Terraform)**:
```hcl
# lambda.tf

resource "aws_lambda_function" "ai_worker" {
  function_name = "leh-ai-worker"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300  # 5분
  memory_size   = 2048  # 2GB

  filename         = "lambda_package.zip"
  source_code_hash = filebase64sha256("lambda_package.zip")

  environment {
    variables = {
      OPENAI_API_KEY = var.openai_api_key
      DYNAMODB_TABLE = "leh_evidence"
      OPENSEARCH_HOST = aws_opensearch_domain.leh_rag.endpoint
    }
  }
}

# S3 Event 트리거
resource "aws_s3_bucket_notification" "evidence_upload" {
  bucket = aws_s3_bucket.evidence.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ai_worker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "cases/"
    filter_suffix       = ""
  }
}
```

---

## 3. Phase 2: 기능 보완

### 3.1 화자 분리 (Diarization)

**현재 문제**:
```python
# 모든 세그먼트가 동일한 화자
messages.append(Message(
    sender=default_sender,  # "Speaker"
    # ...
))
```

**개선안 (pyannote.audio 활용)**:
```python
# parsers/audio_parser.py

from pyannote.audio import Pipeline

class AudioParser(BaseParser):
    def __init__(self, enable_diarization: bool = True):
        """
        초기화

        Args:
            enable_diarization: 화자 분리 활성화 여부
        """
        self.enable_diarization = enable_diarization

        if enable_diarization:
            # pyannote/speaker-diarization 모델 로드
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization"
            )

    def parse(
        self,
        file_path: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        오디오 파일 파싱 (화자 분리 포함)

        Returns:
            List[Message]: 화자별 메시지 리스트
        """
        # 1. Whisper STT
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

        # 2. 화자 분리 (선택)
        speaker_map = None
        if self.enable_diarization:
            speaker_map = self._diarize_audio(file_path)

        # 3. 세그먼트별 Message 생성
        messages = []
        for segment in transcript.segments:
            text = segment['text'].strip()
            start_time = segment['start']

            # 화자 식별
            if speaker_map:
                speaker = self._get_speaker_at_time(speaker_map, start_time)
            else:
                speaker = "Speaker"

            # Message 생성
            segment_time = base_timestamp + timedelta(seconds=start_time)
            messages.append(Message(
                content=text,
                sender=speaker,  # ✅ 화자별 구분
                timestamp=segment_time
            ))

        return messages

    def _diarize_audio(self, file_path: str) -> Dict[float, str]:
        """
        화자 분리 실행

        Args:
            file_path: 오디오 파일 경로

        Returns:
            Dict[float, str]: 타임스탬프별 화자 맵
                {0.5: "Speaker1", 3.2: "Speaker2", ...}
        """
        diarization = self.diarization_pipeline(file_path)

        # 타임스탬프별 화자 맵 생성
        speaker_map = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # 각 세그먼트의 시작/끝 시간에 화자 기록
            speaker_map[turn.start] = speaker
            speaker_map[turn.end] = speaker

        return speaker_map

    def _get_speaker_at_time(
        self,
        speaker_map: Dict[float, str],
        time: float
    ) -> str:
        """
        특정 시간의 화자 식별

        Args:
            speaker_map: 타임스탬프별 화자 맵
            time: 조회할 시간 (초)

        Returns:
            str: 화자 ID (예: "Speaker1")
        """
        # time 이전의 가장 가까운 타임스탬프 찾기
        sorted_times = sorted(speaker_map.keys())

        for i, t in enumerate(sorted_times):
            if t > time:
                # 이전 타임스탬프의 화자 반환
                if i > 0:
                    return speaker_map[sorted_times[i - 1]]
                else:
                    return "Unknown"

        # 가장 마지막 화자 반환
        return speaker_map[sorted_times[-1]] if sorted_times else "Unknown"
```

---

### 3.2 Soft Delete 구현

**현재 문제**:
```python
# Hard Delete만 지원
def delete_case(self, case_id: str) -> int:
    """케이스 완전 삭제"""
    # ...
```

**개선안**:
```python
# storage/schemas.py

class EvidenceFile(BaseModel):
    """증거 파일 메타데이터"""
    # 기존 필드...
    deleted_at: Optional[datetime] = None  # ✅ Soft Delete 필드

class EvidenceChunk(BaseModel):
    """증거 청크 메타데이터"""
    # 기존 필드...
    deleted_at: Optional[datetime] = None  # ✅ Soft Delete 필드

# storage/metadata_store.py

class MetadataStore:
    def delete_case(self, case_id: str, soft_delete: bool = True) -> int:
        """
        케이스 삭제

        Args:
            case_id: 케이스 ID
            soft_delete: True면 deleted_at 설정, False면 완전 삭제

        Returns:
            int: 삭제된 레코드 수
        """
        if soft_delete:
            # Soft Delete: deleted_at 필드 업데이트
            cursor = self.conn.cursor()
            deleted_at = datetime.now().isoformat()

            # 파일 Soft Delete
            cursor.execute(
                "UPDATE evidence_files SET deleted_at = ? WHERE case_id = ?",
                (deleted_at, case_id)
            )
            file_count = cursor.rowcount

            # 청크 Soft Delete
            cursor.execute(
                "UPDATE evidence_chunks SET deleted_at = ? WHERE case_id = ?",
                (deleted_at, case_id)
            )
            chunk_count = cursor.rowcount

            self.conn.commit()
            return file_count + chunk_count

        else:
            # Hard Delete: 실제 삭제 (기존 로직)
            return self._hard_delete(case_id)

    def get_chunks_by_case(self, case_id: str, include_deleted: bool = False):
        """
        케이스별 청크 조회

        Args:
            case_id: 케이스 ID
            include_deleted: 삭제된 데이터 포함 여부

        Returns:
            List[EvidenceChunk]: 청크 리스트
        """
        cursor = self.conn.cursor()

        if include_deleted:
            # 삭제된 데이터 포함
            cursor.execute(
                "SELECT * FROM evidence_chunks WHERE case_id = ?",
                (case_id,)
            )
        else:
            # 삭제된 데이터 제외 (기본)
            cursor.execute(
                "SELECT * FROM evidence_chunks WHERE case_id = ? AND deleted_at IS NULL",
                (case_id,)
            )

        # ... (나머지 로직)
```

---

### 3.3 배치 임베딩

**현재 문제**:
```python
# 메시지별 개별 임베딩 생성
for msg in messages:
    embedding = get_embedding(msg.content)  # ❌ 1회 API 호출
    # ...
```

**개선안**:
```python
# storage/storage_manager.py

def get_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    배치 임베딩 생성

    Args:
        texts: 텍스트 리스트
        batch_size: 배치 크기 (최대 100)

    Returns:
        List[List[float]]: 임베딩 리스트
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    all_embeddings = []

    # 배치 단위로 처리
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch  # ✅ 여러 텍스트 한번에 처리
        )

        batch_embeddings = [data.embedding for data in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings

class StorageManager:
    def process_file(self, filepath: str, case_id: str):
        """파일 처리 (배치 임베딩)"""

        # 1. 파싱
        messages = parser.parse(filepath)

        # 2. 배치 임베딩 생성 (✅ 개선)
        contents = [msg.content for msg in messages]
        embeddings = get_embeddings_batch(contents, batch_size=10)

        # 3. 저장
        for msg, embedding in zip(messages, embeddings):
            # VectorStore 저장
            vector_id = self.vector_store.add(
                documents=[msg.content],
                embeddings=[embedding],
                metadatas=[{...}]
            )

            # MetadataStore 저장
            # ...
```

**비용 절감 효과**:
```
현재: 100개 메시지 = 100번 API 호출
개선: 100개 메시지 = 10번 API 호출 (batch_size=10)
→ API 호출 90% 감소
```

---

## 4. Phase 3: 성능 최적화

### 4.1 캐싱 전략

**임베딩 캐싱**:
```python
# storage/embedding_cache.py

import hashlib
import json
from typing import List, Optional

class EmbeddingCache:
    """임베딩 캐시 (Redis)"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def _get_cache_key(self, text: str, model: str) -> str:
        """캐시 키 생성"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{model}:{text_hash}"

    def get(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """캐시에서 임베딩 조회"""
        key = self._get_cache_key(text, model)
        cached = self.redis.get(key)

        if cached:
            return json.loads(cached)
        return None

    def set(self, text: str, embedding: List[float], model: str = "text-embedding-3-small"):
        """캐시에 임베딩 저장 (TTL: 30일)"""
        key = self._get_cache_key(text, model)
        self.redis.setex(
            key,
            2592000,  # 30일
            json.dumps(embedding)
        )

def get_embedding_with_cache(text: str, cache: EmbeddingCache) -> List[float]:
    """캐싱된 임베딩 생성"""

    # 1. 캐시 조회
    cached_embedding = cache.get(text)
    if cached_embedding:
        return cached_embedding

    # 2. API 호출
    embedding = get_embedding(text)

    # 3. 캐시 저장
    cache.set(text, embedding)

    return embedding
```

---

### 4.2 비동기 처리

**현재 문제**:
```python
# 동기 처리
for msg in messages:
    embedding = get_embedding(msg.content)  # 블로킹
```

**개선안 (asyncio)**:
```python
import asyncio
from typing import List
from openai import AsyncOpenAI

async def get_embeddings_async(texts: List[str]) -> List[List[float]]:
    """비동기 임베딩 생성"""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 비동기 태스크 생성
    tasks = []
    for text in texts:
        task = client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        tasks.append(task)

    # 병렬 실행
    responses = await asyncio.gather(*tasks)

    # 임베딩 추출
    embeddings = [response.data[0].embedding for response in responses]
    return embeddings

# 사용
async def main():
    texts = ["텍스트 1", "텍스트 2", "텍스트 3"]
    embeddings = await get_embeddings_async(texts)
```

**성능 개선**:
```
동기 처리: 10개 텍스트 = 10초 (각 1초)
비동기 처리: 10개 텍스트 = ~2초 (병렬 실행)
→ 5배 속도 향상
```

---

## 5. Phase 4: 코드 품질 개선

### 5.1 타입 힌팅 강화

**현재**:
```python
def process_file(self, filepath, case_id):  # ❌ 타입 힌트 없음
    # ...
```

**개선**:
```python
from typing import List, Dict, Any, Optional
from pathlib import Path

def process_file(
    self,
    filepath: str | Path,  # ✅ 타입 힌트
    case_id: str
) -> Dict[str, Any]:  # ✅ 반환 타입
    """파일 처리"""
    # ...
```

---

### 5.2 에러 핸들링 개선

**현재**:
```python
try:
    messages = parser.parse(filepath)
except Exception as e:  # ❌ 너무 광범위
    print(f"Error: {e}")
```

**개선**:
```python
from typing import Union
from custom_exceptions import (
    FileParsingError,
    EmbeddingGenerationError,
    StorageError
)

def process_file(self, filepath: str, case_id: str):
    """파일 처리 (에러 핸들링 개선)"""

    try:
        # 1. 파싱
        messages = parser.parse(filepath)

    except FileNotFoundError as e:
        # 파일 없음 에러
        raise FileParsingError(f"File not found: {filepath}") from e

    except ValueError as e:
        # 파일 형식 오류
        raise FileParsingError(f"Invalid file format: {e}") from e

    try:
        # 2. 임베딩 생성
        embeddings = get_embeddings_batch([msg.content for msg in messages])

    except openai.APIError as e:
        # OpenAI API 에러
        raise EmbeddingGenerationError(f"OpenAI API error: {e}") from e

    try:
        # 3. 저장
        self.vector_store.add(...)
        self.metadata_store.insert_chunks(...)

    except Exception as e:
        # 저장 실패 시 롤백
        self._rollback_file(file_id)
        raise StorageError(f"Storage failed: {e}") from e
```

---

## 6. Phase 5: Backend 통합

### 6.1 FastAPI 엔드포인트

**프로덕션 API 구조**:
```python
# backend/app/api/evidence.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..core.auth import get_current_user
from ..services.evidence_service import EvidenceService
from ..schemas import EvidenceUploadRequest, SearchRequest

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

@router.post("/upload-url")
async def get_upload_url(
    request: EvidenceUploadRequest,
    current_user = Depends(get_current_user)
):
    """
    증거 업로드 Presigned URL 발급

    Given: 파일명, 케이스 ID
    When: S3 Presigned URL 생성
    Then: URL 반환
    """
    service = EvidenceService()

    presigned_url = service.generate_upload_url(
        case_id=request.case_id,
        filename=request.filename,
        user_id=current_user.id
    )

    return {"upload_url": presigned_url}

@router.get("/search")
async def search_evidence(
    request: SearchRequest,
    current_user = Depends(get_current_user)
):
    """
    증거 검색

    Given: 쿼리, 케이스 ID
    When: RAG 검색 실행
    Then: 검색 결과 반환
    """
    service = EvidenceService()

    results = service.search(
        query=request.query,
        case_id=request.case_id,
        top_k=request.top_k,
        include_context=request.include_context
    )

    return results
```

---

## 📊 7. 우선순위별 타임라인

### Week 1-2: P0 (AWS 통합)
- **Day 1-3**: S3 Storage Adapter 구현 + 테스트
- **Day 4-6**: DynamoDB Metadata Store 구현 + 테스트
- **Day 7-10**: OpenSearch Vector Store 구현 + 테스트
- **Day 11-13**: Lambda Worker 구성 + 배포
- **Day 14**: E2E 통합 테스트

### Week 3: P1 (기능 보완)
- **Day 1-2**: 화자 분리 (Diarization) 구현
- **Day 3**: Soft Delete 구현
- **Day 4**: 배치 임베딩 구현
- **Day 5**: 테스트 및 검증

### Week 4: P2 (성능 최적화)
- **Day 1-2**: 캐싱 전략 구현 (Redis)
- **Day 3-4**: 비동기 처리 구현
- **Day 5**: 성능 모니터링 구현

### Week 5-6: Backend 통합
- **Week 5**: FastAPI 엔드포인트 구현 (Team H 협업)
- **Week 6**: Frontend 통합 (Team P 협업)

---

## 📋 8. 체크리스트

### AWS 통합 완료 조건
- [ ] S3 Storage Adapter 구현 완료
- [ ] DynamoDB Metadata Store 구현 완료
- [ ] OpenSearch Vector Store 구현 완료
- [ ] Lambda Worker 구현 완료
- [ ] S3 Event 트리거 설정 완료
- [ ] E2E 테스트 통과 (304 tests → 350+ tests)
- [ ] 프로덕션 배포 성공

### 기능 보완 완료 조건
- [ ] 화자 분리 구현 완료 (pyannote.audio)
- [ ] Soft Delete 구현 완료
- [ ] 배치 임베딩 구현 완료
- [ ] 성능 개선 확인 (API 호출 90% 감소)

### 품질 보증
- [ ] 테스트 커버리지 95%+ 유지
- [ ] 모든 PR 코드 리뷰 통과
- [ ] 문서 업데이트 완료
- [ ] 성능 벤치마크 통과

---

**최종 목표**: 2주 내 AWS 통합 완료, 프로덕션 배포 가능 상태 달성
