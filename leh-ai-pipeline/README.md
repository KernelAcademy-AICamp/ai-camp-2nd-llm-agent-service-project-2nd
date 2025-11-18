# LEH AI Pipeline

**Legal Evidence Hub - AI Pipeline Implementation**

이혼 소송 변호사를 위한 AI 파트너 솔루션의 AI 파이프라인 구현체입니다.

## 프로젝트 개요

카카오톡 대화, 텍스트 문서, 이미지 등 다양한 증거 자료를 파싱하고 분석하여 법률적 인사이트를 제공하는 RAG 시스템입니다.

### 핵심 기능

- **증거 파싱**: KakaoTalk, 텍스트, 이미지 OCR 지원
- **벡터 검색**: ChromaDB 기반 의미론적 검색
- **증거 분석**: 법률 키워드 기반 점수화 + 리스크 분석
- **하이브리드 RAG**: 증거 검색 + 법률 지식베이스 통합 검색
- **메타데이터 관리**: SQLite 기반 구조화된 정보 저장

### 개발 원칙

- **TDD 기반**: 203개 테스트 (93% 커버리지)
- **로컬 우선**: AWS 통합 전 완전한 로컬 동작 검증
- **모듈화**: 각 컴포넌트 독립적 테스트 가능

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│              입력 계층 (Parsers)                     │
├─────────────────────────────────────────────────────┤
│  KakaoTalkParser  │  TextParser  │  ImageOCRParser  │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│           저장소 계층 (Storage)                      │
├─────────────────────────────────────────────────────┤
│  VectorStore (ChromaDB)  │  MetadataStore (SQLite)  │
│         StorageManager (통합 관리)                   │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│           분석 계층 (Analysis)                       │
├─────────────────────────────────────────────────────┤
│  EvidenceScorer  │  RiskAnalyzer  │  AnalysisEngine │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│              RAG 계층                                │
├─────────────────────────────────────────────────────┤
│  Service RAG (법률 지식)  │  User RAG (증거 검색)   │
│         HybridSearchEngine (통합 검색)               │
└─────────────────────────────────────────────────────┘
```

## 기술 스택

- **Python**: 3.11+
- **Vector DB**: ChromaDB (로컬)
- **Metadata DB**: SQLite
- **Embedding**: OpenAI text-embedding-3-small (768 dim)
- **OCR**: Tesseract + Pillow
- **Testing**: pytest + pytest-cov
- **Validation**: Pydantic

## 디렉토리 구조

```
leh-ai-pipeline/
├── src/
│   ├── parsers/              # 파일 파싱
│   │   ├── base.py           # BaseParser, Message
│   │   ├── kakaotalk.py      # 카카오톡 대화 파싱
│   │   ├── text.py           # 텍스트 문서 파싱
│   │   └── image_ocr.py      # 이미지 OCR
│   ├── storage/              # 데이터 저장 및 검색
│   │   ├── vector_store.py   # ChromaDB 벡터 저장
│   │   ├── metadata_store.py # SQLite 메타데이터
│   │   ├── storage_manager.py # 통합 관리
│   │   ├── search_engine.py  # 증거 검색
│   │   └── schemas.py        # 데이터 스키마
│   ├── analysis/             # 증거 분석
│   │   ├── evidence_scorer.py # 증거 점수화
│   │   ├── risk_analyzer.py   # 리스크 분석
│   │   └── analysis_engine.py # 통합 분석
│   ├── service_rag/          # 법률 지식베이스 RAG
│   │   ├── legal_parser.py    # 법령/판례 파싱
│   │   ├── legal_vectorizer.py # 법률 지식 벡터화
│   │   ├── legal_search.py    # 법률 지식 검색
│   │   └── schemas.py         # 법률 데이터 스키마
│   └── user_rag/             # 사용자 증거 RAG
│       └── hybrid_search.py  # 하이브리드 검색
├── tests/                    # 테스트 (203개, 93% 커버리지)
│   ├── fixtures/             # 테스트 데이터
│   ├── test_parsers.py
│   ├── test_schemas.py
│   ├── test_vector_store.py
│   ├── test_metadata_store.py
│   ├── test_image_ocr.py
│   └── test_integration_e2e.py
├── data/                     # 로컬 데이터 (gitignore)
│   ├── vectors/              # ChromaDB 저장소
│   └── metadata.db           # SQLite DB
├── requirements.txt
├── pytest.ini
└── README.md
```

## 설치 및 실행

### 1. 환경 설정

```bash
# Python 3.11+ 필요
python --version

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
OPENAI_API_KEY=your-api-key-here
```

### 3. 테스트 실행

```bash
# 전체 테스트 (203개)
pytest

