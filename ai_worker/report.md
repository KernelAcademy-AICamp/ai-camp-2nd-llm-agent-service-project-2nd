# AI Worker 법적 증거 추적 시스템 구현 보고서

## 개요

법적 증거물을 정확하게 추적하고 분석하는 시스템을 구현했습니다.
핵심 목표: **"증거는 어디에 있어?"** 질문에 정확한 위치 정보로 답변 가능하게 만들기

```
예: "카톡_배우자.txt 247번째 줄에 외도 증거가 있습니다"
```

---

## 1. 스키마 설계 (src/schemas/)

### 새로 생성된 파일들

| 파일 | 설명 |
|------|------|
| `source_location.py` | 원본 파일 내 위치 정보 (라인/페이지/세그먼트) |
| `legal_analysis.py` | 민법 840조 기반 법적 분류 및 신뢰도 |
| `evidence_file.py` | 파일 메타데이터 (해시, EXIF, 상태) |
| `evidence_chunk.py` | 개별 증거 단위 + 위치 정보 |
| `evidence_cluster.py` | 연관 증거 그룹핑 |
| `search_result.py` | 검색 결과 + 법적 인용 형식 |
| `__init__.py` | 모듈 exports |

### 핵심 스키마

#### SourceLocation - 원본 위치 추적
```python
class SourceLocation(BaseModel):
    file_name: str
    file_type: FileType  # kakaotalk | pdf | image | audio
    line_number: Optional[int]      # 카카오톡용
    page_number: Optional[int]      # PDF용
    segment_start_sec: Optional[float]  # 음성용
    image_index: Optional[int]      # 이미지용

    def to_citation(self) -> str:
        # "파일명 247번째 줄" 형식 반환
```

#### LegalCategory - 민법 840조 카테고리
```python
class LegalCategory(str, Enum):
    ADULTERY = "adultery"           # 제1호: 부정행위
    DESERTION = "desertion"         # 제2호: 악의의 유기
    MISTREATMENT_BY_SPOUSE = "mistreatment_by_spouse"
    MISTREATMENT_BY_INLAWS = "mistreatment_by_inlaws"  # 제3호
    HARM_TO_OWN_PARENTS = "harm_to_own_parents"        # 제4호
    UNKNOWN_WHEREABOUTS = "unknown_whereabouts"        # 제5호
    DOMESTIC_VIOLENCE = "domestic_violence"            # 제6호
    FINANCIAL_MISCONDUCT = "financial_misconduct"
    # ...
```

#### ConfidenceLevel - 신뢰도 레벨
```python
class ConfidenceLevel(int, Enum):
    UNCERTAIN = 1      # 불확실
    WEAK = 2           # 약한 정황
    SUSPICIOUS = 3     # 의심 정황
    STRONG = 4         # 강력한 정황
    DEFINITIVE = 5     # 확정적 증거
```

---

## 2. V2 파서 구현 (src/parsers/)

### 새로 생성된 파일들

| 파일 | 핵심 기능 |
|------|----------|
| `kakaotalk_v2.py` | 라인 번호 추적, 멀티라인 메시지 처리 |
| `pdf_parser_v2.py` | 페이지 번호 추적, 파일 해시 계산 |
| `image_parser_v2.py` | EXIF 추출 (촬영시간, GPS, 기기정보) |
| `audio_parser_v2.py` | 세그먼트 시간 범위 (MM:SS-MM:SS) |

### KakaoTalkParserV2 - 실제 내보내기 형식 지원

```
------------------------------
2023년 5월 10일 수요일
------------------------------
오전 9:23, 홍길동 : 메시지 내용
```

**출력 예시:**
```
test_kakao.txt 4번째 줄
  [홍길동] "오늘 몇시에 와?"
  -> 카테고리: ['general'], Level 1
```

### ImageParserV2 - EXIF 메타데이터 추출

```python
@dataclass
class EXIFMetadata:
    datetime_original: Optional[datetime]  # 촬영 시간
    gps_coordinates: Optional[GPSCoordinates]  # 위치
    device_info: Optional[DeviceInfo]  # 촬영 기기
```

### AudioParserV2 - 세그먼트 시간 추적

```python
@dataclass
class AudioSegment:
    segment_index: int
    start_sec: float
    end_sec: float
    text: str

    def format_time_range(self) -> str:
        # "01:23-01:45" 형식
```

---

## 3. 분석 모듈 통합 (src/analysis/)

### 새로 생성된 파일

| 파일 | 설명 |
|------|------|
| `legal_analyzer.py` | Article840Tagger + EvidenceScorer 통합 |

### LegalAnalyzer - 통합 분석기

