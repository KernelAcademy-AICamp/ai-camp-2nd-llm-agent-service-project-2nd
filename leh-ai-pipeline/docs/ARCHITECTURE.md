# LEH AI Pipeline - 시스템 아키텍처

이혼 소송 증거 관리 시스템의 상세 아키텍처 문서

---

## 목차

- [시스템 개요](#시스템-개요)
- [레이어 구조](#레이어-구조)
- [데이터 흐름](#데이터-흐름)
- [모듈별 상세 설명](#모듈별-상세-설명)
- [케이스 격리 아키텍처](#케이스-격리-아키텍처)
- [성능 및 확장성](#성능-및-확장성)

---

## 시스템 개요

### 아키텍처 패턴

LEH AI Pipeline은 **레이어드 아키텍처 (Layered Architecture)** 패턴을 기반으로 설계되었습니다.

```
┌─────────────────────────────────────────────────┐
│          Application Layer (API)                │
│  (향후 FastAPI/Flask 통합 예정)                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Service Layer (Business Logic)          │
│  - StorageManager                               │
│  - AnalysisEngine                               │
│  - HybridSearch                                 │
└─────────────────────────────────────────────────┘
                      ↓
┌──────────────┬──────────────┬───────────────────┐
│  Parsers     │  Analysis    │  Search           │
│  (입력 처리)  │  (분석 엔진)  │  (검색 엔진)        │
└──────────────┴──────────────┴───────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Data Layer (Storage)                    │
│  - MetadataStore (SQLite)                       │
│  - VectorStore (ChromaDB)                       │
│  - LegalVectorStore (법률 지식)                  │
└─────────────────────────────────────────────────┘
```

### 핵심 설계 원칙

1. **모듈화 (Modularity)**: 각 기능을 독립적인 모듈로 분리
2. **확장성 (Scalability)**: 새로운 파서/분석기 추가 용이
3. **격리성 (Isolation)**: 케이스별 데이터 완전 격리
4. **테스트 가능성 (Testability)**: Mock 기반 유닛 테스트 (94% 커버리지)
5. **의존성 역전 (Dependency Inversion)**: 추상화 기반 인터페이스

---

## 레이어 구조

### 1. Presentation Layer (향후)

현재는 CLI/SDK 형태로 제공되며, 향후 FastAPI 기반 REST API로 확장 예정.

```python
# 향후 API 엔드포인트 예시
POST /api/v1/cases/{case_id}/files
GET  /api/v1/cases/{case_id}/search
POST /api/v1/cases/{case_id}/analyze
```

### 2. Service Layer

#### StorageManager
**역할**: 파일 처리 및 저장 통합 관리

```python
class StorageManager:
    """
    파서 + VectorStore + MetadataStore 통합
    """
    def process_file(filepath: str, case_id: str) -> Dict
    def search(query: str, case_id: str, top_k: int) -> List[Dict]
    def get_case_summary(case_id: str) -> Dict
```

**책임**:
- 파일 타입 자동 감지
- 적절한 파서 선택
- 임베딩 생성 (OpenAI API)
- 메타데이터 + 벡터 동시 저장
- 에러 시 롤백 처리

#### AnalysisEngine
**역할**: 증거 분석 통합 관리

```python
class AnalysisEngine:
    """
    Scorer + RiskAnalyzer + Article840Tagger 통합
    """
    def analyze(messages: List[Message]) -> AnalysisResult
    def get_high_value_messages(messages: List[Message]) -> List[Message]
    def get_summary(messages: List[Message]) -> Dict
```

**책임**:
- 증거 점수 산정
- 위험도 평가
- 법률 조항 태깅
- 통계 요약 생성

#### HybridSearchEngine
**역할**: 사용자 증거 + 법률 지식 통합 검색

```python
class HybridSearchEngine:
    """
    User RAG + Legal RAG 통합
    """
    def search(query: str, case_id: str, top_k: int) -> List[HybridResult]
```

### 3. Domain Layer

#### Parsers (7개)

모든 파서는 `BaseParser` 추상 클래스를 상속합니다.

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Message]:
        """파일 → 메시지 리스트 변환"""
        pass
```

**파서별 특징**:

| 파서 | 입력 | 출력 | 외부 API |
|------|------|------|----------|
| KakaoTalkParser | `.txt` | List[Message] | - |
| PDFParser | `.pdf` | List[Message] | - |
| TextParser | `.txt` | List[Message] | - |
| ImageOCRParser | `.jpg/.png` | List[Message] | Tesseract |
| ImageVisionParser | `.jpg/.png` | VisionAnalysis | GPT-4o Vision |
| AudioParser | `.mp3/.wav` | List[Message] | Whisper STT |
| VideoParser | `.mp4/.avi` | List[Message] | ffmpeg + Whisper |

**데이터 모델**:

```python
@dataclass
class Message:
    content: str                    # 메시지 내용
    sender: str                     # 발신자
    timestamp: datetime             # 발신 시간
```

#### Analysis Modules (4개)

**EvidenceScorer**:
```python
class EvidenceScorer:
    def score(message: Message) -> ScoringResult
    def score_batch(messages: List[Message]) -> List[ScoringResult]

@dataclass
class ScoringResult:
    score: float                    # 0-10점
    matched_keywords: List[str]     # 매칭된 키워드
    categories: List[str]           # 관련 카테고리
```

**RiskAnalyzer**:
```python
class RiskAnalyzer:
    def analyze(messages: List[Message]) -> RiskAnalysis

@dataclass
class RiskAnalysis:
    violence_risk: RiskLevel        # low/medium/high/critical
    financial_risk: RiskLevel
    custody_risk: RiskLevel
    overall_risk: RiskLevel
    risk_indicators: List[str]      # 위험 지표 목록
```

**Article840Tagger**:
```python
class Article840Tagger:
    def tag(message: Message) -> TaggingResult
    def tag_batch(messages: List[Message]) -> List[TaggingResult]

class Article840Category(Enum):
    ADULTERY = "adultery"                      # 제1호: 배우자 부정행위
    DESERTION = "desertion"                    # 제2호: 악의의 유기
    MISTREATMENT_BY_INLAWS = "mistreatment_by_inlaws"  # 제3호
    HARM_TO_OWN_PARENTS = "harm_to_own_parents"        # 제4호
    UNKNOWN_WHEREABOUTS = "unknown_whereabouts"        # 제5호
    IRRECONCILABLE_DIFFERENCES = "irreconcilable_differences"  # 제6호
    GENERAL = "general"
```

**EvidenceSummarizer**:
```python
class EvidenceSummarizer:
    def summarize_conversation(messages: List[Message]) -> SummaryResult
    def summarize_document(text: str) -> SummaryResult
    def summarize_evidence(messages: List[Message]) -> SummaryResult

@dataclass
class SummaryResult:
    summary: str                    # 요약문
    summary_type: SummaryType       # conversation/document/evidence
    key_points: List[str]           # 핵심 포인트
    word_count: int                 # 단어 수
```

### 4. Data Layer

#### MetadataStore (SQLite)

**스키마**:

```sql
CREATE TABLE evidence_files (
    file_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    parsed_at TEXT NOT NULL,
    total_messages INTEGER NOT NULL,
    case_id TEXT NOT NULL,
    filepath TEXT
);

CREATE TABLE evidence_chunks (
    chunk_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    content TEXT NOT NULL,
    score REAL,
    timestamp TEXT NOT NULL,
    sender TEXT NOT NULL,
    vector_id TEXT,
    case_id TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES evidence_files(file_id)
);

-- 인덱스 (성능 최적화)
CREATE INDEX idx_files_case_id ON evidence_files(case_id);
CREATE INDEX idx_chunks_file_id ON evidence_chunks(file_id);
CREATE INDEX idx_chunks_case_id ON evidence_chunks(case_id);
```

**주요 메서드**:

```python
class MetadataStore:
    # 파일 관리
    def save_file(file: EvidenceFile) -> None
    def get_file(file_id: str) -> Optional[EvidenceFile]
    def get_files_by_case(case_id: str) -> List[EvidenceFile]
    def delete_file(file_id: str) -> None

    # 청크 관리
    def save_chunk(chunk: EvidenceChunk) -> None
    def save_chunks(chunks: List[EvidenceChunk]) -> None
    def get_chunk(chunk_id: str) -> Optional[EvidenceChunk]
    def get_chunks_by_file(file_id: str) -> List[EvidenceChunk]
    def get_chunks_by_case(case_id: str) -> List[EvidenceChunk]

    # 케이스 관리
    def list_cases() -> List[str]
    def list_cases_with_stats() -> List[Dict]
    def delete_case(case_id: str) -> None
    def delete_case_complete(case_id: str, vector_store) -> None
```

#### VectorStore (ChromaDB)

**컬렉션 설정**:

```python
collection_name = "leh_evidence"
embedding_model = "text-embedding-3-small"  # 768 dimensions
similarity_metric = "cosine"
```

**메타데이터 구조**:

```python
metadata = {
    "chunk_id": str,        # 청크 ID
    "file_id": str,         # 파일 ID
    "case_id": str,         # 케이스 ID (격리용)
    "sender": str,          # 발신자
    # ... 추가 메타데이터
}
```

**주요 메서드**:

```python
class VectorStore:
    # 벡터 추가
    def add_evidence(text: str, embedding: List[float], metadata: Dict) -> str
    def add_evidences(texts: List[str], embeddings: List[List[float]], metadatas: List[Dict]) -> List[str]

    # 검색
    def search(query_embedding: List[float], n_results: int, where: Optional[Dict]) -> List[Dict]

    # 관리
    def get_by_id(vector_id: str) -> Optional[Dict]
    def delete_by_id(vector_id: str) -> None
    def count() -> int

    # 케이스 격리
    def count_by_case(case_id: str) -> int
    def delete_by_case(case_id: str) -> int
    def verify_case_isolation(case_id: str) -> bool
```

---

## 데이터 흐름

### 1. 파일 업로드 → 저장

```
┌─────────────┐
│  파일 업로드 │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ StorageManager       │
│ - detect_file_type() │  1️⃣ 파일 타입 자동 감지
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ Parser 선택          │
│ - KakaoTalk/PDF/etc  │  2️⃣ 적절한 파서 선택
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ 파싱                 │
│ - parse(file_path)   │  3️⃣ 파일 → List[Message]
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ 파일 메타데이터 생성  │
│ - EvidenceFile       │  4️⃣ 파일 정보 생성
│ - MetadataStore.save │
└──────┬───────────────┘
       │
       ↓
┌────────────────────────────────┐
│  각 메시지 처리 (Loop)          │
├────────────────────────────────┤
│  5️⃣ 청크 메타데이터 생성        │
│     - EvidenceChunk            │
│                                │
│  6️⃣ 임베딩 생성                │
│     - OpenAI Embedding API     │
│     - 768차원 벡터              │
│                                │
│  7️⃣ 벡터 저장                  │
│     - VectorStore.add_evidence │
│     - metadata에 case_id 포함  │
│                                │
│  8️⃣ 메타데이터 저장            │
│     - MetadataStore.save_chunk │
│     - vector_id 연결           │
└────────────────────────────────┘
       │
       ↓
┌──────────────────────┐
│  결과 반환           │
│  - file_id           │
│  - total_messages    │
│  - chunks_stored     │
└──────────────────────┘
```

### 2. 검색 플로우

```
┌─────────────┐
│  검색 쿼리   │
│  + case_id  │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ StorageManager.search│  1️⃣ 검색 요청
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ 쿼리 임베딩 생성      │  2️⃣ OpenAI Embedding API
│ - get_embedding()    │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ VectorStore.search   │  3️⃣ 벡터 검색
│ - where: {case_id}   │     (케이스 필터링)
│ - n_results: top_k   │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ 결과 포맷팅           │  4️⃣ 검색 결과 반환
│ - content            │
│ - metadata           │
│ - distance (유사도)  │
└──────────────────────┘
```

### 3. 분석 플로우

```
┌──────────────────┐
│ List[Message]    │
└────────┬─────────┘
         │
         ↓
┌────────────────────────────┐
│ AnalysisEngine.analyze()   │  1️⃣ 분석 시작
└────────┬───────────────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         ↓                                  ↓
┌─────────────────┐              ┌──────────────────┐
│ EvidenceScorer  │  2️⃣ 점수 산정│  RiskAnalyzer    │  3️⃣ 위험도 분석
│ - score_batch() │              │  - analyze()     │
└────────┬────────┘              └────────┬─────────┘
         │                                │
         └──────────┬─────────────────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │ Article840Tagger     │  4️⃣ 법률 조항 태깅
         │ - tag_batch()        │
         └──────────┬───────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │ AnalysisResult       │  5️⃣ 통합 결과 반환
         │ - scored_messages    │
         │ - risk_analysis      │
         │ - tagged_messages    │
         │ - summary            │
         └──────────────────────┘
```

---

## 케이스 격리 아키텍처

### 설계 목표

1. **완전 격리**: 케이스 A의 사용자가 케이스 B 데이터에 절대 접근 불가
2. **성능 최적화**: 인덱싱을 통한 빠른 케이스별 조회
3. **데이터 무결성**: 케이스 삭제 시 모든 관련 데이터 완전 제거

### 격리 메커니즘

#### 1. case_id 기반 분할

모든 데이터는 `case_id`를 필수 속성으로 가집니다.

```python
# MetadataStore
EvidenceFile(
    file_id="...",
    case_id="case_001",  # ← 케이스 식별자
    # ...
)

EvidenceChunk(
    chunk_id="...",
    case_id="case_001",  # ← 동일 케이스
    # ...
)

# VectorStore
metadata = {
    "case_id": "case_001",  # ← 벡터에도 케이스 ID 포함
    # ...
}
```

#### 2. 데이터베이스 인덱싱

```sql
-- 케이스별 빠른 조회를 위한 인덱스
CREATE INDEX idx_files_case_id ON evidence_files(case_id);
CREATE INDEX idx_chunks_case_id ON evidence_chunks(case_id);
```

#### 3. 검색 시 필터링

```python
# VectorStore 검색 시 반드시 case_id 필터 적용
results = vector_store.search(
    query_embedding=embedding,
    n_results=10,
    where={"case_id": case_id}  # ← 필터링
)

# MetadataStore 조회도 case_id로 제한
chunks = metadata_store.get_chunks_by_case(case_id)
```

#### 4. 케이스 격리 검증

```python
# 격리 검증 메서드
is_isolated = vector_store.verify_case_isolation(case_id)

# 검증 로직:
# 1. case_id로 모든 벡터 조회
# 2. 각 벡터의 metadata.case_id가 요청한 case_id와 일치하는지 확인
# 3. 하나라도 불일치 시 False 반환 (데이터 누수 감지)
```

#### 5. 케이스 완전 삭제

```python
# 1단계: MetadataStore 삭제
metadata_store.delete_case(case_id)
# → evidence_chunks WHERE case_id = ?
# → evidence_files WHERE case_id = ?

# 2단계: VectorStore 삭제
vector_store.delete_by_case(case_id)
# → collection.delete(where={"case_id": case_id})

# 통합 메서드
metadata_store.delete_case_complete(case_id, vector_store)
```

### 격리 테스트

```python
# 테스트 시나리오
def test_case_isolation():
    # Given: 2개 케이스 존재
    store.process_file("file1.txt", case_id="case_A")
    store.process_file("file2.txt", case_id="case_B")

    # When: case_A 검색
    results = store.search("query", case_id="case_A")

    # Then: case_A 결과만 반환
    assert all(r["metadata"]["case_id"] == "case_A" for r in results)
```

---

## 성능 및 확장성

### 성능 최적화

#### 1. 벡터 검색 최적화
- **HNSW 인덱스**: ChromaDB의 계층적 탐색 가능한 작은 세계 그래프
- **Cosine 유사도**: 빠른 유사도 계산
- **배치 처리**: `add_evidences()`로 여러 벡터 동시 추가

#### 2. 데이터베이스 인덱싱
- `case_id`, `file_id` 인덱스로 조회 성능 향상
- 외래 키 제약으로 데이터 무결성 보장

#### 3. 임베딩 캐싱 (향후)
- 동일 텍스트 재임베딩 방지
- Redis 기반 캐시 계층 추가 예정

### 확장성 전략

#### 1. 수평 확장 (Horizontal Scaling)

```
현재 (단일 인스턴스):
┌──────────────────┐
│  Application     │
│  ↓               │
│  StorageManager  │
│  ↓               │
│  SQLite + Chroma │
└──────────────────┘

향후 (분산 시스템):
┌──────────┐  ┌──────────┐  ┌──────────┐
│  App 1   │  │  App 2   │  │  App 3   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   ↓
         ┌─────────────────┐
         │  Load Balancer  │
         └────────┬─────────┘
                  │
      ┌───────────┼───────────┐
      ↓           ↓           ↓
 ┌─────────┐ ┌─────────┐ ┌─────────┐
 │ Postgres│ │  Qdrant │ │  Redis  │
 │ (Meta)  │ │ (Vector)│ │ (Cache) │
 └─────────┘ └─────────┘ └─────────┘
```

#### 2. 모듈 독립 배포

각 모듈을 독립 서비스로 분리 가능:

- **Parser Service**: 파일 파싱 전담
- **Embedding Service**: 임베딩 생성 전담
- **Search Service**: 검색 전담
- **Analysis Service**: 분석 전담

#### 3. 벡터 DB 확장

- **현재**: ChromaDB (로컬)
- **향후**: Qdrant, Pinecone, Weaviate 등으로 교체 가능
- **인터페이스 추상화**: `VectorStore` 추상 클래스로 교체 용이

### 병목 현상 및 해결책

| 병목 현상 | 원인 | 해결책 |
|----------|------|--------|
| 임베딩 생성 느림 | OpenAI API 호출 | 배치 처리, 비동기 처리 |
| 대용량 파일 처리 | 동기 파싱 | 청크 단위 스트리밍 처리 |
| 검색 결과 느림 | 벡터 크기 증가 | HNSW 인덱스 최적화, 필터링 |
| 케이스 많을 때 조회 느림 | 전체 스캔 | 인덱싱 강화, 파티셔닝 |

---

## 보안 고려사항

### 1. 데이터 격리
- **케이스별 완전 격리**: 다른 케이스 데이터 접근 불가
- **격리 검증**: `verify_case_isolation()` 메서드로 주기적 검증

### 2. API 키 관리
- **환경변수**: `.env` 파일로 API 키 관리
- **향후**: Vault, AWS Secrets Manager 통합

### 3. 데이터 암호화
- **현재**: 파일 시스템 수준 암호화
- **향후**: 데이터베이스 암호화 (SQLCipher), 벡터 암호화

### 4. 접근 제어
- **현재**: case_id 기반 격리
- **향후**: RBAC (Role-Based Access Control), JWT 인증

---

## 향후 개선 사항

### 1. 실시간 처리
- WebSocket 기반 실시간 파일 처리 상태 알림
- 스트리밍 파싱 (대용량 파일)

### 2. 고급 분석
- 시간대별 증거 타임라인 생성
- 관계망 분석 (인물 관계도)
- 감정 분석 트렌드

### 3. 다국어 지원
- 영어, 중국어 등 다국어 증거 처리
- 다국어 임베딩 모델 (multilingual-e5)

### 4. UI/UX
- FastAPI + React 웹 인터페이스
- 증거 시각화 대시보드
- 드래그 앤 드롭 파일 업로드

---

## 참고 자료

- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Whisper STT](https://openai.com/research/whisper)
- [민법 제840조 (이혼 원인)](https://www.law.go.kr/)
