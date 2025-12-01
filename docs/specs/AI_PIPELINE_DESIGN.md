
### *증거 분석·요약·라벨링·RAG 구축 파이프라인*

**버전:** v2.0
**작성일:** 2025-11-18
**작성자:** Team L(AI)
**참고 문서:**

* `PRD.md`
* `ARCHITECTURE.md`

---

# 📌 0. 문서 목적

본 문서는 LEH(Legal Evidence Hub)에서 사용되는
**전체 AI 파이프라인 구조**를 정의한다.

AI Worker(L)가 수행하는:

* 증거 ingest
* 파일 타입 자동 판별
* STT/OCR/Parsing
* 요약(Summarization)
* 의미 분석(유책사유/화자/감정/시점 등)
* Embedding 생성
* 사건별 RAG Index 구축(Qdrant)

전 과정을 상세히 기술한다.

백엔드 및 프론트엔드 개발자는 AI Worker가 **어떤 결과를 생성하며**,
그 결과가 **DynamoDB/Qdrant**에서 어떻게 활용되는지 이 문서를 참고한다.

---

# 🧭 1. AI 파이프라인 전체 개요

LEH AI 파이프라인은 다음 특징을 가진다:

### ✔ 100% 자동화

S3 업로드 → S3 Event → AI Worker 실행 → DynamoDB / Qdrant 업데이트

### ✔ 증거 타입별 맞춤 처리

* Text → 구조화 파싱
* Image → Vision OCR + 상황/감정 설명
* Audio → Whisper STT + diarization
* Video → 음성 추출 후 STT + frame 분석(선택)
* PDF → Text Extract + OCR fallback

### ✔ 사건 단위 RAG 구축

각 사건은 독립된 embedding index(`case_rag_<case_id>`)로 관리된다.

### ✔ 법률 도메인 최적화

민법 제840 기준 자동 라벨링
유책사유 기반 필터링
타임라인 생성

---

# 🏗 2. 파이프라인 전체 다이어그램

               ┌───────────────────────┐
               │   S3 Evidence Upload  │
               └─────────┬─────────────┘
                         ▼ (Event)
                ┌──────────────────┐
                │ AI Worker (L)    │
                │ Lambda/ECS       │
                └───────┬──────────┘
      ┌──────────────────┼────────────────────┐
      ▼                  ▼                    ▼
┌─────────────┐   ┌───────────────┐   ┌────────────────┐
│ Preprocess  │   │ Content       │   │ Semantic       │
│ File Type   │   │ Extraction    │   │ Analysis       │
└──────┬──────┘   └──────┬────────┘   └────────┬───────┘
       ▼                 ▼                    ▼
┌─────────────┐   ┌───────────────┐   ┌────────────────┐
│ OCR / STT   │   │ Summarization │   │ Labeling       │
│ Parsing     │   │ (GPT-4o)      │   │ (유책사유 등)  │
└──────┬──────┘   └──────┬────────┘   └────────┬───────┘
       ▼                 ▼                    ▼
┌────────────────────────────────────────────────────────┐
│                Embedding Generation                    │
│             (OpenAI / Voyage / Local)                  │
└───────────────────────┬────────────────────────────────┘
                        ▼
                ┌───────────────┐
                │ Qdrant RAG │
                │ 사건별 index   │
                └──────┬────────┘
                        ▼
                ┌───────────────┐
                │ DynamoDB JSON │
                │ Evidence Meta │
                └───────────────┘

---

# 🧩 3. 파이프라인 단계 상세

## 3.1 Step 1 — 파일 타입 자동 판별

S3에서 파일을 임시 다운로드 후 확장자·헤더 기반으로 판별:

| 타입    | 판별 방식                        |
| ----- | ---------------------------- |
| text  | `.txt`, MIME=text/plain      |
| image | `.jpg`, `.png`, Vision check |
| audio | `.mp3`, `.m4a`               |
| video | `.mp4`                       |
| pdf   | `.pdf`                       |

PDF의 초기 Paralegal 설계에서도 동일하게 파일 타입 기반 분기 흐름을 사용했다.

---

## 3.2 Step 2 — Content Extraction

### 3.2.1 Text File Parsing

**카카오톡 형태가 아니어도 아무 텍스트나 자동 정규화 처리**

* 날짜/시간 감지 (`regex + GPT assist`)
* 대화 구조 추출:

  json
  { "speaker": "", "timestamp": "", "message": "" }
  
* 시스템 메시지/이모지 제거
* 중복 메시지 제거

---

### 3.2.2 Image → OCR + Vision 분석

(PDF에서도 OCR + Vision 정보 추출 구조를 명확히 언급함 )

사용 모델:

* **GPT-4o Vision(우선)**
* Tesseract(백업)

추출 정보:

* 텍스트 내용
* 장면 요약
* 인물/사람 여부
* 감정/톤
* 법률적으로 중요한 표현 감지

---

### 3.2.3 Audio → STT + Diarization

**Whisper 기반**, PDF의 기존 설계와 동일.

추출 결과:

json
[
  {
    "speaker": "S1",
    "timestamp": "00:01:23",
    "text": "그만 좀 소리 질러!"
  }
]

필요 기능:

* 화자 분리
* 욕설/폭언 감지
* 타임스탬프 포함

---

### 3.2.4 Video → Audio + Frame 분석

필수는 아님(MVP 옵션), 구조만 정의:

* ffmpeg로 audio 추출 → STT 처리
* 프레임 기반 OCR (폭행 장면 여부 감지 가능)

---

