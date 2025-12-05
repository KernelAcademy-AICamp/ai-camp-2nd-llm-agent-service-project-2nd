# E2E 테스트 가이드

## 빠른 시작

### 1. 로컬 테스트 (localhost:3000)
```bash
cd frontend
npm run test:e2e
```

### 2. 외부 사이트 테스트 (Production/Staging)
```bash
# Windows PowerShell
$env:BASE_URL="https://your-site.vercel.app"; npx playwright test e2e/production.spec.ts

# Windows CMD
set BASE_URL=https://your-site.vercel.app && npx playwright test e2e/production.spec.ts

# Mac/Linux
BASE_URL=https://your-site.vercel.app npx playwright test e2e/production.spec.ts
```

---

## 테스트 명령어

| 명령어 | 설명 |
|--------|------|
| `npm run test:e2e` | 전체 E2E 테스트 실행 |
| `npm run test:e2e:ui` | UI 모드로 테스트 (브라우저에서 확인) |
| `npx playwright test --headed` | 브라우저 창 띄우며 테스트 |
| `npx playwright show-report` | 테스트 리포트 보기 |

---

## 테스트 파일 목록

```
frontend/e2e/
├── auth.spec.ts        # 인증 플로우 테스트
├── cases.spec.ts       # 사건 관리 테스트
├── evidence.spec.ts    # 증거 업로드 테스트
├── homepage.spec.ts    # 홈페이지 접속 테스트
└── production.spec.ts  # 외부 사이트 테스트
```

---

## 외부 사이트 테스트 예시

### Vercel 배포 사이트 테스트
```bash
$env:BASE_URL="https://leh-frontend.vercel.app"; npx playwright test e2e/production.spec.ts
```

### Netlify 배포 사이트 테스트
```bash
$env:BASE_URL="https://leh-app.netlify.app"; npx playwright test e2e/production.spec.ts
```

### AWS CloudFront 테스트
```bash
$env:BASE_URL="https://d1234567890.cloudfront.net"; npx playwright test e2e/production.spec.ts
```

### 커스텀 도메인 테스트
```bash
$env:BASE_URL="https://app.leh-legal.com"; npx playwright test e2e/production.spec.ts
```

---

## 테스트 항목 (production.spec.ts)

| 테스트 | 설명 |
|--------|------|
| 메인 페이지 접속 | 홈페이지 로드 확인 |
| 로그인 페이지 접속 | 로그인 폼 표시 확인 |
| 회원가입 페이지 접속 | 회원가입 폼 표시 확인 |
| 관계도 페이지 접속 | /cases/1/relationship 접속 |
| 404 페이지 처리 | 없는 페이지 접근 시 처리 확인 |
| 페이지 로드 성능 | 5초 이내 로드 확인 |
| 모바일 뷰 테스트 | iPhone X 해상도 테스트 |
| 다크모드 확인 | 다크모드 렌더링 테스트 |

---

## 스크린샷 확인

테스트 후 스크린샷 파일 위치:
```
frontend/test-results/
├── prod-homepage.png      # 메인 페이지
├── prod-login.png         # 로그인 페이지
├── prod-signup.png        # 회원가입 페이지
├── prod-relationship.png  # 관계도 페이지
├── prod-404.png           # 404 페이지
├── prod-mobile.png        # 모바일 뷰
└── prod-darkmode.png      # 다크모드
```

---

## 브라우저 창 띄우며 테스트 (디버깅용)

```bash
# 브라우저 창을 띄우고 천천히 실행
$env:BASE_URL="https://your-site.com"; npx playwright test e2e/production.spec.ts --headed --slowmo=1000
```

---

## 특정 테스트만 실행

```bash
# 메인 페이지 테스트만
npx playwright test -g "메인 페이지"

# 모바일 테스트만
npx playwright test -g "모바일"
```

---

## 문제 해결

### 브라우저 설치 오류
```bash
npx playwright install
```

### 타임아웃 오류
```bash
# 타임아웃 늘리기 (60초)
npx playwright test --timeout=60000
```

### 상세 로그 보기
```bash
DEBUG=pw:api npx playwright test
```
