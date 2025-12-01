# CONTRIBUTING.md — Legal Evidence Hub (LEH)

### *GitHub 협업 규칙 (Team H · P · L)*

**버전:** v2.0  
**작성일:** 2025-11-18  
**대상:**  

- H (Backend)  
- L (AI / Worker)  
- P (PM / Frontend & Approver)

---

# 📌 0. 목적 (Purpose)

이 문서는 **LEH 레포에서 최소한의 규칙만으로 빠르게 협업**하기 위한 가이드이다.

- 복잡한 GitFlow **금지**
- **main 안정성 최우선**
- **dev는 자유로운 Vibe Coding 존**
- GitHub 초보도 그대로 따라 할 수 있도록 설계

---

# 👥 1. 역할(Role)

- **H (Backend)**: FastAPI, RDS, API, 배포 파이프라인
- **L (AI)**: AI Worker, 파이프라인, RAG/임베딩
- **P (Frontend/PM)**: React 대시보드, UX, **PR 승인자(Reviewer 1차)**

---

# 🌱 2. 브랜치 전략 (Branching Strategy)

> ⛔ **절대규칙 (ABSOLUTE RULES)**
> - `main` 브랜치 직접 push 금지 → PR only (Production 배포)
> - `dev` 브랜치 직접 push 금지 → PR only (Staging 배포)
> - 모든 코드 변경은 작업 브랜치(p-work, feat/*)에서 PR을 통해 진행

단일 패턴만 기억하면 된다:

```text
main  ←  dev  ←  feat/*
              ←  p-work (P 개발자 전용, Claude Code 기반)
```

## 2.1 main

- 실제 서비스/배포용 브랜치
- **직접 push 금지**
- 오직 **PR(dev → main)** 로만 변경
- main이 깨지면 변호사 서비스에 즉시 영향 → 항상 “배포 가능한 상태” 유지

## 2.2 dev

- 모든 개발의 기준 브랜치 (Staging 환경 배포)
- **⚠️ 직접 push 금지** — 오직 **PR(p-work/feat/* → dev)** 로만 변경
- Vibe Coding, 대규모 리팩토링, 구조 변경 등은 작업 브랜치에서 진행 후 PR

## 2.3 feat/*

- 필요할 때만 만드는 작업용 브랜치
- 예시:

  - `feat/parser-unify`
  - `feat/ai-routing-v2`
- 흐름:

  ```sh
  git checkout dev
  git pull origin dev
  git checkout -b feat/parser-unify
  # 작업 후
  git checkout dev
  git merge feat/parser-unify
  git push origin dev
  ```

* **feat/* → dev** merge 시 PR 필수 아님 (dev는 실험장)

## 2.4 p-work (P 개발자 전용)

- P 개발자의 **Claude Code 기반** 작업 브랜치
- **모든 작업은 p-work에서 수행 → dev로 merge**
- 흐름:

  ```sh
  # 1. p-work 브랜치로 이동 (없으면 생성)
  git checkout p-work || git checkout -b p-work

  # 2. dev 최신화 후 p-work에 반영
  git pull origin dev
  git merge dev  # 또는 git rebase dev

  # 3. Claude Code로 작업 수행
  # ... 코드 생성, 수정, 테스트 ...

  # 4. p-work에 커밋 & 푸시
  git add .
  git commit -m "feat: implement xxx"
  git push origin p-work

  # 5. dev로 merge (PR 또는 직접 merge)
  git checkout dev
  git merge p-work
  git push origin dev
  ```

- **장점:**
  - Claude Code 작업 이력이 p-work에 보존
  - dev 브랜치의 안정성 유지
  - 롤백이 필요한 경우 쉽게 되돌리기 가능

## 2.5 exp/* (선택)

- 개인 테스트 / 버려도 되는 코드
- **main/dev로 merge 금지**
- 예시: `exp/L-video-extraction-test`

---

# 🧾 3. 커밋 규칙 (Commit Rules)

## 3.1 메시지는 영어 고정

AI 분석/리팩토링, 변경 추적을 위해 **반드시 영어**로 작성한다.

## 3.2 Prefix 규칙

```text
feat:     기능 추가
fix:      버그 수정
refactor: 구조 변경 (기능 변화 없음)
docs:     문서만 변경
chore:    빌드/설정/로그 등 기타
```

### 예시

```text
feat: add unified text conversation parser
fix: wrong timestamp formatting in evidence ingestion
refactor: clean up ai worker pipeline structure
docs: update backend design document
chore: adjust logging level for lambda
```

---

# 🔁 4. 작업 플로우 (Daily Flow)

## 4.1 H / L 공통 루틴

1. **dev 최신화**

```sh
git checkout dev
git pull origin dev
```

2. **작업 + 로컬 테스트**

- AI에게 코드 생성 요청 → 코드 반영
- 최소한 `pytest` 또는 앱 기동 확인

3. **dev로 push**

```sh
git add .
git commit -m "feat: implement xxx"
git push origin dev
```

4. **배포 준비 시 PR 생성 (dev → main)**

- 기능이 일정 수준 이상 완성 & 테스트 완료되면 PR 생성

---

## 4.2 P 루틴 (PR 승인자 / FE 중심)

1. dev 기준으로 UI/대시보드 작업
2. dev 상태를 확인 후, 배포 가능하면 **PR(dev → main)** 생성 또는 승인
3. main 배포 파이프라인 정상 동작 확인

---

# 🔀 5. Pull Request 규칙 (PR Rules)

## 5.1 방향

- **항상 `dev → main`**
  (예외: 문서만 수정하는 경우 → 아래 5.4 참고)

## 5.2 승인자

- 기본 승인자: **P (또는 지정된 Owner 1명)**
- 코드 퀄리티 리뷰보다 **“동작 여부 / 서비스 영향” 확인이 목적**

## 5.3 PR 템플릿 (요약본)

PR 설명에 아래 3가지만 적는다:

```md
# Summary
- 구현/수정한 내용 한 줄 요약

# Changed Files
- backend/app/...
- ai_worker/...
- frontend/src/...

# Impact
- FE 영향 있음/없음
- 마이그레이션 필요 여부 (예: DB 스키마 변경 등)
```

## 5.4 문서 전용 예외

- `docs/*.md`, `CONTRIBUTING.md`, `README.md` 등 **문서만 수정**하는 경우:

  - **직접 main에 push 허용** (hotfix 문서 업데이트용)
- 코드가 포함되면 반드시 dev → main PR 사용

---

# ⚔️ 6. Conflict 해결 기준

### 6.1 원칙: “작성자 또는 마지막 수정자가 책임지고 해결”

- 누가 코드를 짰는지, 누가 최근에 크게 건드렸는지 기준
- 합의 안 되면 **더 많이 이해하고 있는 사람이** 처리

### 6.2 기본 절차

```sh
git checkout dev
git pull origin dev
# conflict 표시된 파일 수정
git add .
git commit
git push origin dev
```

### 6.3 체크리스트

- 공용 스키마/타입 변경 여부 확인 (FE/H/L 상호 공지)
- 필요 시:

  - PR 코멘트에 “breaking change” 표기
  - `docs/` 내 설계 문서도 함께 업데이트

---

# 🚀 7. 배포 규칙 (Deployment)

## 7.1 main → 배포 파이프라인

- main에 merge 되면 GitHub Actions가 동작:

  ```text
  dev → main PR merge
    → CI (테스트)
    → CD (AWS 배포: BE/AI/FE)
  ```

- main 상태 = “변호사에게 보이는 서비스 상태”

## 7.2 dev 환경

- 가능하면 별도의 **staging 환경**에 연결
- staging 장애는 괜찮지만, main 장애는 바로 대응해야 함

---

# 📁 8. 리포 구조 (Repo Layout)

실제 레포 구조는 문서들에 맞춰 아래처럼 통일한다:

```text
root/
├── .env                  # 통합 환경 변수 (Git 제외)
├── .env.example          # 환경 변수 템플릿
├── backend/              # FastAPI 백엔드 (H)
│   ├── app/
│   │   ├── api/          # 라우터 (auth, cases, evidence, admin)
│   │   ├── core/         # 설정, 보안, 의존성
│   │   ├── db/           # 모델, 스키마, 세션
│   │   ├── middleware/   # 보안, 에러, 감사 로그
│   │   ├── repositories/ # 데이터 접근 레이어
│   │   ├── services/     # 비즈니스 로직
│   │   ├── utils/        # S3, DynamoDB, Qdrant, OpenAI 어댑터
│   │   └── main.py       # FastAPI 엔트리포인트
│   ├── tests/
│   └── .env              # → symlink to ../.env
│
├── ai_worker/            # AI Lambda 워커 (L)
│   ├── handler.py        # Lambda 엔트리포인트
│   ├── src/
│   │   ├── parsers/      # 파일 타입별 파서
│   │   ├── analysis/     # 분석 엔진
│   │   ├── service_rag/  # 법률 지식 RAG
│   │   ├── user_rag/     # 사건별 RAG
│   │   └── storage/      # DynamoDB, Qdrant 저장소
│   ├── tests/
│   └── .env              # → symlink to ../.env
│
├── frontend/             # Next.js 대시보드 (P)
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React 컴포넌트
│   │   ├── hooks/        # 커스텀 훅
│   │   ├── lib/          # 유틸리티, API 클라이언트
│   │   ├── types/        # TypeScript 타입
│   │   └── tests/        # 테스트
│   └── .env              # → symlink to ../.env
│
├── docs/                 # 설계 문서
│   ├── specs/            # PRD, Architecture, API Spec 등
│   ├── guides/           # 개발 가이드
│   ├── business/         # 비즈니스 문서
│   └── archive/          # 아카이브
│
├── .github/              # GitHub 설정
│   ├── workflows/        # CI/CD
│   └── PULL_REQUEST_TEMPLATE.md
│
├── CLAUDE.md             # AI 에이전트 규칙
├── CONTRIBUTING.md       # 협업 규칙 (이 파일)
└── README.md             # 프로젝트 소개
```

---

# 🧰 9. Git 치트 시트 (Cheat Sheet)

### 현재 브랜치 확인

```sh
git branch
```

### dev로 이동

```sh
git checkout dev
```

### dev 최신 코드 받기

```sh
git pull origin dev
```

### 변경사항 커밋 & dev로 push

```sh
git add .
git commit -m "feat: ..."
git push origin dev
```

### PR 생성

- GitHub 웹 UI → **Compare & pull request** → `base: main`, `compare: dev` 확인 → **Create PR**

---

# ✅ 10. 팀 약속 (Team Agreement)

- **main은 절대 깨지지 않는다.**
- **dev는 마음껏 부수고 고치는 공간이다.**
- **PR은 형식이 아니라 “서비스를 지키는 마지막 안전장치”이다.**
- **AI는 개발을 가속하는 도구이지, 책임을 대신지는 존재가 아니다.**

이 네 가지를 지키는 선에서, 나머지는 **유연하게** 결정한다.

---

**END OF CONTRIBUTING.md**