# 커버리지 리포트
pytest --cov=src --cov-report=html

# 특정 모듈 테스트
pytest tests/test_parsers.py -v
pytest tests/test_integration_e2e.py -v

# 실패한 테스트만 재실행
pytest --lf -x
```

## 모듈 레퍼런스

### 1. Parsers (파싱 계층)

#### KakaoTalkParser
카카오톡 대화 내역 파싱

```python
from src.parsers.kakaotalk import KakaoTalkParser
from datetime import datetime

parser = KakaoTalkParser()

# 표준 형식
messages = parser.parse(
    """2024.01.15. 오후 2:30, 홍길동 : 이혼 상담 부탁드립니다
    2024.01.15. 오후 2:35, 변호사 : 네, 상담 가능합니다"""
)

# iOS 형식
messages = parser.parse(
    """[홍길동] [오후 2:30] 이혼 상담 부탁드립니다
    [변호사] [오후 2:35] 네, 상담 가능합니다"""
)

# 결과: List[Message]
for msg in messages:
    print(f"{msg.sender}: {msg.content} ({msg.timestamp})")
```

#### TextParser
일반 텍스트 문서 파싱

```python
from src.parsers.text import TextParser

parser = TextParser()
messages = parser.parse(
    file_path="evidence.txt",
    default_sender="의뢰인"
)
# 빈 줄 기준으로 메시지 분리
```

#### ImageOCRParser
이미지에서 텍스트 추출 (Tesseract OCR)

```python
from src.parsers.image_ocr import ImageOCRParser
from datetime import datetime

parser = ImageOCRParser()
messages = parser.parse(
    file_path="screenshot.png",
    default_sender="상담자",
    default_timestamp=datetime.now()
)
# 한글+영어 인식, 줄 단위로 메시지 생성
```

### 2. Storage (저장 계층)

#### StorageManager
증거 파일 저장 및 관리

```python
from src.storage.storage_manager import StorageManager

# 초기화
storage = StorageManager(
    vector_db_path="./data/vectors",
    metadata_db_path="./data/metadata.db"
)

# 증거 파일 저장 (자동 파싱 + 벡터화)
result = storage.process_file(
    file_path="kakaotalk.txt",
    file_type="kakaotalk",
    case_id="case_001",
    original_filename="대화내역_2024.txt"
)

# 결과
print(f"파일 ID: {result['file_id']}")
print(f"청크 수: {result['chunks_created']}")
```

#### SearchEngine
증거 검색

```python
from src.storage.search_engine import SearchEngine

search = SearchEngine(storage)

# 의미론적 검색
results = search.search(
    query="폭행 증거",
    case_id="case_001",
    top_k=5
)

for result in results:
    print(f"내용: {result.content}")
    print(f"유사도: {1 - result.distance:.2f}")
    print(f"발신자: {result.sender}")
```

### 3. Analysis (분석 계층)

#### AnalysisEngine
통합 증거 분석

```python
from src.analysis.analysis_engine import AnalysisEngine

analyzer = AnalysisEngine()

# 케이스 분석
result = analyzer.analyze_case(
    messages=messages,
    case_id="case_001",
    high_value_threshold=6.0
)

# 결과
print(f"총 메시지: {result.total_messages}")
print(f"평균 점수: {result.average_score}")
print(f"고가치 메시지: {len(result.high_value_messages)}개")
print(f"리스크 레벨: {result.risk_assessment.risk_level}")

# 고가치 메시지
for msg in result.high_value_messages:
    print(f"[{msg.score}점] {msg.message.content}")
