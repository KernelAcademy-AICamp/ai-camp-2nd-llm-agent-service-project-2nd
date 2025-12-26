# 법률 문서 JSON 템플릿 구현 계획

## 배경

컨퍼런스 인사이트: 법률 문서 템플릿을 **텍스트 + 문서 형식(줄바꿈, 들여쓰기, 정렬)** 정보를 포함한 JSON으로 변환하면 산출물 품질이 크게 향상됨.

## 목표

1. 법률 문서 템플릿을 구조화된 JSON으로 변환
2. Qdrant에 템플릿 JSON 저장 및 검색
3. GPT 프롬프트에서 JSON 템플릿 활용
4. 정확한 문서 형식으로 최종 산출물 생성

---

## Phase 1: 템플릿 JSON 스키마 설계 (완료)

### 완료 항목
- [x] 이혼소장 스키마 설계 (`docs/divorce_complaint_schema.json`)
- [x] 예시 문서 생성 (`docs/divorce_complaint_example.json`)

### 스키마 핵심 구조
```json
{
  "text": "청구 내용",
  "format": {
    "indent_level": 1,
    "indent_chars": 4,
    "alignment": "left",
    "spacing_before": 1,
    "spacing_after": 1,
    "bold": false,
    "hanging_indent": true
  }
}
```

### 추가 템플릿 (향후)
- [ ] 이혼 답변서
- [ ] 준비서면
- [ ] 양육비 청구서
- [ ] 재산분할 청구서

---

## Phase 2: Qdrant 템플릿 저장소 구축

### 2.1 Collection 설계

```python
# Collection: legal_templates
# 용도: 법률 문서 템플릿 저장 및 검색

template_point = {
    "id": "template_divorce_complaint_v1",
    "vector": [...],  # 템플릿 설명 임베딩
    "payload": {
        "template_type": "이혼소장",
        "version": "1.0.0",
        "schema": {...},      # 전체 JSON 스키마
        "example": {...},     # 예시 데이터
        "description": "가정법원 이혼소송 소장 템플릿",
        "applicable_cases": ["divorce", "custody", "alimony"],
        "created_at": "2024-12-03T00:00:00Z"
    }
}
```

### 2.2 파일 위치
- `ai_worker/src/storage/template_store.py` (신규)

### 2.3 핵심 기능
```python
class TemplateStore:
    def get_template(self, template_type: str) -> dict:
        """템플릿 타입으로 JSON 스키마 조회"""

    def search_templates(self, query: str) -> list[dict]:
        """쿼리로 적합한 템플릿 검색"""

    def upload_template(self, template: dict) -> str:
        """새 템플릿 업로드"""
```

---

## Phase 3: Draft 생성 파이프라인 개선

### 3.1 현재 구조
```
사용자 요청 → RAG 검색 → GPT 프롬프트 → 텍스트 초안
```

### 3.2 개선 구조
```
사용자 요청 → RAG 검색 → 템플릿 선택 → GPT 프롬프트 → JSON 초안 → 문서 렌더링
                            ↓
                    Qdrant 템플릿 조회
```

### 3.3 수정 대상 파일
- `backend/app/services/draft_service.py`
  - 템플릿 조회 로직 추가
  - GPT 프롬프트에 JSON 스키마 포함
  - 응답을 JSON으로 파싱

### 3.4 GPT 프롬프트 개선
```python
prompt = f"""
다음 JSON 스키마에 맞춰 이혼소장 초안을 작성하세요.

## 스키마
{template_schema}

## 증거 데이터
{evidence_context}

## 사건 정보
{case_info}

응답은 반드시 유효한 JSON 형식으로 출력하세요.
"""
```

---

## Phase 4: 문서 렌더링 (JSON → 문서)

### 4.1 렌더러 설계

```python
# backend/app/services/document_renderer.py

class DocumentRenderer:
    def render_to_text(self, json_doc: dict) -> str:
        """JSON을 포맷팅된 텍스트로 변환"""

    def render_to_docx(self, json_doc: dict) -> bytes:
        """JSON을 Word 문서로 변환"""

    def render_to_pdf(self, json_doc: dict) -> bytes:
        """JSON을 PDF로 변환"""
```

### 4.2 렌더링 규칙
```python
FORMAT_RULES = {
    "indent_level": lambda n: "    " * n,  # 4칸 들여쓰기
    "alignment": {
        "center": lambda w, t: t.center(w),
        "right": lambda w, t: t.rjust(w),
        "left": lambda w, t: t
    },
    "spacing_before": lambda n: "\n" * n,
    "spacing_after": lambda n: "\n" * n,
}
```

---

## Phase 5: API 확장

### 5.1 템플릿 관리 API
```
GET  /api/templates              - 템플릿 목록
GET  /api/templates/{type}       - 특정 템플릿 조회
POST /api/templates              - 템플릿 업로드 (관리자)
```

### 5.2 초안 생성 API 수정
```python
# 기존
POST /api/cases/{case_id}/draft
Response: { "draft": "텍스트 초안..." }

# 변경
POST /api/cases/{case_id}/draft
Response: {
    "draft_json": {...},       # 구조화된 JSON
    "draft_text": "...",       # 렌더링된 텍스트
    "template_used": "이혼소장"
}
```

---

## 구현 우선순위

| 순서 | 작업 | 담당 | 예상 범위 |
|------|------|------|-----------|
| 1 | TemplateStore 구현 | L-work | ai_worker |
| 2 | 템플릿 업로드 스크립트 | L-work | ai_worker |
| 3 | draft_service 수정 | Backend | backend |
| 4 | DocumentRenderer 구현 | Backend | backend |
| 5 | API 확장 | Backend | backend |

---

## 기술 스택

- **Qdrant**: 템플릿 벡터 저장소 (legal_templates collection)
- **OpenAI GPT-4o**: JSON 형식 초안 생성
- **python-docx**: Word 문서 렌더링 (선택)
- **WeasyPrint/ReportLab**: PDF 렌더링 (선택)

---

## 예상 효과

1. **일관된 문서 형식**: 모든 초안이 동일한 포맷 규칙 적용
2. **유지보수 용이**: 템플릿 수정 시 코드 변경 불필요
3. **확장성**: 새로운 문서 유형 추가 용이
4. **품질 향상**: GPT가 구조화된 스키마 기반으로 정확한 출력 생성
