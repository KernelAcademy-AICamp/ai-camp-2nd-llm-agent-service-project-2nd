# LEH AI Pipeline

이혼 소송 증거 관리 및 분석을 위한 AI 기반 파이프라인 시스템

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [설치 및 실행](#설치-및-실행)
- [프로젝트 구조](#프로젝트-구조)
- [문서](#문서)

---

## 프로젝트 개요

**LEH AI Pipeline**은 이혼 소송에서 발생하는 다양한 형태의 증거 자료를 **자동으로 수집, 분석, 관리**하는 AI 기반 시스템입니다.

### 목적

1. **증거 자동 파싱**: 카카오톡, PDF, 이미지, 오디오, 비디오 등 다양한 형태의 증거 자동 처리
2. **증거 가치 평가**: AI 기반 증거 점수 산정 및 위험도 분석
3. **법률 조항 자동 분류**: 민법 840조 이혼 사유 자동 태깅
4. **증거 검색 및 요약**: 벡터 검색 기반 관련 증거 탐색 및 LLM 기반 요약
5. **케이스별 격리**: 사건별 데이터 완전 격리로 데이터 보안 강화

### 대상 사용자

- **변호사**: 이혼 소송 증거 관리 및 분석
- **법률 사무소**: 케이스 관리 자동화
- **개인 의뢰인**: 증거 자료 정리 및 이해

---

## 주요 기능

### 1. 📄 멀티포맷 파서 (Parsers)

| 파서 | 지원 형식 | 주요 기능 |
|------|----------|----------|
| **KakaoTalk Parser** | `.txt` | 카카오톡 대화 파싱, 발신자/시간 추출 |
| **PDF Parser** | `.pdf` | PDF 문서 텍스트 추출 (PyPDF2) |
| **Text Parser** | `.txt` | 일반 텍스트 파일 파싱 |
| **Image OCR Parser** | `.jpg`, `.png` | 이미지 텍스트 인식 (Tesseract) |
| **Image Vision Parser** | `.jpg`, `.png` | 감정/맥락/분위기 분석 (GPT-4o Vision) |
| **Audio Parser** | `.mp3`, `.m4a`, `.wav` | 음성 → 텍스트 변환 (Whisper STT) |
| **Video Parser** | `.mp4`, `.avi`, `.mov` | 비디오 → 오디오 → 텍스트 (ffmpeg + Whisper) |

### 2. 🧠 AI 분석 엔진 (Analysis)

#### Evidence Scorer
- **기능**: 증거 가치 점수 산정 (0-10점)
- **방식**: 키워드 기반 가중치 계산
- **카테고리**: 이혼, 폭력, 금전, 외도, 학대 등

#### Risk Analyzer
- **기능**: 사건 위험도 평가
- **지표**: 폭력 위험, 금전 분쟁, 양육권 분쟁
- **출력**: 위험 수준 (low/medium/high/critical)

#### Article 840 Tagger
- **기능**: 민법 840조 이혼 사유 자동 분류
- **카테고리**:
  - 제1호: 배우자 부정행위 (Adultery)
  - 제2호: 악의의 유기 (Desertion)
  - 제3호: 배우자 직계존속의 부당한 대우 (Mistreatment by In-laws)
  - 제4호: 자기 직계존속에 대한 학대/유기 (Harm to Own Parents)
  - 제5호: 생사 3년 이상 불명 (Unknown Whereabouts)
  - 제6호: 혼인 지속 불가능한 중대 사유 (Irreconcilable Differences)
  - 일반 증거 (General)

#### Evidence Summarizer
- **기능**: 증거 자동 요약 (GPT-4o)
- **유형**: 대화 요약, 문서 요약, 증거 컬렉션 요약
- **출력**: 요약문 + 핵심 포인트 추출

### 3. 💾 스토리지 시스템 (Storage)

#### Metadata Store (SQLite)
- **테이블**: `evidence_files`, `evidence_chunks`
- **기능**:
  - 파일/청크 메타데이터 관리
  - 케이스별 격리 (case_id 인덱싱)
  - 케이스 완전 삭제 (cascade)

#### Vector Store (ChromaDB)
- **컬렉션**: `leh_evidence`
- **임베딩**: OpenAI text-embedding-3-small (768차원)
- **기능**:
  - 유사도 검색 (Cosine similarity)
  - 케이스별 필터링 (where 조건)
  - 케이스 격리 검증

#### Storage Manager
- **기능**: 파서 + VectorStore + MetadataStore 통합
- **프로세스**: 파일 → 파싱 → 임베딩 → 저장

### 4. 🔍 검색 시스템 (Search)

#### Search Engine
- **기능**: 벡터 검색 + 컨텍스트 확장
- **특징**: 이전/이후 메시지 자동 추가

#### Hybrid Search
- **기능**: 사용자 증거 + 법률 지식 통합 검색
- **출력**: 통합 검색 결과 (거리 기준 정렬)

### 5. ⚖️ 법률 RAG (Legal RAG)

#### Legal Parser
- **기능**: 법률 조문 파싱 및 벡터화
- **출처**: 민법, 가사소송법 등

#### Legal Search
- **기능**: 법률 조문 검색
- **특징**: 관련 조문 자동 탐색

---

## 기술 스택

### Core
- **Python 3.12**
- **Pydantic** - 데이터 검증 및 모델링

### AI & ML
- **OpenAI API**
  - GPT-4o: 텍스트 요약, 분석
  - GPT-4o Vision: 이미지 감정/맥락 분석
  - Whisper: 음성 인식 (STT)
  - text-embedding-3-small: 텍스트 임베딩
- **pytesseract**: OCR (Optical Character Recognition)

### Storage
- **ChromaDB**: 벡터 데이터베이스 (로컬 persist)
- **SQLite**: 메타데이터 저장

### Media Processing
- **PyPDF2**: PDF 텍스트 추출
- **ffmpeg-python**: 비디오 → 오디오 변환
- **Pillow (PIL)**: 이미지 처리

### Testing
- **pytest**: 유닛 테스트 프레임워크
- **pytest-cov**: 커버리지 측정 (94% 달성)
- **unittest.mock**: Mock 테스트

---

## 설치 및 실행

### 사전 요구사항

1. **Python 3.12+** 설치
2. **ffmpeg** 설치 (비디오 처리용)
   ```bash
   # Windows (Chocolatey)
   choco install ffmpeg

   # macOS (Homebrew)
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

3. **Tesseract OCR** 설치
   ```bash
   # Windows
   # https://github.com/UB-Mannheim/tesseract/wiki 에서 설치

   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-kor
   ```

### 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd leh-ai-pipeline

# 2. 가상환경 생성 및 활성화
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

### 실행

```python
from src.storage.storage_manager import StorageManager

# 스토리지 매니저 초기화
manager = StorageManager(
    vector_db_path="./data/chromadb",
    metadata_db_path="./data/metadata.db"
)

# 파일 처리
result = manager.process_file(
    filepath="./evidence/kakao_chat.txt",
    case_id="case_001"
)

# 검색
results = manager.search(
    query="외도 증거",
    case_id="case_001",
    top_k=5
)
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 모듈만
pytest tests/test_parsers.py -v
```

---

## 프로젝트 구조

```
leh-ai-pipeline/
├── src/
│   ├── parsers/              # 파일 파서
│   │   ├── base.py           # 기본 파서 인터페이스
│   │   ├── kakaotalk.py      # 카카오톡 파서
│   │   ├── pdf_parser.py     # PDF 파서
│   │   ├── text.py           # 텍스트 파서
│   │   ├── image_ocr.py      # OCR 파서
│   │   ├── image_vision.py   # GPT-4o Vision 파서
│   │   ├── audio_parser.py   # Whisper 오디오 파서
│   │   └── video_parser.py   # 비디오 파서
│   │
│   ├── analysis/             # 분석 엔진
│   │   ├── evidence_scorer.py    # 증거 점수 산정
│   │   ├── risk_analyzer.py      # 위험도 분석
│   │   ├── article_840_tagger.py # 민법 840조 태깅
│   │   ├── summarizer.py         # LLM 요약
│   │   └── analysis_engine.py    # 통합 분석 엔진
│   │
│   ├── storage/              # 저장소 시스템
│   │   ├── metadata_store.py     # SQLite 메타데이터
│   │   ├── vector_store.py       # ChromaDB 벡터 저장소
│   │   ├── storage_manager.py    # 통합 스토리지 관리
│   │   ├── search_engine.py      # 검색 엔진
│   │   └── schemas.py            # 데이터 스키마
│   │
│   ├── service_rag/          # 법률 RAG 서비스
│   │   ├── legal_parser.py       # 법률 조문 파서
│   │   ├── legal_search.py       # 법률 검색
│   │   ├── legal_vectorizer.py   # 법률 벡터화
│   │   └── schemas.py
│   │
│   └── user_rag/             # 사용자 RAG
│       ├── hybrid_search.py      # 통합 검색
│       └── schemas.py
│
├── tests/                    # 테스트 (304 tests, 94% coverage)
│   ├── test_parsers.py
│   ├── test_analysis.py
│   ├── test_storage.py
│   └── ...
│
├── docs/                     # 문서
│   ├── README.md             # 프로젝트 개요 (현재 파일)
│   ├── ARCHITECTURE.md       # 시스템 아키텍처
│   ├── API_REFERENCE.md      # API 레퍼런스
│   ├── FLOW_DIAGRAMS.md      # 데이터 플로우
│   └── USAGE_GUIDE.md        # 사용 가이드
│
├── data/                     # 데이터 저장 디렉토리
│   ├── chromadb/             # 벡터 데이터베이스
│   └── metadata.db           # SQLite 메타데이터
│
├── requirements.txt          # Python 의존성
├── pytest.ini                # pytest 설정
└── README.md                 # 메인 README
```

---

## 문서

- [**ARCHITECTURE.md**](./ARCHITECTURE.md) - 시스템 아키텍처 상세 설명
- [**API_REFERENCE.md**](./API_REFERENCE.md) - 모든 클래스 및 메서드 API 레퍼런스
- [**FLOW_DIAGRAMS.md**](./FLOW_DIAGRAMS.md) - 데이터 플로우 다이어그램
- [**USAGE_GUIDE.md**](./USAGE_GUIDE.md) - 사용 가이드 및 코드 예제

---

## 라이선스

Copyright (c) 2024 LEH AI Pipeline Team

---

## 팀

- **L (AI/Data)**: AI 파이프라인, 분석 엔진, 파서 개발
- **H (Backend/Infra)**: 백엔드 API, 인프라 구축
- **P (Frontend/PM)**: 프론트엔드 UI, 프로젝트 관리

---

## 버전 히스토리

### v1.0.0 (2024-01-XX)
- ✅ 7가지 파서 구현 (KakaoTalk, PDF, Text, OCR, Vision, Audio, Video)
- ✅ 4가지 분석 엔진 (Scorer, Risk, Article 840, Summarizer)
- ✅ 케이스별 데이터 격리 시스템
- ✅ 벡터 검색 및 하이브리드 검색
- ✅ 304 테스트, 94% 커버리지 달성

---

## 문의

프로젝트 관련 문의사항은 이슈 트래커를 이용해주세요.