### 3.2.5 PDF → Text Extract → OCR fallback

* 텍스트 PDF → PyPDF2
* 스캔본 PDF → OCR → Vision 분석

---

# 🧠 4. Step 3 — Summarization (요약)

요약은 기존 Paralegal 시스템에서 핵심 기능이었다.
PDF 설계에서 GPT 기반 요약 프로세스를 도입했으며, LEH에서 이를 확장한다.

### 요약 규칙

1. **법률적 사건 흐름 중심**
2. **날짜 / 화자 / 행위 / 감정 포함**
3. **유책사유 관련 내용은 강조**
4. **증거 번호 자동 표시 가능**

### 출력 예시

json
"2021-03-22 새벽, 피고가 고성을 지르며 폭언하였고 원고는 공포감을 느꼈다."

---

# ⚖️ 5. Step 4 — Semantic Analysis (의미 분석)

### 5.1 유책사유 자동 라벨링 (민법 제840 기준)

* 부정행위
* 악의의 유기
* 학대
* 유기
* 계속적 불화
* 3년 실종
* 기타 중대한 사유

### 5.2 기타 Legal Features

* 감정 분석
* 위험 표현(협박, 위협, 통제)
* 관계 패턴
* 사실관계 핵심 포인트(인정/부정 문장)

---

# 🔍 6. Step 5 — Embedding 생성

### Embedding 모델

* OpenAI text-embedding-3-large
* 또는 Voyage 등 사건 특화 모델
* Qdrant와 호환되는 1536~3072 dimension

### Embedding 대상

* OCR/STT 전체 텍스트
* 요약
* 파싱된 대화 message
* 사건 핵심 포인트

---

# 🔎 7. Step 6 — 사건별 RAG Index 구축 (Qdrant)

PDF에서도 RAG 기반 Draft 생성이 핵심 기능으로 강조됨.
LEH에서는 이를 사건 단위로 완전히 분리한다.

### 인덱스 이름

case_rag_{case_id}

### 문서 구조

json
{
  "id": "case_123_ev_3",
  "case_id": "case_123",
  "evidence_id": "ev_3",
  "content": "전체 텍스트",
  "summary": "...",
  "labels": ["폭언"],
  "timestamp": "2024-12-21",
  "vector": [0.12, ...]
}

---

# 🗂 8. Step 7 — DynamoDB 저장 구조

Worker는 최종 JSON을 DynamoDB에 저장한다:

json
{
  "case_id": "case_123",
  "evidence_id": "ev_3",
  "type": "audio",
  "timestamp": "2024-12-25",
  "speaker": "S1",
  "labels": ["폭언"],
  "ai_summary": "...",
  "insights": ["지속적 고성"],
  "content": "STT 결과 전문",
  "s3_key": "cases/123/raw/xx.m4a",
  "qdrant_id": "case_123_ev_3"
}

---

# 🧩 9. Step 8 — 타임라인 데이터 생성

타임라인 구성 요소:

* timestamp
* speaker
* main_event (요약 기반)
* evidence_id

타임라인은 FE에서 그대로 렌더링할 수 있도록 다음 형태로 저장:

json
{
  "timeline_event": {
    "evidence_id": "ev_3",
    "timestamp": "2024-12-25T10:20:00Z",
    "description": "피고가 고성을 지르며 폭언함",
    "labels": ["폭언"]
  }
}

---

# 🛠 10. Worker 내부 설계

### 필수 파이썬 모듈

* boto3 (S3, DynamoDB)
* Qdrant client
* openai (4o / Whisper)
* ffmpeg/ffprobe
* regex/mecab(선택)
* pydantic

---

### Worker 구조

ai_worker/
├── handler.py          # Lambda 핸들러
├── processor/
│   ├── router.py       # 타입별 분기
│   ├── text_parser.py
│   ├── ocr.py
│   ├── stt.py
│   ├── semantic.py
│   ├── embed.py
│   └── timeline.py
└── utils/
    ├── s3.py
    ├── qdrant.py
    ├── dynamo.py
    └── ffmpeg.py

---

# 🚨 11. 에러 핸들링 & 재처리

### Worker 실패 시

* 실패 사유 로그 기록
* DynamoDB에 `"status": "failed"` 저장
* S3 → DLQ(SQS Dead Letter Queue) 연동 가능

### 재처리

POST /admin/reprocess-evidence

---

# 🧪 12. 테스트 전략

### Unit Test

* 타입별 parser 테스트
* OCR mock test
* STT mock test
* 유책사유 라벨링 테스트
* embedding 사이즈 검증

### Integration Test

* S3 → Worker → DynamoDB 전체 플로우
* Qdrant RAG 쿼리

---

# 🤝 13. 백엔드/프론트 연동 인터페이스

| 목적            | 출처          | 목적지      |
| ------------- | ----------- | -------- |
| 증거 metadata   | AI Worker   | DynamoDB |
| 증거 검색         | Qdrant  | Backend  |
| Draft Preview | BE → GPT-4o | FE       |
| Timeline      | DynamoDB    | FE       |

---

# ✔️ 14. 최종 산출물

AI 파이프라인이 최종적으로 제공하는 데이터들은:

1. **증거 raw → 정제된 content**
2. **요약(ai_summary)**
3. **유책사유(labels)**
4. **임베딩(vector)**
5. **증거 인사이트(insights)**
6. **타임라인 데이터**
7. **RAG Index 문서**

이 7개가 LEH 전체 기능의 기반이 된다.

---

# 🔚 END OF AI_PIPELINE_DESIGN.md
