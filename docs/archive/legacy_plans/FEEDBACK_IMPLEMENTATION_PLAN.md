# FEEDBACK_IMPLEMENTATION_PLAN.md

### *LEH 서비스 피드백 대응 구현 계획*

**버전:** v1.0
**작성일:** 2025-12-04
**작성자:** Team H·P·L
**관련 문서:** `FEEDBACK.md`, `ARCHITECTURE.md`, `AI_PIPELINE_DESIGN.md`

---

## 변경 이력 (Change Log)

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2025-12-04 | L-work | 최초 작성 |

---

## 📋 피드백 대응 우선순위

```
┌─────────────────────────────────────────────────────────────────┐
│                    피드백 대응 우선순위                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔴 긴급 (즉시)                                                 │
│  ├─ 1. 초안 생성 버그 수정                                      │
│  └─ 2. AI 톤앤매너 가이드라인 (방향성 전환)                      │
│           │                                                     │
│           ▼                                                     │
│  🟡 중요 (다음 단계)                                            │
│  ├─ 3. 성능 개선                                                │
│  └─ 4. AI 어드바이스 기능 (증거 부족 안내)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔴 1. 초안 생성 버그 수정

> **피드백:** "초안 생성 기능도 오류가 나서 안됐다"

### 1.1 현황 파악

#### 확인 필요 사항
- [ ] 오류 재현 방법 확인
- [ ] 에러 로그 수집
- [ ] 특정 조건에서만 발생하는지 확인

#### 예상 오류 지점

```
[초안 생성 플로우]

Frontend                Backend                 AI Worker
   │                       │                       │
   │ POST /draft           │                       │
   ├──────────────────────▶│                       │
   │                       │ 1. 사건 메타 조회     │
   │                       │    (PostgreSQL)       │
   │                       │       ⚠️ 오류?        │
   │                       │                       │
   │                       │ 2. 증거 조회          │
   │                       │    (DynamoDB)         │
   │                       │       ⚠️ 오류?        │
   │                       │                       │
   │                       │ 3. RAG 검색           │
   │                       │    (Qdrant)           │
   │                       │       ⚠️ 오류?        │
   │                       │                       │
   │                       │ 4. GPT 호출           │
   │                       │       ⚠️ 오류?        │
   │                       │                       │
   │                       │ 5. 템플릿 렌더링      │
   │                       │       ⚠️ 오류?        │
   │                       │                       │
   │◀──────────────────────│                       │
   │ Response              │                       │
```

### 1.2 디버깅 계획

| 단계 | 작업 | 담당 | 확인 방법 |
|------|------|------|----------|
| 1 | 프론트 에러 확인 | P | 브라우저 콘솔, 네트워크 탭 |
| 2 | API 응답 확인 | H | API 로그, HTTP 상태 코드 |
| 3 | DB 연결 확인 | H | PostgreSQL, DynamoDB 연결 테스트 |
| 4 | Qdrant 연결 확인 | L | 컬렉션 조회 테스트 |
| 5 | GPT API 확인 | L | API 키, 쿼터 확인 |
| 6 | 템플릿 렌더링 확인 | H/L | TemplateStore, DocumentRenderer 테스트 |

### 1.3 예상 수정 작업

#### Case 1: API 연결 오류
```python
# backend/app/services/draft_service.py

async def generate_draft(case_id: str):
    try:
        # 각 단계별 예외 처리 강화
        case = await get_case(case_id)
        if not case:
            raise HTTPException(404, "사건을 찾을 수 없습니다")

        evidences = await get_evidences(case_id)
        if not evidences:
            raise HTTPException(400, "증거가 없습니다. 먼저 증거를 업로드해주세요")

        # ...
    except QdrantException as e:
        logger.error(f"Qdrant 오류: {e}")
        raise HTTPException(503, "검색 서비스 일시 오류")
    except OpenAIError as e:
        logger.error(f"OpenAI 오류: {e}")
        raise HTTPException(503, "AI 서비스 일시 오류")
```

#### Case 2: 프론트 에러 핸들링
```typescript
// frontend/src/services/draftService.ts