```

#### EvidenceScorer
증거 점수화 (키워드 기반)

```python
from src.analysis.evidence_scorer import EvidenceScorer

scorer = EvidenceScorer()

# 단일 메시지 점수
score_result = scorer.score(message)
print(f"점수: {score_result.score}")
print(f"매칭 키워드: {score_result.matched_keywords}")

# 배치 점수화
results = scorer.score_batch(messages)
```

#### RiskAnalyzer
리스크 분석 (패턴 탐지)

```python
from src.analysis.risk_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer()

# 리스크 평가
risk = analyzer.analyze(messages)
print(f"리스크 레벨: {risk.risk_level}")  # LOW/MEDIUM/HIGH/CRITICAL
print(f"리스크 요인: {risk.risk_factors}")
print(f"경고사항: {risk.warnings}")
print(f"권장사항: {risk.recommendations}")
```

### 4. Service RAG (법률 지식베이스)

#### LegalVectorizer
법률 지식 벡터화

```python
from src.service_rag.legal_parser import StatuteParser
from src.service_rag.legal_vectorizer import LegalVectorizer
from src.service_rag.schemas import Statute

# 법령 파싱
parser = StatuteParser()
statute = parser.parse(
    text="민법 제840조(이혼원인) ① 부부의 일방은...",
    statute_id="s001",
    metadata={"category": "가족법"}
)

# 벡터화 및 저장
vectorizer = LegalVectorizer(
    collection_name="legal_knowledge",
    persist_directory="./data/legal_vectors"
)
chunk_id = vectorizer.vectorize_statute(statute)

# 판례도 동일하게 처리 가능
```

#### LegalSearchEngine
법률 지식 검색

```python
from src.service_rag.legal_search import LegalSearchEngine

search = LegalSearchEngine(
    collection_name="legal_knowledge"
)

# 법률 지식 검색
results = search.search(
    query="이혼 원인",
    top_k=5
)

for result in results:
    print(f"유형: {result.doc_type}")  # statute or case_law
    print(f"내용: {result.content}")
    print(f"유사도: {1 - result.distance:.2f}")
```

### 5. User RAG (하이브리드 검색)

#### HybridSearchEngine
증거 + 법률 지식 통합 검색

```python
from src.user_rag.hybrid_search import HybridSearchEngine

# 초기화
hybrid = HybridSearchEngine(
    storage_manager=storage,
    evidence_collection="leh_evidence",
    legal_collection="legal_knowledge"
)

# 하이브리드 검색
results = hybrid.search(
    query="폭행 증거의 법적 효력",
    case_id="case_001",
    top_k=10,
    search_evidence=True,   # 증거 검색
    search_legal=True       # 법률 지식 검색
)

# 결과 분류
for result in results:
    if result.source == "evidence":
        print(f"[증거] {result.content}")
    else:
        print(f"[법률] {result.result_type}: {result.content}")
    print(f"관련도: {result.relevance_score:.2f}\n")
```

## FastAPI 통합 가이드

### 1. 기본 엔드포인트 예시

```python
from fastapi import FastAPI, UploadFile, HTTPException
from src.storage.storage_manager import StorageManager
from src.analysis.analysis_engine import AnalysisEngine
from src.user_rag.hybrid_search import HybridSearchEngine

app = FastAPI()

# 싱글톤 초기화
storage = StorageManager(
    vector_db_path="./data/vectors",
    metadata_db_path="./data/metadata.db"
)
analyzer = AnalysisEngine()
hybrid_search = HybridSearchEngine(storage_manager=storage)

