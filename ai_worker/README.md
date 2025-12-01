# LEH AI Worker

**Legal Evidence Hub - AI Processing Pipeline**

AWS Lambda 기반 AI Worker로, S3에 업로드된 증거 파일을 자동으로 파싱·분석·임베딩하여 구조화된 데이터로 변환합니다.

---

## 📋 개요

### 목적
- S3 ObjectCreated 이벤트를 트리거로 증거 파일 자동 처리
- 다양한 파일 타입 (이미지, PDF, 오디오, 비디오, 텍스트) 지원
- GPT-4o, Whisper, Vision API를 활용한 AI 분석
- DynamoDB/Qdrant에 구조화된 데이터 저장

### 주요 기능
1. **멀티 파서 시스템**: 파일 타입별 최적화된 파서
2. **AI 분석 엔진**: 요약, 이혼 사유 태깅 (민법 840조), 리스크 분석
3. **벡터 임베딩**: OpenAI Embedding API를 사용한 RAG 검색
4. **메타데이터 관리**: DynamoDB 기반 증거 메타데이터 저장

---

## 🏗️ 아키텍처

```
S3 Bucket (Evidence Upload)
    ↓ (S3 Event Trigger)
Lambda: ai_worker/handler.py
    ↓
route_parser() → 파일 타입 감지
    ├─ ImageVisionParser     (.jpg, .png)
    ├─ PDFParser             (.pdf)
    ├─ AudioParser           (.mp3, .wav, .m4a)
    ├─ VideoParser           (.mp4, .avi, .mov)
    └─ TextParser            (.txt, .csv, .json)
    ↓
route_and_process()
    ├─ Parse (파싱)
    ├─ Analyze (분석: 요약, 840조 태깅)
    ├─ Embed (벡터화)
    └─ Store (저장)
        ├─ DynamoDB (메타데이터)
        └─ Qdrant (벡터 인덱스)
```

---

## 📁 디렉토리 구조

```
ai_worker/
├── handler.py                 # Lambda 엔트리포인트 (S3 이벤트 처리)
├── src/
│   ├── analysis/              # AI 분석 엔진
│   │   ├── analysis_engine.py # 통합 분석 엔진
│   │   ├── article_840_tagger.py  # 민법 840조 사유 태깅
│   │   ├── evidence_scorer.py  # 증거 점수 평가
│   │   ├── risk_analyzer.py    # 리스크 분석
│   │   └── summarizer.py       # 증거 요약
│   ├── parsers/               # 파일 타입별 파서
│   │   ├── base.py            # BaseParser 추상 클래스
│   │   ├── image_vision.py    # GPT-4o Vision (감정/맥락 분석)
│   │   ├── image_ocr.py       # Tesseract OCR (옵션)
│   │   ├── pdf_parser.py      # PDF 텍스트 추출
│   │   ├── audio_parser.py    # Whisper STT
│   │   ├── video_parser.py    # 비디오 → 오디오 → STT
│   │   ├── text.py            # 일반 텍스트
│   │   └── kakaotalk.py       # 카톡 대화 (TXT/CSV)
│   ├── service_rag/           # 법률 서비스 RAG
│   │   ├── legal_parser.py    # 법률 문서 파싱
│   │   ├── legal_search.py    # 법률 검색
│   │   └── legal_vectorizer.py # 법률 벡터화
│   ├── storage/               # 저장소 레이어
│   │   ├── metadata_store.py  # DynamoDB 메타데이터
│   │   ├── vector_store.py    # Qdrant 벡터 DB
│   │   ├── search_engine.py   # 검색 엔진
│   │   └── storage_manager.py # 통합 저장 관리자
│   └── user_rag/              # 사용자 RAG (하이브리드 검색)
│       ├── hybrid_search.py   # 키워드 + 벡터 검색
│       └── schemas.py         # RAG 스키마
├── tests/                     # 테스트 코드
│   ├── src/                   # 유닛 테스트
│   │   ├── test_parsers.py
│   │   ├── test_analysis_engine.py
│   │   ├── test_article_840_tagger.py
│   │   └── ...
│   └── fixtures/              # 테스트 데이터
├── requirements.txt           # Python 의존성
├── .env.example               # 환경 변수 템플릿
├── pytest.ini                 # Pytest 설정
├── DOCKERFILE                 # Lambda 컨테이너 이미지
└── README.md                  # 이 파일

```

---

## 🚀 시작하기

### 1. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집 (OpenAI API Key, AWS 리소스 등)
vi .env
```

### 2. 의존성 설치

```bash
# Python 3.11+ 필요
pip install -r requirements.txt
```

### 3. 로컬 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 파서 테스트
pytest tests/src/test_parsers.py

# 커버리지 확인
pytest --cov=src --cov-report=html
```

### 4. Lambda 배포

```bash
# Docker 이미지 빌드 (Lambda Container)
docker build -t leh-ai-worker .

# ECR에 푸시 후 Lambda 함수 업데이트
# (배포 스크립트는 별도 제공)
```

---

## 🔧 설정

### 환경 변수 (.env)

주요 환경 변수:

```env
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_GPT_MODEL=gpt-4o
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# AWS Resources
S3_EVIDENCE_BUCKET=leh-evidence-bucket
DYNAMODB_TABLE_EVIDENCE_METADATA=leh-evidence-metadata
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

전체 환경 변수 목록은 `.env.example` 참고.

---

## 📊 처리 흐름 예시

### 예시 1: 이미지 파일 업로드 (divorce_evidence_001.jpg)

```
1. S3 Upload: s3://leh-evidence-bucket/case_123/divorce_evidence_001.jpg
2. Lambda Trigger: handler.handle(event)
3. route_parser('.jpg') → ImageVisionParser
4. Parse: GPT-4o Vision API 호출
   - 감정: "슬픔(0.8), 분노(0.6)"
   - 맥락: "부부 싸움 현장 사진, 물건 파손 흔적"
