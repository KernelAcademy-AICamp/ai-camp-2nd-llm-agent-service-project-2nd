# LEH AI Pipeline - 사용 가이드

실제 사용 예제 및 베스트 프랙티스

---

## 목차

- [빠른 시작](#빠른-시작)
- [파일 처리 예제](#파일-처리-예제)
- [검색 예제](#검색-예제)
- [분석 예제](#분석-예제)
- [케이스 관리](#케이스-관리)
- [고급 사용법](#고급-사용법)
- [베스트 프랙티스](#베스트-프랙티스)
- [문제 해결](#문제-해결)

---

## 빠른 시작

### 1. 환경 설정

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정 (.env 파일)
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. 기본 사용 예제

```python
from src.storage.storage_manager import StorageManager

# 스토리지 매니저 초기화
manager = StorageManager()

# 파일 업로드
result = manager.process_file(
    filepath="./evidence/kakao_chat.txt",
    case_id="case_001"
)

print(f"파일 ID: {result['file_id']}")
print(f"저장된 메시지: {result['chunks_stored']}개")

# 검색
results = manager.search(
    query="외도 관련 증거",
    case_id="case_001",
    top_k=5
)

for i, r in enumerate(results, 1):
    print(f"\n{i}. {r['content'][:100]}...")
    print(f"   유사도: {r['distance']:.4f}")
```

---

## 파일 처리 예제

### 카카오톡 대화 파일

```python
from src.parsers.kakaotalk import KakaoTalkParser

# 1. 파서 직접 사용
parser = KakaoTalkParser()
messages = parser.parse("kakao_chat.txt")

for msg in messages[:5]:
    print(f"[{msg.timestamp}] {msg.sender}: {msg.content}")

# 2. StorageManager로 자동 처리
manager = StorageManager()
result = manager.process_file(
    filepath="kakao_chat.txt",
    case_id="divorce_case_2024_001"
)
```

**카카오톡 파일 형식**:
```
2024-01-15 오후 3:30, 홍길동 : 안녕하세요
2024-01-15 오후 3:31, 김철수 : 네, 안녕하세요
```

### PDF 문서

```python
from src.parsers.pdf_parser import PDFParser

parser = PDFParser()
messages = parser.parse("divorce_agreement.pdf")

# 페이지별로 메시지 생성됨
for i, msg in enumerate(messages, 1):
    print(f"페이지 {i}: {msg.content[:200]}...")
```

### 오디오 파일 (음성 녹음)

```python
from src.parsers.audio_parser import AudioParser
from datetime import datetime

parser = AudioParser()
messages = parser.parse(
    file_path="call_recording.mp3",
    default_sender="통화 녹음",
    base_timestamp=datetime(2024, 1, 15, 14, 30)  # 통화 시작 시간
)

# Whisper STT 결과를 시간대별로 출력
for msg in messages:
    print(f"[{msg.timestamp}] {msg.content}")
```

### 비디오 파일

```python
from src.parsers.video_parser import VideoParser

parser = VideoParser()
messages = parser.parse(
    file_path="cctv_footage.mp4",
    default_sender="CCTV 음성"
)

# 비디오에서 오디오 추출 → STT 자동 수행
for msg in messages:
    print(f"[{msg.timestamp}] {msg.content}")
```

### 이미지 파일 (OCR + Vision)

```python
from src.parsers.image_ocr import ImageOCRParser
from src.parsers.image_vision import ImageVisionParser

# 1. OCR만 사용 (텍스트 추출)
ocr_parser = ImageOCRParser()
messages = ocr_parser.parse("text_screenshot.jpg")
print(f"인식된 텍스트: {messages[0].content}")

# 2. Vision 분석 (감정/맥락)
vision_parser = ImageVisionParser()
analysis = vision_parser.analyze_vision("photo.jpg")

print(f"감정: {', '.join(analysis.emotions)}")
print(f"맥락: {analysis.context}")
print(f"분위기: {analysis.atmosphere}")
print(f"신뢰도: {analysis.confidence:.2%}")

# 3. OCR + Vision 통합
messages = vision_parser.parse("evidence_photo.jpg")
# [0]: OCR 결과
# [1]: Vision 분석 결과
```

---

## 검색 예제

### 기본 검색

```python
from src.storage.storage_manager import StorageManager

manager = StorageManager()

# 증거 검색
results = manager.search(
    query="외도 증거",
    case_id="case_001",
    top_k=10
)

for r in results:
    print(f"내용: {r['content'][:100]}...")
    print(f"파일: {r['metadata']['file_id']}")
    print(f"발신자: {r['metadata']['sender']}")
    print(f"유사도: {r['distance']:.4f}\n")
```

### 컨텍스트 확장 검색

```python
from src.storage.search_engine import SearchEngine
from src.storage.vector_store import VectorStore
from src.storage.metadata_store import MetadataStore

# 검색 엔진 초기화
vector_store = VectorStore()
metadata_store = MetadataStore()
search_engine = SearchEngine(vector_store, metadata_store)

# 전후 맥락 포함 검색
results = search_engine.search(
    query="폭력",
    case_id="case_001",
    top_k=5,
    context_window=2  # 전후 2개 메시지씩
)

for r in results:
    print("=== 이전 맥락 ===")
    for ctx in r.context_before:
        print(f"  {ctx}")

    print("\n=== 검색 결과 ===")
    print(f"  {r.content}")

    print("\n=== 이후 맥락 ===")
    for ctx in r.context_after:
        print(f"  {ctx}")
    print("\n" + "="*50 + "\n")
```

### 하이브리드 검색 (증거 + 법률)

```python
from src.user_rag.hybrid_search import HybridSearchEngine
from src.storage.search_engine import SearchEngine
from src.service_rag.legal_search import LegalSearchEngine

# 초기화
evidence_search = SearchEngine(vector_store, metadata_store)
legal_search = LegalSearchEngine()
hybrid_engine = HybridSearchEngine(evidence_search, legal_search)

# 통합 검색
results = hybrid_engine.search(
    query="이혼 사유",
    case_id="case_001",
    top_k=10
)

for r in results:
    if r.source == "legal":
        print(f"📜 법률 조문: {r.content[:100]}...")
    else:
        print(f"📂 증거 자료: {r.content[:100]}...")
    print(f"   유사도: {r.distance:.4f}\n")
```

---

## 분석 예제

### 증거 점수 산정

```python
from src.analysis.evidence_scorer import EvidenceScorer
from src.parsers.base import Message
from datetime import datetime

scorer = EvidenceScorer()

# 단일 메시지 점수
message = Message(
    content="외도 증거입니다. 불륜 관계를 확인했습니다.",
    sender="의뢰인",
    timestamp=datetime.now()
)

result = scorer.score(message)
print(f"점수: {result.score:.1f}/10")
print(f"매칭 키워드: {', '.join(result.matched_keywords)}")
print(f"카테고리: {', '.join(result.categories)}")

# 여러 메시지 일괄 점수
messages = [...]  # 파서로 추출한 메시지
results = scorer.score_batch(messages)

high_value = [
    (msg, res) for msg, res in zip(messages, results)
    if res.score >= 7.0
]

print(f"고가치 증거: {len(high_value)}개")
```

### 위험도 분석

```python
from src.analysis.risk_analyzer import RiskAnalyzer, RiskLevel

analyzer = RiskAnalyzer()
messages = [...]  # 대화 메시지 목록

risk = analyzer.analyze(messages)

# 위험도 출력
print(f"폭력 위험: {risk.violence_risk.value}")
print(f"금전 분쟁: {risk.financial_risk.value}")
print(f"양육권 분쟁: {risk.custody_risk.value}")
print(f"종합 위험도: {risk.overall_risk.value}")

# 위험 지표
print("\n위험 지표:")
for indicator in risk.risk_indicators:
    print(f"  - {indicator}")

# 긴급 개입 필요 여부
if risk.overall_risk == RiskLevel.CRITICAL:
    print("\n⚠️ 긴급 개입 필요!")
```

### 민법 840조 자동 태깅

```python
from src.analysis.article_840_tagger import Article840Tagger, Article840Category

tagger = Article840Tagger()

message = Message(
    content="남편의 외도 사실을 확인했습니다. 증거 사진도 있습니다.",
    sender="의뢰인",
    timestamp=datetime.now()
)

result = tagger.tag(message)

print(f"분류된 카테고리: {[cat.value for cat in result.categories]}")
print(f"신뢰도: {result.confidence:.2%}")

# 카테고리별 매칭 키워드
for category, keywords in result.matched_keywords.items():
    print(f"{category.value}: {', '.join(keywords)}")

# 특정 카테고리 확인
if Article840Category.ADULTERY in result.categories:
    print("민법 840조 제1호 (배우자 부정행위) 해당")
```

### 증거 요약

```python
from src.analysis.summarizer import EvidenceSummarizer, SummaryType

summarizer = EvidenceSummarizer(model="gpt-4o")

# 대화 요약
messages = [...]  # 카카오톡 대화
summary = summarizer.summarize_conversation(
    messages=messages,
    max_words=150,
    language="ko"
)

print(f"요약: {summary.summary}")
print(f"\n핵심 포인트:")
for i, point in enumerate(summary.key_points, 1):
    print(f"  {i}. {point}")
print(f"\n단어 수: {summary.word_count}")

# 문서 요약
with open("divorce_petition.txt", "r") as f:
    text = f.read()

doc_summary = summarizer.summarize_document(
    text=text,
    max_words=200
)
print(doc_summary.summary)

# 증거 컬렉션 요약
evidence_summary = summarizer.summarize_evidence(
    messages=messages,
    max_words=200
)
print(evidence_summary.summary)
```

### 종합 분석 엔진

```python
from src.analysis.analysis_engine import AnalysisEngine

engine = AnalysisEngine()
messages = [...]  # 모든 증거 메시지

# 종합 분석
result = engine.analyze(messages)

# 점수화된 메시지
print(f"총 메시지: {len(result.scored_messages)}")
print(f"평균 점수: {result.summary['average_score']:.2f}")

# 고가치 증거
high_value = engine.get_high_value_messages(
    messages,
    threshold=7.0
)
print(f"고가치 증거: {len(high_value)}개")

for msg, score_result in high_value[:5]:
    print(f"\n[{score_result.score:.1f}점] {msg.content[:100]}...")

# 위험도
risk = result.risk_analysis
print(f"\n종합 위험도: {risk.overall_risk.value}")
```

---

## 케이스 관리

### 케이스 목록 조회

```python
from src.storage.metadata_store import MetadataStore

store = MetadataStore()

# 전체 케이스 목록
cases = store.list_cases()
print(f"전체 케이스 수: {len(cases)}")
for case_id in cases:
    print(f"  - {case_id}")

# 통계 포함 목록
stats_list = store.list_cases_with_stats()
for stats in stats_list:
    print(f"{stats['case_id']}:")
    print(f"  파일: {stats['file_count']}개")
    print(f"  청크: {stats['chunk_count']}개")
```

### 특정 케이스 조회

```python
# 케이스 통계
stats = store.get_case_stats("case_001")
print(f"케이스 ID: {stats['case_id']}")
print(f"파일 수: {stats['file_count']}")
print(f"청크 수: {stats['chunk_count']}")

# 케이스 파일 목록
files = store.get_files_by_case("case_001")
for f in files:
    print(f"{f.filename} ({f.file_type}) - {f.parsed_at}")

# 케이스 청크 목록
chunks = store.get_chunks_by_case("case_001")
print(f"전체 청크: {len(chunks)}개")
```

### 케이스 삭제

```python
from src.storage.metadata_store import MetadataStore
from src.storage.vector_store import VectorStore

metadata_store = MetadataStore()
vector_store = VectorStore()

# 메타데이터만 삭제 (벡터 유지)
metadata_store.delete_case("case_001")

# 완전 삭제 (메타데이터 + 벡터)
metadata_store.delete_case_complete(
    case_id="case_001",
    vector_store=vector_store
)

print("케이스 삭제 완료")

# 삭제 확인
remaining = metadata_store.list_cases()
print(f"남은 케이스: {len(remaining)}개")
```

### 케이스 격리 검증

```python
from src.storage.vector_store import VectorStore

vector_store = VectorStore()

# 격리 검증
is_isolated = vector_store.verify_case_isolation("case_001")

if is_isolated:
    print("✅ 케이스 데이터 격리 확인")
else:
    print("❌ 케이스 데이터 누수 감지!")

# 케이스별 벡터 개수
count = vector_store.count_by_case("case_001")
print(f"케이스 벡터 수: {count}개")
```

---

## 고급 사용법

### 배치 처리

```python
import os
from pathlib import Path

manager = StorageManager()
case_id = "bulk_upload_case"

# 폴더 내 모든 파일 처리
evidence_dir = Path("./evidence")
for file_path in evidence_dir.glob("**/*"):
    if file_path.is_file():
        try:
            result = manager.process_file(
                filepath=str(file_path),
                case_id=case_id
            )
            print(f"✅ {file_path.name}: {result['chunks_stored']}개 청크")
        except Exception as e:
            print(f"❌ {file_path.name}: {e}")
```

### 커스텀 파서 작성

```python
from src.parsers.base import BaseParser, Message
from datetime import datetime
from typing import List

class CustomParser(BaseParser):
    """커스텀 형식 파서"""

    def parse(self, file_path: str) -> List[Message]:
        messages = []

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 커스텀 파싱 로직
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    timestamp_str, sender, content = parts[:3]
                    timestamp = datetime.fromisoformat(timestamp_str)

                    message = Message(
                        content=content.strip(),
                        sender=sender.strip(),
                        timestamp=timestamp
                    )
                    messages.append(message)

        return messages

# 사용
parser = CustomParser()
messages = parser.parse("custom_format.txt")
```

### 분석 결과 시각화

```python
import matplotlib.pyplot as plt
import pandas as pd

# 메시지별 점수 분포
scorer = EvidenceScorer()
messages = [...]  # 파서 출력
results = scorer.score_batch(messages)

scores = [r.score for r in results]
plt.hist(scores, bins=20, edgecolor='black')
plt.xlabel('증거 점수')
plt.ylabel('메시지 수')
plt.title('증거 점수 분포')
plt.show()

# 시간대별 위험도
df = pd.DataFrame([
    {
        'timestamp': msg.timestamp,
        'score': res.score
    }
    for msg, res in zip(messages, results)
])

df['date'] = df['timestamp'].dt.date
daily_avg = df.groupby('date')['score'].mean()
daily_avg.plot(kind='line', title='일별 평균 증거 점수')
plt.show()
```

### 증거 보고서 생성

```python
from datetime import datetime
import json

def generate_evidence_report(case_id: str, output_file: str):
    """증거 분석 보고서 생성"""

    # 데이터 수집
    metadata_store = MetadataStore()
    manager = StorageManager()
    analyzer = AnalysisEngine()

    # 케이스 정보
    stats = metadata_store.get_case_stats(case_id)
    chunks = metadata_store.get_chunks_by_case(case_id)

    # 메시지 변환
    messages = [
        Message(
            content=chunk.content,
            sender=chunk.sender,
            timestamp=chunk.timestamp
        )
        for chunk in chunks
    ]

    # 분석
    analysis = analyzer.analyze(messages)
    high_value = analyzer.get_high_value_messages(messages, threshold=7.0)

    # 보고서 작성
    report = {
        "case_id": case_id,
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_files": stats['file_count'],
            "total_messages": stats['chunk_count'],
            "average_score": analysis.summary['average_score'],
            "high_value_count": len(high_value)
        },
        "risk_analysis": {
            "violence": analysis.risk_analysis.violence_risk.value,
            "financial": analysis.risk_analysis.financial_risk.value,
            "custody": analysis.risk_analysis.custody_risk.value,
            "overall": analysis.risk_analysis.overall_risk.value,
            "indicators": analysis.risk_analysis.risk_indicators
        },
        "high_value_evidence": [
            {
                "content": msg.content,
                "score": res.score,
                "timestamp": msg.timestamp.isoformat(),
                "sender": msg.sender,
                "keywords": res.matched_keywords
            }
            for msg, res in high_value[:20]  # 상위 20개
        ]
    }

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"보고서 생성 완료: {output_file}")

# 사용
generate_evidence_report("case_001", "evidence_report.json")
```

---

## 베스트 프랙티스

### 1. 케이스 ID 명명 규칙

```python
# 권장: 일관된 명명 규칙
case_id = "divorce_2024_001_kim"
case_id = "case_20240115_seoul_001"

# 비권장: 불명확한 ID
case_id = "case1"
case_id = "김씨"
```

### 2. 에러 처리

```python
from pathlib import Path

def safe_process_file(filepath: str, case_id: str):
    """안전한 파일 처리"""

    try:
        # 파일 존재 확인
        if not Path(filepath).exists():
            raise FileNotFoundError(f"파일 없음: {filepath}")

        # 파일 크기 확인 (100MB 제한)
        file_size = Path(filepath).stat().st_size
        if file_size > 100 * 1024 * 1024:
            raise ValueError(f"파일이 너무 큼: {file_size / 1024 / 1024:.1f}MB")

        # 처리
        manager = StorageManager()
        result = manager.process_file(filepath, case_id)

        return {"success": True, "result": result}

    except FileNotFoundError as e:
        return {"success": False, "error": f"파일 오류: {e}"}
    except ValueError as e:
        return {"success": False, "error": f"검증 오류: {e}"}
    except Exception as e:
        return {"success": False, "error": f"처리 실패: {e}"}
```

### 3. 데이터 정리

```python
# 주기적으로 불필요한 케이스 삭제
def cleanup_old_cases(days: int = 365):
    """오래된 케이스 정리"""

    from datetime import datetime, timedelta

    metadata_store = MetadataStore()
    vector_store = VectorStore()

    cutoff_date = datetime.now() - timedelta(days=days)

    for case_id in metadata_store.list_cases():
        files = metadata_store.get_files_by_case(case_id)

        # 모든 파일이 cutoff_date 이전인지 확인
        if all(f.parsed_at < cutoff_date for f in files):
            print(f"삭제: {case_id} (마지막 파일: {max(f.parsed_at for f in files)})")
            metadata_store.delete_case_complete(case_id, vector_store)
```

### 4. 로깅

```python
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('leh_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 사용
try:
    result = manager.process_file(filepath, case_id)
    logger.info(f"파일 처리 성공: {filepath} → {result['chunks_stored']}개 청크")
except Exception as e:
    logger.error(f"파일 처리 실패: {filepath}", exc_info=True)
```

---

## 문제 해결

### Q1: OpenAI API 오류

**문제**: `OpenAIError: The api_key client option must be set`

**해결**:
```bash
# .env 파일 확인
OPENAI_API_KEY=sk-...

# 환경변수 로드 확인
from dotenv import load_dotenv
load_dotenv()

import os
print(os.getenv("OPENAI_API_KEY"))  # None이 아니어야 함
```

### Q2: ffmpeg 오류 (비디오 파서)

**문제**: `ffmpeg audio extraction failed`

**해결**:
```bash
# ffmpeg 설치 확인
ffmpeg -version

# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

### Q3: Tesseract OCR 오류

**문제**: `TesseractNotFoundError`

**해결**:
```bash
# Tesseract 설치
# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# 경로 확인 (Python)
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
```

### Q4: ChromaDB 파일 잠금 오류 (Windows)

**문제**: `PermissionError: [WinError 32]`

**해결**:
```python
# VectorStore 사용 후 명시적으로 삭제
vector_store = VectorStore()
# ... 사용 ...
del vector_store

import gc
gc.collect()  # 가비지 컬렉션
```

### Q5: 메모리 부족 (대용량 파일)

**문제**: 대용량 파일 처리 시 메모리 부족

**해결**:
```python
# 청크 단위로 처리
def process_large_file_in_chunks(filepath, case_id, chunk_size=100):
    """대용량 파일을 청크 단위로 처리"""

    parser = KakaoTalkParser()  # 또는 적절한 파서
    all_messages = parser.parse(filepath)

    manager = StorageManager()

    for i in range(0, len(all_messages), chunk_size):
        chunk_messages = all_messages[i:i+chunk_size]

        # 청크 처리
        # ... 임베딩 및 저장 ...

        print(f"처리: {i+len(chunk_messages)}/{len(all_messages)}")
```

---

## 다음 단계

- [API_REFERENCE.md](./API_REFERENCE.md) - 상세 API 문서
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 시스템 아키텍처
- [FLOW_DIAGRAMS.md](./FLOW_DIAGRAMS.md) - 데이터 플로우