async function generateDraft(caseId: string) {
  try {
    const response = await api.post(`/cases/${caseId}/draft`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 400) {
      toast.error(error.response.data.detail);  // "증거가 없습니다"
    } else if (error.response?.status === 503) {
      toast.error("서비스 일시 오류입니다. 잠시 후 다시 시도해주세요");
    } else {
      toast.error("초안 생성에 실패했습니다");
    }
    throw error;
  }
}
```

### 1.4 담당 및 작업

| 담당 | 작업 |
|------|------|
| **Frontend (P)** | 에러 UI 표시, 로딩 상태 개선 |
| **Backend (H)** | API 예외 처리 강화, 로그 추가 |
| **AI Worker (L)** | Qdrant/GPT 연결 확인, 파이프라인 테스트 |

### 1.5 완료 기준

- [ ] 초안 생성 버튼 클릭 시 정상 동작
- [ ] 오류 발생 시 사용자에게 명확한 메시지 표시
- [ ] 에러 로그 수집 가능

---

## 🔴 2. AI 톤앤매너 가이드라인 (방향성 전환)

> **피드백:** "해결책을 제시하는 방향은 X", "객관적인 정보 제시, 맥락에 대한 이해도를 높일 방법"

### 2.1 핵심 원칙

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI 톤앤매너 원칙                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ 하지 말아야 할 것 (해결책 제시)                              │
│  ──────────────────────────────────                             │
│  • "~하세요", "~해야 합니다"                                    │
│  • "승소 가능성이 높습니다"                                     │
│  • "위자료를 3천만원으로 청구하세요"                            │
│  • "이 증거를 추가하세요"                                       │
│                                                                 │
│  ✅ 해야 할 것 (객관적 정보 제시)                               │
│  ──────────────────────────────                                 │
│  • "~입니다", "~으로 나타납니다"                                │
│  • "유사 판례 3건 중 2건이 승소했습니다"                        │
│  • "유사 판례 위자료 범위: 2천만원~4천만원"                     │
│  • "12월 4일 시점의 증거가 없습니다"                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 메시지 변환 예시

| 상황 | ❌ Before | ✅ After |
|------|----------|----------|
| 증거 부족 | "폭언 증거를 더 제출하세요" | "2024년 3월 이후 폭언 관련 증거가 없습니다" |
| 위자료 | "위자료 3천만원을 청구하세요" | "유사 판례 위자료 범위: 2~4천만원 (평균 3천만원)" |
| 승패 예측 | "승소 가능성이 높습니다" | "유사 판례 10건 중 7건 승소 (70%)" |
| 전략 제안 | "외도 증거를 확보해야 합니다" | "외도 관련 증거: 0건" |
| 재산분할 | "60%를 청구하세요" | "유사 판례 분할 비율: 55~65%" |

### 2.3 프롬프트 가이드라인

```python
# ai_worker/src/prompts/guidelines.py

TONE_GUIDELINES = """
[AI 응답 가이드라인]

1. 객관적 정보만 제시
   - 판례 통계, 수치, 날짜 등 사실 기반
   - 주관적 판단이나 조언 금지

2. 현황 설명에 집중
   - "~입니다", "~으로 확인됩니다"
   - "~하세요", "~해야 합니다" 사용 금지

3. 부족한 부분은 사실만 언급
   - ❌ "증거를 더 확보하세요"
   - ✅ "해당 기간 증거가 없습니다"

4. 예측은 통계로 표현
   - ❌ "승소할 것 같습니다"
   - ✅ "유사 판례 승소율: 70% (7/10건)"

5. 면책 문구 필수
   - "본 정보는 참고용이며 법률 조언이 아닙니다"
"""