5. Analyze:
   - Summarizer: "부부 갈등으로 인한 물건 파손 증거"
   - Article840Tagger: "제1호: 배우자의 부정행위 (신뢰도: 0.3)"
6. Embed: OpenAI Embedding API → 1536-dim vector
7. Store:
   - DynamoDB: 메타데이터 (파일명, 타입, 감정, 요약, 태그)
   - Qdrant: 벡터 인덱스 (case_rag_123)
8. Response: {"status": "processed", "file": "...", "parser_type": "ImageVisionParser"}
```

### 예시 2: 오디오 파일 업로드 (call_recording_20240101.mp3)

```
1. S3 Upload: s3://leh-evidence-bucket/case_456/call_recording_20240101.mp3
2. Lambda Trigger: handler.handle(event)
3. route_parser('.mp3') → AudioParser
4. Parse: Whisper STT
   - 텍스트: "여보, 당신이 그 사람이랑 만난 거 다 알아..."
   - 화자: 구분 안 됨 (Whisper 한계)
5. Analyze:
   - Summarizer: "배우자 간 외도 관련 대화, 감정적 충돌"
   - Article840Tagger: "제1호: 배우자의 부정행위 (신뢰도: 0.8)"
6. Embed: 전사 텍스트 → 벡터화
7. Store: DynamoDB + Qdrant
8. Response: {"status": "processed", ...}
```

---

## 🧪 테스트

### 테스트 구조

- `tests/src/`: 유닛 테스트 (파서, 분석 엔진, 저장소)
- `tests/fixtures/`: 테스트 데이터 (샘플 이미지, PDF, 텍스트)

### 주요 테스트 케이스

```bash
# 파서 테스트
pytest tests/src/test_image_vision.py   # GPT-4o Vision
pytest tests/src/test_audio_parser.py   # Whisper STT
pytest tests/src/test_pdf_parser.py     # PDF 파싱

# 분석 엔진 테스트
pytest tests/src/test_article_840_tagger.py  # 민법 840조 태깅
pytest tests/src/test_summarizer.py          # 요약

# 통합 테스트
pytest tests/src/test_integration_e2e.py     # End-to-End
```

### Mock 사용

테스트 시 OpenAI API 호출을 Mock으로 대체:

```python
# pytest.ini 설정
[pytest]
env =
    PYTEST_MOCK_S3=true
    PYTEST_MOCK_QDRANT=true
```

---

## 🔍 디버깅

### CloudWatch Logs 확인

```bash
# Lambda 로그 스트림 확인
aws logs tail /aws/lambda/leh-ai-worker --follow
```

### 로컬 Lambda 테스트

```python
# test_local.py
import json
from handler import handle

event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "leh-evidence-bucket"},
            "object": {"key": "case_123/test.jpg"}
        }
    }]
}

result = handle(event, None)
print(json.dumps(result, indent=2))
```

---

## 📝 마이그레이션 히스토리

**From**: `leh-ai-pipeline` (로컬 개발/테스트 구현)
**To**: `ai_worker` (AWS Lambda 배포 버전)
**Date**: 2025-11-19

### 주요 변경 사항

1. **디렉토리 구조**:
   - `leh-ai-pipeline/src/` → `ai_worker/src/`
   - 모든 파서, 분석, 저장소 모듈 복사

2. **handler.py 통합**:
   - S3 이벤트 처리 로직 구현
   - `route_parser()`, `route_and_process()` 함수 추가
   - mock 처리 → 실제 파이프라인 연결

3. **의존성 병합**:
   - `leh-ai-pipeline/requirements.txt` + `ai_worker/requirements.txt`
   - ChromaDB (로컬) → Qdrant (Vector DB)

4. **환경 설정**:
   - `.env.example` 생성 (AWS 리소스 경로 매핑)

5. **테스트 통합**:
   - `leh-ai-pipeline/tests/` → `ai_worker/tests/src/`
   - pytest.ini, fixtures 복사

6. **백업**:
   - 기존 `ai_worker/` → `ai_worker_backup/` 보존

---

## 🤝 기여 가이드

### Git 워크플로우

```bash
# feature 브랜치에서 작업
git checkout dev
git pull origin dev
git checkout -b feat/new-parser

# 개발 완료 후
git checkout dev
git merge feat/new-parser
git push origin dev

# main에는 PR로만 병합 (P 승인 필요)
```

### 커밋 컨벤션

```
feat: 새 기능 추가
fix: 버그 수정
refactor: 코드 리팩토링
docs: 문서 업데이트
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

---

## 📚 참고 문서

- [LEH 프로젝트 README](../README.md)
- [PRD](../docs/specs/PRD.md)
- [Architecture](../docs/specs/ARCHITECTURE.md)
- [AI Pipeline Design](../docs/specs/AI_PIPELINE_DESIGN.md)
- [Contributing](../docs/CONTRIBUTING.md)

---

## 📞 문의

**Team L (AI / Data)**: AI Worker 구현 및 유지보수
**Team H (Backend)**: FastAPI 통합 및 인프라
**Team P (Frontend/PM)**: 대시보드 UI 및 GitHub 운영

---

**Last Updated**: 2025-11-19
**Version**: 1.0.0 (Migrated from leh-ai-pipeline)
