
## LEH AI Worker 고급 패턴 & 클린코드 가이드

> 대상: **L(AI Worker 담당)**, AI 코드 생성기
> 범위: **S3 Event → 텍스트/이미지/음성 분석 → DynamoDB/Qdrant 저장**

---

# 1. 기본 목표

* **증거 타입이 늘어나도 구조가 무너지지 않는 Worker 설계**
* **AI 모델 변경(Whisper, GPT-4o Vision, Embedding) 시 최소 수정**
* **일관된 로깅 / 오류 분류 / 재시도 정책 체계화**
* **도메인 객체(EvidenceRecord)와 Infra(AWS) 명확 분리**

---

# 2. 기본 디렉터리 구조

bash
ai_worker/
  handler.py                # 엔트리 포인트, orchestration only
  processors/               # 파일 타입별 Processor (Strategy Pattern)
    base.py
    text_parser.py
    ocr_processor.py
    stt_processor.py
    pdf_processor.py
  storage/                  # DynamoDB / S3 / Qdrant Adapter Layer
    dynamo.py
    s3.py
    qdrant.py
  workflows/                # workflow 정의 (예: drive ingestion)
    leh_drive_ingestion_mvp.json

---

# 3. Handler 책임 (Single Responsibility Principle)

`handler.py`는 **오케스트레이션 전용**이어야 한다.

### Handler가 해야 할 일

1. **Event 파싱**
2. **파일 확장자/타입 판별**
3. **적절한 Processor 선택 (Strategy Pattern)**
4. **Processor.process() 호출**
5. **저장(storage 모듈)에 위임**

### Handler가 하면 안 되는 일 (금지)

* ❌ 직접 STT/OCR 호출
* ❌ boto3 DynamoDB SDK를 직접 호출
* ❌ Qdrant 클라이언트를 직접 사용하는 것
* ❌ EvidenceRecord 직접 생성 (Factory 사용해야 함)

---

# 4. Processor 설계 (Strategy Pattern)

Processor는 **파일 타입별 처리 전략**을 담당한다.

---

## 4.1 Base 클래스

python
from abc import ABC, abstractmethod

class EvidenceProcessor(ABC):
    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        ...

    @abstractmethod
    def process(self, s3_uri: str) -> EvidenceRecord:
        ...

모든 Processor는 이 추상 클래스를 구현한다.

---

## 4.2 구현 예시 (이미지 → OCR)

python
class ImageOcrProcessor(EvidenceProcessor):
    def supports(self, ext: str) -> bool:
        return ext.lower() in [".jpg", ".jpeg", ".png"]

    def process(self, s3_uri: str) -> EvidenceRecord:
        # 1. S3에서 이미지 로드
        # 2. Vision/OCR 호출
        # 3. EvidenceRecord 생성 후 반환
        ...

---

## 4.3 Processor 선택 로직

python
PROCESSORS: list[EvidenceProcessor] = [
    TextProcessor(...),
    PdfProcessor(...),
    ImageOcrProcessor(...),
    AudioSttProcessor(...),
]

def select_processor(ext: str) -> EvidenceProcessor:
    for p in PROCESSORS:
        if p.supports(ext):
            return p
    raise UnsupportedFileTypeError(ext)

---

# 5. Storage 레이어 (Adapter Pattern)

Worker는 직접 boto3나 Qdrant SDK를 호출하지 않는다.

---

## 예시: DynamoDB 저장

python

# storage/dynamo.py

def save_evidence(record: EvidenceRecord) -> None:
    # boto3 dynamodb client 사용
    ...

## 예시: Qdrant Indexing

python

# storage/qdrant.py

def index_evidence_vector(record: EvidenceRecord, vector: list[float]) -> None:
    ...

---

# 6. EvidenceRecord / Factory

증거의 최종 구조(EvidenceRecord)는 도메인 모델로 고정한다.

---

## 6.1 EvidenceRecord 모델

python
from dataclasses import dataclass
from typing import Literal

@dataclass
class EvidenceRecord:
    evidence_id: str
    case_id: str
    type: Literal["text", "image", "audio", "video", "pdf"]
    timestamp: str
    speaker: str | None
    labels: list[str]
    summary: str
    content: str
    s3_key: str

---

## 6.2 Factory 패턴

python
def make_evidence_record(
    case_id: str,
    type: str,
    content: str,
    **kwargs,
) -> EvidenceRecord:
    ...

모든 Processor는 EvidenceRecord를 직접 만들지 않고 **Factory 메서드**로 호출한다.

---

# 7. AI 호출 패턴

AI 모델 호출은 **직접 SDK 사용 금지**, 반드시 Wrapper(Client) 이용.

---

## 7.1 Wrapper 예시

python
class VisionClient:
    def extract_text(self, image_bytes: bytes) -> str:
        ...

class SttClient:
    def transcribe(self, audio_bytes: bytes) -> str:
        ...

---

## 7.2 규칙

* 모든 AI 호출은 반드시:

  * Timeout
  * Retry (지수 백오프)
  * Logging (민감정보 제외)
* Prompt 내용, 파라미터는 `.md` 또는 config 파일로 분리
* Worker 내부에서는 **content 전문을 로그로 남기지 않는다**

---

# 8. 에러 처리 & 재시도

Worker의 안정성을 위해 에러 유형을 명확하게 구분한다.

---

## 8.1 에러 종류

| 에러 종류            | 설명                 | 후속 조치      |
| ---------------- | ------------------ | ---------- |
| `TransientError` | 네트워크/일시적 OpenAI 장애 | 재시도        |
| `PermanentError` | 지원하지 않는 포맷, 손상 파일  | DLQ 이동     |
| `SecurityError`  | 민감정보 처리 위반         | 알림 + 버킷 점검 |

---

## 8.2 재시도 정책

* AWS Lambda / SQS Re-drive 정책에 의존
* Processor 내부에서 무한 재시도 금지

---

# 9. 로깅 원칙

### 기록해야 하는 정보

* case_id
* evidence_id
* processor_name
* status ("start", "extract", "save", "index", "done")

### 금지

* ❌ content 전문 로그
* ❌ summary 전문 로그
* ❌ 프롬프트 전체 출력

---

# 10. 테스트 전략 (AI Worker)

Worker는 **세 가지 레벨**의 테스트가 필요하다.

---

## 10.1 Processor 유닛 테스트

* Input: S3 URI / mock 파일
* Output: EvidenceRecord 구조 검증
* OCR/STT/Vision/Embedding은 mock fixture 사용

---

## 10.2 Storage 테스트

* DynamoDB Local
* Qdrant Test Container
* S3 Localstack

---

## 10.3 Handler 통합 테스트

* Input: S3 Event fixture
* Flow:

  1. Event 파싱
  2. Processor 선택
  3. Processor.process()
  4. storage.save / storage.index

---

# 11. 확장성 (새 타입 추가 절차)

새로운 파일 타입을 지원하려면 다음 4단계를 따른다.

1. `processors/`에 새 Processor 구현
2. `PROCESSORS` 리스트에 Processor 추가
3. 단위 테스트 + 통합 테스트 추가
4. plan.md 및 API_SPEC에 변경 없으면 BE/FE 영향 없음

---

# 12. 결론

이 가이드의 목적:

* Worker가 **견고하고 예측 가능한 파이프라인**을 유지할 것
* 파일 타입 / AI 모델 / 스토리지 구조 확장 시 **코드 변경 최소화**
* Strategy + Adapter + Factory 패턴을 통해 유지보수성 극대화

AI 및 L 담당자는 Worker 코드 작성·수정 시
**본 문서의 패턴을 반드시 우선 적용해야 한다.**
