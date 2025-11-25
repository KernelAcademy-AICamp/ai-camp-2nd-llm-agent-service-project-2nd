# Testing Strategy Guide

LEH 프로젝트의 테스트 전략을 통합 정리합니다.

**TDD 상세 규칙:** [plan.md](plan.md) 참조

---

## 1. TDD 원칙 (Red-Green-Refactor)

모든 기능 구현은 TDD 사이클을 따릅니다:

1. **Red**: 실패하는 테스트 먼저 작성
2. **Green**: 테스트를 통과하는 최소 코드 작성
3. **Refactor**: 코드 개선 (테스트 통과 유지)

### 금지 사항
- ❌ 테스트 없이 기능 구현 PR
- ❌ 테스트와 기능 구현을 다른 PR로 분리
- ❌ 실패하는 테스트를 skip 처리

---

## 2. Backend 테스트

### 테스트 구조

```
backend/tests/
├── test_api/           # API 엔드포인트 테스트
│   ├── test_auth.py
│   ├── test_cases.py
│   └── test_evidence.py
├── test_services/      # 비즈니스 로직 테스트
│   ├── test_case_service.py
│   └── test_evidence_service.py
└── conftest.py         # 공통 fixture
```

### 테스트 레벨

| 레벨 | 대상 | 특징 |
|------|------|------|
| **Unit** | Service, Repository | Mock 사용, 빠른 실행 |
| **Integration** | API 엔드포인트 | TestClient, 실제 DB (test DB) |

### 예시: Service 테스트

```python
# test_services/test_case_service.py
import pytest
from unittest.mock import Mock
from app.services.case_service import CaseService

def test_create_case_success(mock_case_repository):
    service = CaseService(repository=mock_case_repository)
    result = service.create_case(title="테스트 사건", user_id="user_1")

    assert result.title == "테스트 사건"
    mock_case_repository.create.assert_called_once()
```

### 실행 명령어

```bash
# 전체 테스트
pytest

# Unit 테스트만
pytest -m unit

# Integration 테스트만
pytest -m integration

# 커버리지 포함
pytest --cov=app --cov-report=html
```

---

## 3. AI Worker 테스트

### 테스트 구조

```
ai_worker/tests/
├── test_parsers/       # 파서별 테스트
│   ├── test_text_parser.py
│   ├── test_image_parser.py
│   └── test_audio_parser.py
├── test_analysis/      # 분석 엔진 테스트
├── test_storage/       # 저장소 연동 테스트
└── conftest.py
```

### 테스트 레벨

| 레벨 | 대상 | 특징 |
|------|------|------|
| **Unit** | 개별 Parser, Analyzer | 샘플 파일 사용 |
| **Integration** | handler → storage 플로우 | LocalStack 또는 Mock |

### 예시: Parser 테스트

```python
# test_parsers/test_text_parser.py
import pytest
from src.parsers.text import TextParser

def test_parse_kakao_chat():
    parser = TextParser()
    sample_file = "tests/fixtures/sample_kakao.txt"

    result = parser.parse(sample_file)

    assert len(result) > 0
    assert result[0].sender is not None
    assert result[0].timestamp is not None
```

### 커버리지 요구사항

```bash
# 80% 이상 커버리지 필수
pytest --cov=src --cov-fail-under=80
```

---

## 4. Frontend 테스트

### 테스트 구조

```
frontend/src/tests/
├── components/         # 컴포넌트 테스트
│   ├── CaseCard.test.tsx
│   └── EvidenceList.test.tsx
├── hooks/              # 훅 테스트
└── pages/              # 페이지 통합 테스트
```

### 테스트 도구

- **Jest**: 테스트 러너
- **React Testing Library**: 컴포넌트 테스트
- **MSW (Mock Service Worker)**: API 모킹

### 테스트 원칙

1. **사용자 관점 테스트**: 구현 세부사항이 아닌 동작 테스트
2. **접근성 쿼리 우선**: `getByRole`, `getByLabelText` 사용
3. **비동기 처리**: `waitFor`, `findBy*` 사용

### 예시: 컴포넌트 테스트

```typescript
// tests/components/CaseCard.test.tsx
import { render, screen } from '@testing-library/react'
import { CaseCard } from '@/components/cases/CaseCard'

describe('CaseCard', () => {
  it('사건 제목을 표시한다', () => {
    render(<CaseCard title="이혼 사건 #1" status="진행중" />)

    expect(screen.getByRole('heading')).toHaveTextContent('이혼 사건 #1')
    expect(screen.getByText('진행중')).toBeInTheDocument()
  })
})
```

### 실행 명령어

```bash
# 전체 테스트
npm test

# Watch 모드
npm run test:watch

# 커버리지
npm run test:coverage
```

---

## 5. 테스트 데이터 관리

### Fixture 사용

```
tests/fixtures/
├── sample_kakao.txt      # 카카오톡 채팅 샘플
├── sample_image.jpg      # 이미지 샘플
├── sample_audio.mp3      # 오디오 샘플
└── sample_evidence.json  # 증거 메타데이터 샘플
```

### Factory 패턴

```python
# conftest.py
@pytest.fixture
def sample_case():
    return {
        "case_id": "case_001",
        "title": "테스트 사건",
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z"
    }
```

---

## 6. CI 통합

GitHub Actions에서 자동 테스트 실행:

```yaml
# .github/workflows/test.yml
- name: Backend Tests
  run: |
    cd backend
    pytest --cov=app --cov-fail-under=80

- name: AI Worker Tests
  run: |
    cd ai_worker
    pytest --cov=src --cov-fail-under=80

- name: Frontend Tests
  run: |
    cd frontend
    npm test -- --coverage
```

---

## 테스트 체크리스트

### PR 제출 전
- [ ] 새 기능에 대한 테스트 작성됨
- [ ] 모든 테스트 통과
- [ ] 커버리지 80% 이상 유지
- [ ] Mock/Fixture 적절히 사용

### 코드 리뷰 시
- [ ] 테스트가 실제 동작을 검증하는가?
- [ ] 엣지 케이스 테스트 포함 여부
- [ ] 불필요한 테스트 중복 없음

---

## 관련 문서
- [plan.md](plan.md) - TDD 개발 계획 및 체크리스트
- [test_template.md](test_template.md) - 테스트 작성 템플릿
