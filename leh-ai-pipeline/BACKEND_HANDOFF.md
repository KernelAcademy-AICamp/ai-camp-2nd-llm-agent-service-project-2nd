# Backend Handoff Guide

**LEH AI Pipeline → Backend Team Integration Guide**

## 핸드오프 개요

AI 파이프라인의 모든 기능이 로컬 환경에서 완전히 검증되었습니다 (203 테스트, 93% 커버리지).
이 가이드는 백엔드 팀이 파이프라인을 FastAPI 서버로 통합하고 AWS로 마이그레이션하는 과정을 안내합니다.

## 검증 완료 사항

### ✅ 완료된 컴포넌트

1. **파싱 시스템** (leh-ai-pipeline/src/parsers)
   - KakaoTalkParser: 카카오톡 대화 파싱 (표준/iOS 형식)
   - TextParser: 일반 텍스트 문서 파싱
   - ImageOCRParser: 이미지 OCR (Tesseract)
   - 모든 파서는 `List[Message]` 반환, BaseParser 인터페이스 준수

2. **저장소 시스템** (leh-ai-pipeline/src/storage)
   - VectorStore: ChromaDB 기반 벡터 저장 (OpenAI embeddings)
   - MetadataStore: SQLite 기반 메타데이터 관리
   - StorageManager: 파일 처리 통합 관리 (파싱→임베딩→저장)
   - SearchEngine: 의미론적 검색 + 메타데이터 필터링

3. **분석 시스템** (leh-ai-pipeline/src/analysis)
   - EvidenceScorer: 법률 키워드 기반 증거 점수화
   - RiskAnalyzer: 패턴 기반 리스크 탐지 (LOW/MEDIUM/HIGH/CRITICAL)
   - AnalysisEngine: 통합 분석 인터페이스

4. **RAG 시스템** (leh-ai-pipeline/src/service_rag, src/user_rag)
   - Service RAG: 법률 지식베이스 (법령/판례)
   - User RAG: 케이스별 증거 검색
   - HybridSearchEngine: 증거 + 법률 지식 통합 검색

### ✅ 테스트 검증

- **총 203개 테스트**, 93% 커버리지
- **E2E 통합 테스트** 9개 통과
- 모든 컴포넌트 독립적 테스트 가능
- TDD 방식으로 개발 (RED-GREEN-REFACTOR)

## Phase 1: FastAPI 서버 구축 (1-2주)

### 1.1 프로젝트 구조 제안

```
backend/
├── app/
│   ├── main.py                  # FastAPI 앱
│   ├── config.py                # 설정
│   ├── dependencies.py          # 의존성 주입
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── evidence.py     # 증거 관련 엔드포인트
│   │   │   ├── analysis.py     # 분석 엔드포인트
│   │   │   └── search.py       # 검색 엔드포인트
│   ├── models/                  # Pydantic 모델
│   │   ├── requests.py
│   │   └── responses.py
│   └── services/                # 비즈니스 로직
│       ├── evidence_service.py
│       ├── analysis_service.py
│       └── search_service.py
├── leh-ai-pipeline/             # AI 파이프라인 (서브모듈)
│   └── src/
└── tests/
```

### 1.2 FastAPI 서버 초기 설정

**app/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import evidence, analysis, search
from app.dependencies import get_storage_manager