# 프롬프트에 가이드라인 삽입
def build_prompt(context: str, query: str) -> str:
    return f"""
{TONE_GUIDELINES}

[사건 정보]
{context}

[요청]
{query}

위 가이드라인을 반드시 준수하여 응답하세요.
"""
```

### 2.4 적용 대상

| 기능 | 파일 | 수정 내용 |
|------|------|----------|
| 초안 생성 | `draft_service.py` | 프롬프트에 가이드라인 추가 |
| 증거 분석 | `evidence_analyzer.py` | 분석 결과 톤 변경 |
| AI 어드바이스 | (신규) | 처음부터 가이드라인 적용 |

### 2.5 담당 및 작업

| 담당 | 작업 |
|------|------|
| **AI Worker (L)** | 프롬프트 가이드라인 작성 및 적용 |
| **Backend (H)** | API 응답 메시지 검토 |
| **Frontend (P)** | UI 텍스트 검토 (버튼, 라벨 등) |

### 2.6 완료 기준

- [ ] 모든 AI 응답이 "~하세요" 형태 제거
- [ ] 통계/수치 기반 정보 제시로 변경
- [ ] 면책 문구 표시

---

## 🟡 3. 성능 개선

> **피드백:** "작업 속도가 느리다"

### 3.1 성능 측정 대상

| 구간 | 현재 예상 | 목표 |
|------|----------|------|
| 증거 업로드 → 분석 완료 | ? 초 | 10초 이내 |
| 초안 생성 | ? 초 | 15초 이내 |
| 페이지 로딩 | ? 초 | 2초 이내 |
| RAG 검색 | ? 초 | 1초 이내 |

### 3.2 예상 병목 지점

```
┌─────────────────────────────────────────────────────────────────┐
│                    성능 병목 분석                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [증거 분석 파이프라인]                                          │
│                                                                 │
│  파일 다운로드 ──▶ 파싱 ──▶ GPT 분석 ──▶ 임베딩 ──▶ 저장       │
│       1초           2초       ⚠️ 5~10초      2초       1초       │
│                               (병목!)                           │
│                                                                 │
│  [초안 생성]                                                    │
│                                                                 │
│  DB 조회 ──▶ RAG 검색 ──▶ GPT 생성 ──▶ 렌더링                  │
│     1초        2초        ⚠️ 10~20초      1초                   │
│                           (병목!)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 개선 방안

#### 3.3.1 GPT 호출 최적화

| 방안 | 효과 | 난이도 | 우선순위 |
|------|------|--------|----------|
| **스트리밍 응답** | 체감 속도 향상 | 🟡 중간 | ⭐ 1순위 |
| 병렬 처리 | 전체 시간 단축 | 🟡 중간 | 2순위 |
| 캐싱 | 반복 요청 빠름 | 🟢 낮음 | 3순위 |
| 경량 모델 | 비용+속도 | 🟢 낮음 | 검토 |

#### 3.3.2 스트리밍 응답 구현

```python
# backend/app/api/draft.py

from fastapi.responses import StreamingResponse

@router.post("/cases/{case_id}/draft/stream")
async def generate_draft_stream(case_id: str):
    """스트리밍으로 초안 생성 (실시간 출력)"""

    async def generate():
        async for chunk in draft_service.generate_stream(case_id):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

```typescript
// frontend/src/hooks/useDraftStream.ts

function useDraftStream(caseId: string) {
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const generate = async () => {
    setIsLoading(true);
    setDraft("");

    const eventSource = new EventSource(`/api/cases/${caseId}/draft/stream`);

    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        setIsLoading(false);
      } else {
        const { text } = JSON.parse(event.data);
        setDraft(prev => prev + text);  // 실시간 추가
      }
    };
  };

  return { draft, isLoading, generate };
}
```

#### 3.3.3 로딩 UX 개선

```
┌─────────────────────────────────────────────────────────────────┐
│                    로딩 UX 개선                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Before (나쁜 UX)                                               │
│  ┌─────────────────────────────┐                                │
│  │                             │                                │
│  │      ⏳ 로딩 중...          │  ← 10초간 아무것도 안 보임     │
│  │                             │                                │
│  └─────────────────────────────┘                                │
│                                                                 │
│  After (좋은 UX)                                                │
│  ┌─────────────────────────────┐                                │
│  │ ✅ 사건 정보 조회 완료      │                                │
│  │ ✅ 증거 15건 분석 완료      │                                │
│  │ ⏳ 초안 작성 중... (3/5)    │  ← 진행 상황 표시              │
│  │ ░░░░░░░░░░░░░░░████████    │                                │
│  │                             │                                │
│  │ 청구취지                    │  ← 스트리밍으로 실시간 표시    │
│  │ 1. 원고와 피고는 이혼한다.  │                                │
│  │ 2. 피고는 원고에게...█      │                                │
│  └─────────────────────────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 담당 및 작업

