# VERSIONING.md — LEH 버전 관리 규칙

**버전:** v1.0
**작성일:** 2025-11-27
**대상:** Team H · P · L

---

## 1. 버전 관리 원칙

### 1.1 Semantic Versioning (SemVer)

LEH 프로젝트는 **Semantic Versioning 2.0.0**을 따릅니다:

```
MAJOR.MINOR.PATCH
```

| 버전 | 변경 시점 | 예시 |
|------|---------|------|
| **MAJOR** | 하위 호환성 깨지는 변경 (Breaking Change) | API 스키마 변경, DB 마이그레이션 필수 |
| **MINOR** | 하위 호환성 유지하며 기능 추가 | 새 API 엔드포인트, 새 파서 추가 |
| **PATCH** | 버그 수정, 문서 수정 | 보안 패치, 오타 수정 |

### 1.2 Pre-release 버전

MVP 이전에는 `0.x.y` 버전을 사용합니다:

- `0.1.0` ~ `0.9.x`: 알파/베타 단계
- `1.0.0`: 첫 번째 프로덕션 릴리스 (GA)

```
0.2.0        # 현재 버전
0.2.1        # 버그 수정
0.3.0        # 새 기능 추가
1.0.0        # 프로덕션 릴리스
```

---

## 2. 컴포넌트별 버전 관리

### 2.1 버전 동기화 정책

| 컴포넌트 | 버전 파일 | 동기화 정책 |
|----------|----------|-------------|
| **Frontend** | `frontend/package.json` | 통합 버전 사용 |
| **Backend** | `backend/app/__init__.py` | 통합 버전 사용 |
| **AI Worker** | `ai_worker/src/__init__.py` | 독립 버전 사용 (API 변경 시에만 동기화) |

### 2.2 현재 버전

```
Frontend:   0.2.0
Backend:    0.2.0
AI Worker:  0.1.0
```

### 2.3 버전 변경 절차

1. **버전 파일 업데이트**

```bash
# Frontend
npm version minor  # 또는 major, patch

# Backend
# backend/app/__init__.py 수정
__version__ = "0.3.0"

# AI Worker
# ai_worker/src/__init__.py 수정
__version__ = "0.2.0"
```

2. **CHANGELOG.md 업데이트**

3. **Git 태그 생성**

```bash
git tag -a v0.3.0 -m "Release v0.3.0: 새 기능 설명"
git push origin v0.3.0
```

---

## 3. Git 태그 규칙

### 3.1 태그 명명 규칙

```
v{MAJOR}.{MINOR}.{PATCH}
```

예시:
- `v0.2.0` - 통합 릴리스
- `v0.2.1` - 패치 릴리스

### 3.2 컴포넌트별 태그 (선택)

대규모 변경 시 컴포넌트별 태그 사용 가능:

```
frontend-v0.3.0
backend-v0.3.0
ai-worker-v0.2.0
```

### 3.3 태그 생성 명령

```bash
# Annotated 태그 (권장)
git tag -a v0.2.0 -m "Release v0.2.0

## What's Changed
- feat: DynamoDB Mock → Real 전환
- feat: Design System 구현
- fix: handler.py 버그 수정
"

# 태그 푸시
git push origin v0.2.0

# 모든 태그 푸시
git push origin --tags
```

---

## 4. 릴리스 프로세스

### 4.1 릴리스 체크리스트

- [ ] 모든 테스트 통과 (CI 녹색)
- [ ] CHANGELOG.md 업데이트
- [ ] 버전 파일 업데이트 (package.json, __init__.py)
- [ ] PR 생성 및 승인 (dev → main)
- [ ] main 브랜치 머지
- [ ] Git 태그 생성 및 푸시
- [ ] GitHub Release 생성 (선택)

### 4.2 릴리스 주기

| 릴리스 유형 | 주기 | 설명 |
|------------|------|------|
| **Patch** | 필요 시 | 긴급 버그 수정 |
| **Minor** | 1-2주 | 스프린트 종료 시 |
| **Major** | 분기별 | 대규모 변경, Breaking Changes |

### 4.3 GitHub Release

```bash
# GitHub CLI로 릴리스 생성
gh release create v0.2.0 \
  --title "v0.2.0 - Design System & AWS Integration" \
  --notes-file RELEASE_NOTES.md
```

---

## 5. Breaking Changes 관리

### 5.1 Breaking Change 정의

다음 변경은 Breaking Change로 간주:

- API 엔드포인트 URL 변경
- 요청/응답 스키마 변경 (필수 필드 추가/제거)
- 인증 방식 변경
- DB 스키마 변경 (마이그레이션 필요)
- 환경 변수 이름 변경

### 5.2 Breaking Change 처리

1. **MAJOR 버전 증가**
2. **마이그레이션 가이드 작성**
3. **CHANGELOG에 명시**

```markdown
## [1.0.0] - 2025-02-01

### ⚠️ Breaking Changes
- `GET /cases` 응답에서 `created_at` → `createdAt`으로 변경
- 환경 변수 `OPENSEARCH_HOST` → `QDRANT_HOST`로 변경

### Migration Guide
1. Frontend: Case 타입 정의 업데이트
2. Backend: .env 파일 환경 변수 이름 변경
```

---

## 6. 버전 확인 방법

### 6.1 런타임에서 버전 확인

**Backend:**
```python
from app import __version__
print(__version__)  # "0.2.0"
```

**AI Worker:**
```python
from src import __version__
print(__version__)  # "0.1.0"
```

**Frontend:**
```typescript
import packageJson from '../package.json';
console.log(packageJson.version);  // "0.2.0"
```

### 6.2 Git에서 버전 확인

```bash
# 모든 태그 목록
git tag -l

# 현재 커밋의 태그
git describe --tags --always

# 특정 태그의 커밋 확인
git show v0.2.0
```

---

## 7. 자동화 (향후 계획)

### 7.1 Conventional Commits + Release Please

```yaml
# .github/workflows/release.yml
name: Release Please

on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: node
          package-name: leh
```

### 7.2 자동 버전 범프

```bash
# npm version 사용 (Frontend)
npm version patch -m "chore: bump version to %s"

# bump2version 사용 (Backend/AI Worker)
pip install bump2version
bump2version minor
```

---

## 8. 참고 자료

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**END OF VERSIONING.md**