```python
class LegalAnalyzer:
    def analyze(self, chunk: EvidenceChunk) -> LegalAnalysis:
        # 1. Article840Tagger로 카테고리 분류
        # 2. EvidenceScorer로 점수 계산
        # 3. LegalAnalysis 생성 및 반환

    def analyze_batch(self, chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
        # 일괄 분석 후 legal_analysis 필드 업데이트

    def get_summary_stats(self, chunks: List[EvidenceChunk]) -> dict:
        # 카테고리별 분포, 고가치 증거 수 등 통계
```

### 분석 결과 예시

```
입력: "어제 그 사람 또 만났어. 호텔에서."
출력:
  - 카테고리: adultery
  - 신뢰도: Level 1
  - 키워드: [호텔]
  - 검토필요: True (중요 카테고리이나 신뢰도 낮음)

입력: "뭐? 불륜이야?"
출력:
  - 카테고리: adultery
  - 신뢰도: Level 4 (강력한 정황)
  - 키워드: [불륜]
```

---

## 4. 저장소 통합 (src/storage/)

### 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `storage_manager_v2.py` | LegalAnalyzer 연동, 자동 분석 기능 |

### StorageManagerV2 - 자동 분석 파이프라인

```python
class StorageManagerV2:
    def __init__(self, auto_analyze: bool = True):
        self.legal_analyzer = LegalAnalyzer(use_ai=False)

    def _store_chunks(self, chunks, case_id):
        # 자동 분석 실행
        if self.auto_analyze:
            chunks = self.legal_analyzer.analyze_batch(chunks)

        # Qdrant에 저장 (분석 결과 포함)
        for chunk in chunks:
            payload = chunk.to_search_payload()
            payload["reasoning"] = chunk.legal_analysis.reasoning
            payload["matched_keywords"] = chunk.legal_analysis.matched_keywords
            # ...
```

---

## 5. 전체 파이프라인

```
[파일 업로드]
     ↓
[V2 파서] → EvidenceChunk (위치 정보 포함)
     ↓
[LegalAnalyzer] → LegalAnalysis (카테고리, 신뢰도)
     ↓
[VectorStore] → Qdrant 저장 (임베딩 + 메타데이터)
     ↓
[검색] → SearchResult (법적 인용 형식)
```

---

## 6. 테스트 결과

### 파싱 + 분석 통합 테스트

```
=== 파싱 결과 ===
총 청크: 4개

=== 분석 결과 ===
test_evidence.txt 4번째 줄
  [홍길동] "오늘 몇시에 와?"
  -> 카테고리: ['general'], Level 1

test_evidence.txt 5번째 줄
  [김영희] "어제 그 사람 또 만났어. 호텔에서."
  -> 카테고리: ['adultery'], Level 1, 키워드: [호텔]

test_evidence.txt 6번째 줄
  [홍길동] "뭐? 불륜이야?"
  -> 카테고리: ['adultery'], Level 4, 키워드: [불륜]

test_evidence.txt 7번째 줄
  [김영희] "시어머니가 또 폭언했어"
  -> 카테고리: ['mistreatment_by_inlaws'], Level 1, 키워드: [폭언, 시어머니]

=== 통계 ===
카테고리별: {general: 1, adultery: 2, mistreatment_by_inlaws: 1}
고가치 증거: 1개
검토 필요: 1개
```

---

## 7. 파일 목록

### 새로 생성된 파일 (11개)

```
src/schemas/
├── __init__.py
├── source_location.py
├── legal_analysis.py
├── evidence_file.py
├── evidence_chunk.py
├── evidence_cluster.py
└── search_result.py

src/parsers/
├── kakaotalk_v2.py
├── pdf_parser_v2.py
├── image_parser_v2.py
└── audio_parser_v2.py

src/analysis/
└── legal_analyzer.py

src/storage/
└── storage_manager_v2.py
```

### 수정된 파일 (1개)

```
src/analysis/__init__.py  # LegalAnalyzer export 추가
```

---

## 8. 검색 엔진 V2 (src/storage/search_engine_v2.py)

### SearchEngineV2 - 법적 인용 형식 지원

```python
engine = SearchEngineV2(vector_store)

# 기본 검색
result = engine.search("외도 증거", case_id="case_001")

# 카테고리별 검색
result = engine.search_by_category(LegalCategory.ADULTERY, case_id)

# 인물별 검색
result = engine.search_by_person("김영희", case_id)

# 고가치 증거 조회 (Level 4-5)
result = engine.get_high_value_evidence(case_id)

# 인용으로 직접 조회
item = engine.get_evidence_by_citation("카톡_배우자.txt", case_id, line_number=247)

# 응답 출력
print(result.to_answer())
# **'외도 증거'** 검색 결과: 3건
# 1. 카톡_배우자.txt 247번째 줄 (2023-05-10 09:23) [김영희]
#    "어제 그 사람 또 만났어..."
#    신뢰도: Level 4, 카테고리: adultery
```

---

## 9. 키워드 확장 (article_840_tagger.py)