@app.post("/evidence/upload")
async def upload_evidence(
    file: UploadFile,
    case_id: str,
    file_type: str  # "kakaotalk" | "text" | "image"
):
    """증거 파일 업로드 및 처리"""
    try:
        # 파일 저장
        content = await file.read()
        temp_path = f"./temp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)

        # 파싱 및 저장
        result = storage.process_file(
            file_path=temp_path,
            file_type=file_type,
            case_id=case_id,
            original_filename=file.filename
        )

        return {
            "file_id": result["file_id"],
            "chunks_created": result["chunks_created"],
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evidence/analyze")
async def analyze_evidence(case_id: str):
    """케이스 분석"""
    try:
        # 증거 조회
        messages = storage.get_messages_by_case(case_id)

        # 분석
        result = analyzer.analyze_case(
            messages=messages,
            case_id=case_id
        )

        return {
            "total_messages": result.total_messages,
            "average_score": result.average_score,
            "high_value_count": len(result.high_value_messages),
            "risk_level": result.risk_assessment.risk_level.value,
            "risk_factors": result.risk_assessment.risk_factors,
            "warnings": result.risk_assessment.warnings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def hybrid_search_endpoint(
    query: str,
    case_id: str,
    top_k: int = 10
):
    """하이브리드 검색"""
    try:
        results = hybrid_search.search(
            query=query,
            case_id=case_id,
            top_k=top_k
        )

        return {
            "query": query,
            "results": [
                {
                    "source": r.source,
                    "type": r.result_type,
                    "content": r.content,
                    "relevance": r.relevance_score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 에러 핸들링

```python
from fastapi import HTTPException
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "File not found"}
    )
```

## 테스트 현황

### 전체 통계
- **총 테스트**: 203개
- **커버리지**: ~93%
- **TDD 방식**: RED-GREEN-REFACTOR 사이클 준수

### 모듈별 테스트

| 모듈 | 테스트 파일 | 테스트 수 | 커버리지 |
|------|------------|----------|---------|
| Parsers | test_parsers.py | 40 | 100% |
| Storage | test_vector_store.py, test_metadata_store.py | 60 | 95% |
| Analysis | test_analysis.py | 50 | 100% |
| Service RAG | test_legal_*.py | 33 | 98% |
| User RAG | test_hybrid_search.py | 10 | 100% |
| Image OCR | test_image_ocr.py | 14 | 100% |
| Integration | test_integration_e2e.py | 9 | N/A |

### E2E 통합 테스트

`tests/test_integration_e2e.py` 포함:
- 증거 처리 전체 플로우 (파싱→저장→분석→검색)
- 법률 지식 처리 플로우 (파싱→벡터화→검색)
- 하이브리드 검색 플로우
- 컴포넌트간 통합 검증
- 데이터 생명주기 검증
- 시스템 준비 상태 검증

## 개발 로드맵

- ✅ **Week 1**: 파싱 기반 구축 (KakaoTalk, Text)
- ✅ **Week 2**: 로컬 저장소 (ChromaDB + SQLite)
- ✅ **Week 3**: 분석 엔진 (증거 점수, 리스크 분석)
- ✅ **Week 4**: Service RAG (법률 지식 베이스)
- ✅ **Week 5**: User RAG (케이스별 증거 검색)
- ✅ **Week 6**: 이미지 OCR + 전체 통합
- ✅ **Week 7**: 테스트 + 문서화 + 백엔드 핸드오프

## 백엔드 핸드오프 체크리스트

✅ 모든 모듈 100% 작동 검증 (203 테스트 통과)
✅ 로컬 환경 완전 동작 (ChromaDB + SQLite)
✅ API 레퍼런스 문서화
✅ FastAPI 통합 가이드 제공
⏳ AWS 마이그레이션 가이드 (백엔드 팀 협업)

## 다음 단계 (백엔드 팀)

1. **FastAPI 서버 구현**
   - `/evidence/upload`, `/evidence/analyze`, `/search/hybrid` 엔드포인트
   - 파일 업로드 핸들링
   - 에러 핸들링 및 로깅

2. **AWS 마이그레이션**
   - ChromaDB → AWS OpenSearch or Pinecone
   - SQLite → AWS RDS PostgreSQL
   - S3 파일 저장 통합

3. **인증/권한**
   - 케이스 소유권 검증
   - 변호사-의뢰인 접근 제어

4. **성능 최적화**
   - 배치 처리 큐 (Celery)
   - 캐싱 전략 (Redis)
   - 비동기 임베딩 처리

## 라이선스

Private - AI Camp 2nd Project