| 담당 | 작업 | 상세 |
|------|------|------|
| **Backend (H)** | 스트리밍 API | SSE 엔드포인트 구현 |
| **Backend (H)** | 성능 로깅 | 각 단계별 소요 시간 측정 |
| **AI Worker (L)** | GPT 스트리밍 | OpenAI 스트리밍 연동 |
| **AI Worker (L)** | 병렬 처리 | 독립 작업 병렬화 |
| **Frontend (P)** | 스트리밍 UI | 실시간 텍스트 표시 |
| **Frontend (P)** | 진행 상태 UI | 프로그레스 바, 단계 표시 |

### 3.5 완료 기준

- [ ] 초안 생성 시 스트리밍으로 실시간 출력
- [ ] 프로그레스 바로 진행 상황 표시
- [ ] 각 구간 소요 시간 로그 수집

---

## 🟡 4. AI 어드바이스 기능 (증거 부족 안내)

> **피드백:** "12월 4일 부분의 증거가 부족해서 해당 증거가 필요합니다 라고 어드바이스를 제시하는 방식"

### 4.1 기능 개요

증거 현황을 분석하여 **부족한 부분을 객관적으로 안내**하는 기능

### 4.2 어드바이스 유형

| 유형 | 설명 | 예시 메시지 |
|------|------|-------------|
| 기간 공백 | 특정 기간 증거 없음 | "2024년 3월~5월 증거가 없습니다" |
| 유형 부족 | 특정 유형 증거 없음 | "녹음 증거: 0건" |
| 유책사유 공백 | 특정 유책사유 증거 없음 | "경제적 학대 관련 증거: 0건" |
| 판례 비교 | 유사 판례 대비 부족 | "유사 판례 평균 증거 수: 15건 (현재: 8건)" |

### 4.3 데이터 구조

```python
@dataclass
class EvidenceAdvice:
    advice_type: str          # 'time_gap', 'type_missing', 'fault_missing', 'precedent_compare'
    severity: str             # 'info', 'warning'
    message: str              # 사용자에게 표시할 메시지
    details: dict             # 상세 정보

# 예시
EvidenceAdvice(
    advice_type="time_gap",
    severity="warning",
    message="2024년 3월~5월 기간의 증거가 없습니다",
    details={
        "gap_start": "2024-03-01",
        "gap_end": "2024-05-31",
        "before_count": 5,
        "after_count": 3
    }
)
```

### 4.4 분석 로직

```python
# ai_worker/src/analysis/evidence_advisor.py

class EvidenceAdvisor:
    """증거 현황 분석 및 어드바이스 생성 (LLM 미사용)"""

    def __init__(self, case_id: str):
        self.case_id = case_id

    def analyze_time_gaps(self, evidences: List[Evidence]) -> List[EvidenceAdvice]:
        """시간대별 공백 분석"""
        dates = sorted([e.timestamp for e in evidences])
        gaps = []

        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            if diff > 30:  # 30일 이상 공백
                gaps.append(EvidenceAdvice(
                    advice_type="time_gap",
                    severity="warning",
                    message=f"{dates[i-1].strftime('%Y년 %m월')}~{dates[i].strftime('%Y년 %m월')} 기간의 증거가 없습니다",
                    details={"gap_days": diff}
                ))

        return gaps

    def analyze_evidence_types(self, evidences: List[Evidence]) -> List[EvidenceAdvice]:
        """증거 유형별 현황 분석"""
        type_counts = Counter(e.evidence_type for e in evidences)
        advices = []

        # 일반적으로 필요한 증거 유형
        expected_types = ["chat_log", "photo", "recording", "document"]

        for etype in expected_types:
            count = type_counts.get(etype, 0)
            advices.append(EvidenceAdvice(
                advice_type="type_status",
                severity="info",
                message=f"{EVIDENCE_TYPE_NAMES[etype]}: {count}건",
                details={"type": etype, "count": count}
            ))

        return advices

    def analyze_fault_coverage(self, evidences: List[Evidence]) -> List[EvidenceAdvice]:
        """유책사유별 현황 분석"""
        fault_counts = Counter()
        for e in evidences:
            for fault in e.fault_types:
                fault_counts[fault] += 1

        advices = []
        all_faults = ["adultery", "violence", "verbal_abuse", "economic_abuse", "desertion"]

        for fault in all_faults:
            count = fault_counts.get(fault, 0)
            advices.append(EvidenceAdvice(
                advice_type="fault_status",
                severity="warning" if count == 0 else "info",
                message=f"{FAULT_NAMES[fault]} 관련 증거: {count}건",
                details={"fault": fault, "count": count}
            ))

        return advices

    def get_all_advices(self, evidences: List[Evidence]) -> List[EvidenceAdvice]:
        """전체 어드바이스 생성"""
        advices = []
        advices.extend(self.analyze_time_gaps(evidences))
        advices.extend(self.analyze_evidence_types(evidences))
        advices.extend(self.analyze_fault_coverage(evidences))
        return advices
```