### 새로 추가된 카테고리

| 카테고리 | 설명 |
|---------|------|
| `DOMESTIC_VIOLENCE` | 가정폭력 (제6호 세부) |
| `FINANCIAL_MISCONDUCT` | 재정 비행 (제6호 세부) |

### 확장된 키워드 예시

**폭력 (DOMESTIC_VIOLENCE)**
```
때렸, 맞았, 멱살, 머리채, 뺨, 주먹, 발로 찼
멍, 상처, 응급실, 진단서
협박, 죽인다, 통제, 감시, 스토킹
```

**외도 (ADULTERY)**
```
바람피, 양다리, 내연녀, 내연남
만나고 있어, 사귀고 있어
몰래, 들켰, 걸렸
```

**유기 (DESERTION)**
```
집에 안 와, 안 들어와, 잠수
생활비, 돈 안 줘, 카드 끊
애도 안 봐, 육아 안 해
```

**재정 비행 (FINANCIAL_MISCONDUCT)**
```
도박, 빚, 채무, 사채
빼돌렸, 숨겼, 낭비, 탕진
통장, 계좌, 명의
```

### 테스트 결과

```
[OK] "남편이 또 때렸어" -> domestic_violence
[OK] "바람피고 있어" -> adultery
[OK] "애도 안 봐" -> desertion
[OK] "도박으로 빚이 1억이야" -> financial_misconduct
[OK] "시어머니가 구박해" -> mistreatment_by_inlaws

=== Result: 13/13 passed ===
```

---

## 10. AI 기반 분석 (legal_analyzer.py)

### GPT-4 연동 구현

```python
# 키워드 기반 분석 (기본)
analyzer = LegalAnalyzer(use_ai=False)
analysis = analyzer.analyze(chunk)

# AI 기반 분석 (GPT-4)
ai_analyzer = LegalAnalyzer(use_ai=True, ai_model="gpt-4o-mini")
analysis = ai_analyzer.analyze(chunk)
```

### 주요 기능

| 기능 | 설명 |
|------|------|
| `_analyze_ai_based()` | GPT-4를 사용한 정확한 법적 분류 |
| `_get_system_prompt()` | 민법 840조 전문 프롬프트 |
| `_build_analysis_prompt()` | 청크 → 프롬프트 변환 |
| `_parse_ai_response()` | JSON 응답 → LegalAnalysis 변환 |
| `_fallback_to_keyword()` | API 오류 시 키워드 기반으로 fallback |

### 시스템 프롬프트 설계

```
당신은 한국 이혼 소송 전문 법률 AI입니다.
민법 840조 이혼 사유:
1. adultery (제1호): 부정행위
2. desertion (제2호): 악의의 유기
3. domestic_violence (제6호): 가정폭력
4. financial_misconduct (제6호): 재정 비행
...

신뢰도 레벨 (1-5):
1. UNCERTAIN: 관련성 불확실
2. WEAK: 약한 정황
3. SUSPICIOUS: 의심 정황
4. STRONG: 강력한 정황
5. DEFINITIVE: 확정적 증거

출력: JSON 형식
```

### Fallback 동작

```
OPENAI_API_KEY 없음 → 키워드 기반 분석으로 fallback
API 오류 발생 → 키워드 기반 분석으로 fallback
```

---

## 11. 테스트 코드 작성

### 새로 생성된 테스트 파일

| 파일 | 테스트 수 | 설명 |
|------|----------|------|
| `test_kakaotalk_v2.py` | 12개 | KakaoTalkParserV2 파싱, 라인 번호 추적 |
| `test_legal_analyzer.py` | 25개 | LegalAnalyzer 분석, 카테고리, 신뢰도 |
| `test_search_engine_v2.py` | 22개 | SearchEngineV2 검색, 필터, 변환 |

### 테스트 결과

```
tests/src/test_legal_analyzer.py: 25 passed
tests/src/test_search_engine_v2.py: 22 passed
tests/src/test_kakaotalk_v2.py: 12 passed
================================================
Total: 59 passed, 0 failed
```

### 테스트 커버리지

- KakaoTalkParserV2: 81%
- SearchEngineV2: 56%
- LegalAnalyzer: 19% (AI fallback 제외)

---

## 12. 완료 현황

| 작업 | 상태 |
|------|------|
| 1. 검색 엔진 업데이트 | ✓ |
| 2. 키워드 확장 | ✓ |
| 3. AI 기반 분석 | ✓ |
| 4. 테스트 코드 작성 | ✓ |

### 전체 파이프라인

```
[파일 업로드] → [V2 파서] → [LegalAnalyzer] → [VectorStore] → [SearchEngineV2]
                    ↓              ↓                              ↓
              라인번호 추적    카테고리/신뢰도         법적 인용 형식 출력
```

---

## 작성일

2025-12-01 (최종)