app = FastAPI(
    title="LEH Backend API",
    version="1.0.0",
    description="Legal Evidence Hub Backend API"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션: 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    # StorageManager 초기화 등
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    # DB 연결 종료 등
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**app/dependencies.py**
```python
from functools import lru_cache
from leh_ai_pipeline.src.storage.storage_manager import StorageManager
from leh_ai_pipeline.src.analysis.analysis_engine import AnalysisEngine
from leh_ai_pipeline.src.user_rag.hybrid_search import HybridSearchEngine

@lru_cache()
def get_storage_manager():
    """StorageManager 싱글톤"""
    return StorageManager(
        vector_db_path="./data/vectors",
        metadata_db_path="./data/metadata.db"
    )

@lru_cache()
def get_analysis_engine():
    """AnalysisEngine 싱글톤"""
    return AnalysisEngine()

@lru_cache()
def get_hybrid_search():
    """HybridSearchEngine 싱글톤"""
    storage = get_storage_manager()
    return HybridSearchEngine(storage_manager=storage)
```

### 1.3 핵심 엔드포인트 구현

**app/api/v1/evidence.py**
```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.dependencies import get_storage_manager
from app.models.requests import EvidenceUploadRequest
from app.models.responses import EvidenceUploadResponse
from leh_ai_pipeline.src.storage.storage_manager import StorageManager
import tempfile
import os

router = APIRouter()

@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str,
    file_type: str,  # "kakaotalk" | "text" | "image"
    storage: StorageManager = Depends(get_storage_manager)
):
    """
    증거 파일 업로드

    Given: 파일 업로드
    When: 파싱 및 벡터 저장 실행
    Then: file_id와 생성된 청크 수 반환
    """
    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # AI 파이프라인 실행
            result = storage.process_file(
                file_path=tmp_path,
                file_type=file_type,
                case_id=case_id,
                original_filename=file.filename
            )

            return EvidenceUploadResponse(
                file_id=result["file_id"],
                chunks_created=result["chunks_created"],
                status="success"
            )

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/files/{case_id}")
async def list_case_files(
    case_id: str,
    storage: StorageManager = Depends(get_storage_manager)
):
    """케이스의 모든 증거 파일 조회"""
    try:
        files = storage.metadata_store.get_files_by_case(case_id)
        return {"case_id": case_id, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**app/api/v1/analysis.py**
```python
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_storage_manager, get_analysis_engine
from app.models.responses import AnalysisResponse
from leh_ai_pipeline.src.storage.storage_manager import StorageManager
from leh_ai_pipeline.src.analysis.analysis_engine import AnalysisEngine

router = APIRouter()

@router.post("/analyze/{case_id}", response_model=AnalysisResponse)
async def analyze_case(
    case_id: str,
    high_value_threshold: float = 6.0,
    storage: StorageManager = Depends(get_storage_manager),
    analyzer: AnalysisEngine = Depends(get_analysis_engine)
):
    """
    케이스 분석

    Given: case_id
    When: 모든 증거 메시지 분석 실행
    Then: 점수, 리스크, 고가치 메시지 반환
    """
    try:
        # 케이스의 모든 메시지 조회
        chunks = storage.metadata_store.get_chunks_by_case(case_id)

        if not chunks:
            raise HTTPException(status_code=404, detail="No evidence found for this case")

        # Message 객체로 변환
        from leh_ai_pipeline.src.parsers.base import Message
        messages = [
            Message(
                content=chunk["content"],
                sender=chunk.get("sender", "Unknown"),
                timestamp=chunk.get("timestamp")
            )
            for chunk in chunks
        ]

        # 분석 실행
        result = analyzer.analyze_case(
            messages=messages,
            case_id=case_id,
            high_value_threshold=high_value_threshold
        )

        return AnalysisResponse(
            case_id=case_id,
            total_messages=result.total_messages,
            average_score=result.average_score,
            high_value_count=len(result.high_value_messages),
            high_value_messages=[
                {
                    "content": msg.message.content,
                    "sender": msg.message.sender,
                    "score": msg.score,
                    "matched_keywords": msg.matched_keywords
                }
                for msg in result.high_value_messages
            ],
            risk_level=result.risk_assessment.risk_level.value,
            risk_factors=result.risk_assessment.risk_factors,
            warnings=result.risk_assessment.warnings,
            recommendations=result.risk_assessment.recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**app/api/v1/search.py**
```python
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_hybrid_search
from app.models.requests import SearchRequest
from app.models.responses import SearchResponse
from leh_ai_pipeline.src.user_rag.hybrid_search import HybridSearchEngine

router = APIRouter()

@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    search_engine: HybridSearchEngine = Depends(get_hybrid_search)
):
    """
    하이브리드 검색 (증거 + 법률 지식)

    Given: 검색 쿼리
    When: 증거 검색 + 법률 지식 검색 실행
    Then: 통합 결과 반환 (관련도 순)
    """
    try:
        results = search_engine.search(
            query=request.query,
            case_id=request.case_id,
            top_k=request.top_k,
            search_evidence=request.search_evidence,
            search_legal=request.search_legal
        )

        return SearchResponse(
            query=request.query,
            case_id=request.case_id,
            results=[
                {
                    "source": r.source,
                    "result_type": r.result_type,
                    "content": r.content,
                    "relevance_score": r.relevance_score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 1.4 Pydantic 모델

**app/models/requests.py**
```python
from pydantic import BaseModel, Field
from typing import Optional

class EvidenceUploadRequest(BaseModel):
    case_id: str = Field(..., description="케이스 ID")
    file_type: str = Field(..., description="파일 타입: kakaotalk, text, image")

class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    case_id: str = Field(..., description="케이스 ID")
    top_k: int = Field(10, description="반환할 결과 수")
    search_evidence: bool = Field(True, description="증거 검색 여부")
    search_legal: bool = Field(True, description="법률 지식 검색 여부")
```

**app/models/responses.py**
```python
from pydantic import BaseModel
from typing import List, Dict, Any

class EvidenceUploadResponse(BaseModel):
    file_id: str
    chunks_created: int
    status: str

class AnalysisResponse(BaseModel):
    case_id: str
    total_messages: int
    average_score: float
    high_value_count: int
    high_value_messages: List[Dict[str, Any]]
    risk_level: str
    risk_factors: List[str]
    warnings: List[str]
    recommendations: List[str]

class SearchResponse(BaseModel):
    query: str
    case_id: str
    results: List[Dict[str, Any]]
```

### 1.5 테스트

```bash
# FastAPI 서버 실행
uvicorn app.main:app --reload --port 8000

# 테스트
curl -X POST "http://localhost:8000/api/v1/evidence/upload" \
  -F "file=@test.txt" \
  -F "case_id=case_001" \
  -F "file_type=text"
```

## Phase 2: AWS 마이그레이션 (2-3주)

### 2.1 저장소 마이그레이션

#### ChromaDB → AWS OpenSearch / Pinecone

**현재 (로컬):**
```python
VectorStore(
    collection_name="leh_evidence",
    persist_directory="./data/vectors"
)
```

**마이그레이션 후:**
```python
# 옵션 1: AWS OpenSearch
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

client = OpenSearch(
    hosts=[{'host': 'your-domain.region.es.amazonaws.com', 'port': 443}],
    http_auth=AWS4Auth(...),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# 옵션 2: Pinecone (추천 - 관리형 서비스)
import pinecone
pinecone.init(api_key="...", environment="us-west1-gcp")
index = pinecone.Index("leh-evidence")
```

**마이그레이션 스크립트:**
```python
# scripts/migrate_to_pinecone.py
import pinecone
from leh_ai_pipeline.src.storage.vector_store import VectorStore

# 로컬 ChromaDB에서 데이터 읽기
local_store = VectorStore(collection_name="leh_evidence")
results = local_store.collection.get(include=["embeddings", "metadatas", "documents"])

# Pinecone에 업로드
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index("leh-evidence")

for i, (id, embedding, metadata, document) in enumerate(zip(
    results["ids"],
    results["embeddings"],
    results["metadatas"],
    results["documents"]
)):
    index.upsert([(id, embedding, {**metadata, "content": document})])
```

#### SQLite → AWS RDS PostgreSQL

**현재 (로컬):**
```python
MetadataStore(db_path="./data/metadata.db")
```

**마이그레이션 후:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "postgresql://user:password@your-rds-endpoint:5432/leh_db"
)
Session = sessionmaker(bind=engine)
```

**마이그레이션 스크립트:**
```python
# scripts/migrate_to_postgres.py
import sqlite3
import psycopg2

# SQLite 연결
sqlite_conn = sqlite3.connect("./data/metadata.db")
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL 연결
pg_conn = psycopg2.connect(
    host="your-rds-endpoint",
    database="leh_db",
    user="user",
    password="password"
)
pg_cursor = pg_conn.cursor()

# 테이블 생성 (leh-ai-pipeline/src/storage/metadata_store.py의 스키마 사용)
# ...

# 데이터 마이그레이션
sqlite_cursor.execute("SELECT * FROM evidence_files")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute("INSERT INTO evidence_files VALUES (%s, %s, ...)", row)

pg_conn.commit()
```

### 2.2 파일 저장소 마이그레이션

**S3 통합:**
```python
import boto3
from fastapi import UploadFile

s3_client = boto3.client('s3')

@router.post("/upload")
async def upload_evidence(file: UploadFile, case_id: str, file_type: str):
    # S3에 원본 파일 저장
    s3_key = f"cases/{case_id}/evidence/{file.filename}"
    s3_client.upload_fileobj(file.file, "leh-evidence-bucket", s3_key)

    # 임시 다운로드하여 파싱
    tmp_path = f"/tmp/{file.filename}"
    s3_client.download_file("leh-evidence-bucket", s3_key, tmp_path)

    # 기존 파이프라인 실행
    result = storage.process_file(
        file_path=tmp_path,
        file_type=file_type,
        case_id=case_id,
        original_filename=file.filename
    )

    return result
```

### 2.3 환경 설정

**config.py**
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str = "us-west1-gcp"

    # RDS PostgreSQL
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # S3
    s3_bucket_name: str = "leh-evidence-bucket"

    # Redis (캐싱)
    redis_host: str
    redis_port: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()
```

## Phase 3: 인증 및 권한 (1-2주)

### 3.1 케이스 접근 제어

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_case_access(
    case_id: str,
    token: str = Depends(oauth2_scheme)
):
    """케이스 접근 권한 검증"""
    user = decode_token(token)

    # 케이스 소유자 확인
    case_owner = get_case_owner(case_id)

    if user.id != case_owner.lawyer_id and user.id != case_owner.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this case"
        )

    return user

@router.post("/analyze/{case_id}")
async def analyze_case(
    case_id: str,
    user = Depends(verify_case_access)  # 권한 체크
):
    # ...
```

## Phase 4: 성능 최적화 (2주)

### 4.1 비동기 처리

**Celery 태스크:**
```python
# tasks.py
from celery import Celery

celery_app = Celery('leh', broker='redis://localhost:6379/0')

@celery_app.task
def process_file_async(file_path: str, file_type: str, case_id: str):
    """파일 처리를 백그라운드에서 실행"""
    storage = get_storage_manager()
    result = storage.process_file(
        file_path=file_path,
        file_type=file_type,
        case_id=case_id
    )
    return result

# 사용
@router.post("/upload")
async def upload_evidence(file: UploadFile, case_id: str, file_type: str):
    # S3 업로드
    s3_key = upload_to_s3(file, case_id)

    # 비동기 처리 시작
    task = process_file_async.delay(s3_key, file_type, case_id)

    return {
        "task_id": task.id,
        "status": "processing"
    }

@router.get("/upload/status/{task_id}")
async def check_upload_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

### 4.2 캐싱 전략

**Redis 캐싱:**
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@router.post("/search/hybrid")
async def hybrid_search(request: SearchRequest):
    # 캐시 키 생성
    cache_key = f"search:{request.case_id}:{request.query}:{request.top_k}"

    # 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 검색 실행
    results = search_engine.search(...)

    # 캐시 저장 (5분 TTL)
    redis_client.setex(cache_key, 300, json.dumps(results))

    return results
```

## Phase 5: 모니터링 및 로깅

### 5.1 로깅

```python
import logging
from logging.handlers import RotatingFileHandler

# 로깅 설정
logger = logging.getLogger("leh")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler("leh.log", maxBytes=10485760, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# 사용
@router.post("/upload")
async def upload_evidence(...):
    logger.info(f"Upload started: case_id={case_id}, file={file.filename}")
    try:
        result = storage.process_file(...)
        logger.info(f"Upload success: file_id={result['file_id']}")
        return result
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise
```

### 5.2 메트릭 수집

```python
from prometheus_client import Counter, Histogram
import time

# 메트릭 정의
upload_counter = Counter('leh_uploads_total', 'Total uploads')
upload_duration = Histogram('leh_upload_duration_seconds', 'Upload duration')

@router.post("/upload")
async def upload_evidence(...):
    start_time = time.time()

    try:
        result = storage.process_file(...)
        upload_counter.inc()
        return result
    finally:
        upload_duration.observe(time.time() - start_time)
```

## 체크리스트

### Phase 1: FastAPI 서버 (1-2주)
- [ ] FastAPI 프로젝트 구조 생성
- [ ] 의존성 주입 설정
- [ ] 증거 업로드 엔드포인트
- [ ] 분석 엔드포인트
- [ ] 검색 엔드포인트
- [ ] 에러 핸들링
- [ ] API 문서 (Swagger)
- [ ] 통합 테스트

### Phase 2: AWS 마이그레이션 (2-3주)
- [ ] Pinecone/OpenSearch 설정
- [ ] RDS PostgreSQL 설정
- [ ] S3 버킷 설정
- [ ] ChromaDB → Pinecone 마이그레이션 스크립트
- [ ] SQLite → PostgreSQL 마이그레이션 스크립트
- [ ] 환경 변수 설정
- [ ] 마이그레이션 테스트

### Phase 3: 인증/권한 (1-2주)
- [ ] JWT 토큰 인증
- [ ] 케이스 소유권 검증
- [ ] 변호사-의뢰인 접근 제어
- [ ] RBAC (Role-Based Access Control)

### Phase 4: 성능 최적화 (2주)
- [ ] Celery 설정
- [ ] 비동기 파일 처리
- [ ] Redis 캐싱
- [ ] 임베딩 배치 처리
- [ ] DB 쿼리 최적화

### Phase 5: 모니터링 (1주)
- [ ] 로깅 시스템
- [ ] Prometheus 메트릭
- [ ] CloudWatch 통합
- [ ] 알림 설정 (Slack, PagerDuty)

## 예상 타임라인

- **Week 1-2**: FastAPI 서버 구축 (Phase 1)
- **Week 3-5**: AWS 마이그레이션 (Phase 2)
- **Week 6-7**: 인증/권한 (Phase 3)
- **Week 8-9**: 성능 최적화 (Phase 4)
- **Week 10**: 모니터링 및 최종 테스트 (Phase 5)

**총 예상 기간**: 10주 (2.5개월)

## 문의 및 지원

AI 파이프라인 관련 질문:
- 코드 이해: `leh-ai-pipeline/README.md` 참조
- 테스트: `pytest leh-ai-pipeline/tests/` 실행하여 검증
- 아키텍처: `leh-ai-pipeline/README.md`의 "시스템 아키텍처" 섹션

## 핸드오프 완료 기준

✅ 백엔드 팀이 다음 작업을 완료하면 핸드오프 성공:
1. FastAPI 서버에서 `/evidence/upload` 엔드포인트 동작
2. 로컬 환경에서 end-to-end 테스트 통과
3. AWS 환경에서 기본 파이프라인 동작 검증

---

**핸드오프 완료일**: TBD
**AI 파이프라인 버전**: v1.0.0
**백엔드 팀 담당자**: TBD