### 4.5 API 설계

```yaml
# GET /cases/{id}/evidence-advice

Response:
  200:
    case_id: "uuid"
    total_evidence_count: 8
    advices:
      - advice_type: "time_gap"
        severity: "warning"
        message: "2024년 3월~5월 기간의 증거가 없습니다"
      - advice_type: "type_status"
        severity: "info"
        message: "카카오톡 대화: 5건"
      - advice_type: "fault_status"
        severity: "warning"
        message: "경제적 학대 관련 증거: 0건"
    summary:
      time_coverage: "2024-01 ~ 2024-08 (3개월 공백)"
      evidence_types: {"chat_log": 5, "photo": 2, "recording": 1}
      fault_coverage: {"verbal_abuse": 3, "violence": 2, "adultery": 0}
```

### 4.6 UI 설계

```
┌─────────────────────────────────────────────────────────────────┐
│                    증거 현황 어드바이스                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 증거 현황 요약                                              │
│  ─────────────────────────────                                  │
│  총 증거: 8건 │ 기간: 2024-01 ~ 2024-08                         │
│                                                                 │
│  ⚠️ 확인 필요                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • 2024년 3월~5월 기간의 증거가 없습니다                  │    │
│  │ • 경제적 학대 관련 증거: 0건                             │    │
│  │ • 외도 관련 증거: 0건                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  📋 증거 유형별 현황                                            │
│  ─────────────────────────────                                  │
│  │ 카카오톡 대화    ████████████████  5건                       │
│  │ 사진            ████████          2건                       │
│  │ 녹음            ████              1건                       │
│  │ 문서            ░░░░              0건                       │
│                                                                 │
│  📋 유책사유별 현황                                              │
│  ─────────────────────────────                                  │
│  │ 폭언            ████████████      3건                       │
│  │ 폭행            ████████          2건                       │
│  │ 외도            ░░░░              0건                       │
│  │ 경제적 학대     ░░░░              0건                       │
│                                                                 │
│  ℹ️ 본 정보는 참고용이며 법률 조언이 아닙니다                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.7 담당 및 작업

| 담당 | 작업 | 파일 |
|------|------|------|
| **AI Worker (L)** | EvidenceAdvisor 클래스 | `evidence_advisor.py` |
| **Backend (H)** | 어드바이스 API | `GET /cases/{id}/evidence-advice` |
| **Frontend (P)** | 어드바이스 패널 UI | `EvidenceAdvicePanel.tsx` |

### 4.8 완료 기준

- [ ] 시간대별 공백 자동 탐지
- [ ] 증거 유형별 현황 표시
- [ ] 유책사유별 현황 표시
- [ ] 객관적 톤 (안내만, 지시 없음)

---

## 📊 전체 작업 요약

### 우선순위별 담당 작업

#### 🔴 긴급 (1-2주 내)

| 항목 | AI Worker (L) | Backend (H) | Frontend (P) |
|------|---------------|-------------|--------------|
| 버그 수정 | Qdrant/GPT 연결 확인 | API 예외 처리 | 에러 UI |
| 톤앤매너 | 프롬프트 가이드라인 | API 응답 검토 | UI 텍스트 검토 |

#### 🟡 중요 (2-4주 내)

| 항목 | AI Worker (L) | Backend (H) | Frontend (P) |
|------|---------------|-------------|--------------|
| 성능 개선 | GPT 스트리밍 | SSE API | 스트리밍 UI |
| 어드바이스 | EvidenceAdvisor | 어드바이스 API | 어드바이스 패널 |

---

## 🗓️ 다음 단계

1. **버그 재현**: 초안 생성 오류 재현 및 로그 확인
2. **긴급 수정**: 버그 수정 + 톤앤매너 적용
3. **성능 측정**: 현재 성능 baseline 측정
4. **순차 개선**: 스트리밍 → 어드바이스 순서로 구현

---

**END OF FEEDBACK_IMPLEMENTATION_PLAN.md**
