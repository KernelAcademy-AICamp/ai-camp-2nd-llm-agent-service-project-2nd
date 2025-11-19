# Project-Specific Claude Instructions for LEH (Legal Evidence Hub)

## 🔴 CRITICAL: Role-Based Git Permissions

**Your Role in This Project**: **L (AI / Data)**

### L Role Responsibilities
- AI Worker implementation
- Parser development (STT/OCR)
- RAG/Embedding pipeline
- Data processing logic

---

## ⛔ ABSOLUTE RESTRICTIONS

### 1. Main Branch Access - STRICTLY FORBIDDEN

**YOU MUST NEVER:**
- ❌ `git push origin main` - **ABSOLUTELY PROHIBITED**
- ❌ `git commit` directly on main branch
- ❌ `git checkout main` for making changes
- ❌ Direct merge to main branch

**REASON:**
- L role has **NO PERMISSION** to push to main
- Main branch is **production-ready only**
- Main changes require **P (PM/Frontend) approval** via PR

### 2. Push Approval - ALWAYS ASK USER FIRST

**🚨 CRITICAL RULE (2025-11-19):**
> **NEVER push to GitHub without user approval!**

**YOU MUST ALWAYS:**
- ✅ Ask user: "Push할까요?" before ANY `git push`
- ✅ Wait for explicit user confirmation
- ✅ User decides when to push, not you

**REASON:**
- User wants deliberate, controlled pushes
- Local commits = safe experimentation
- Push = team impact, needs careful timing
- User approval = final safety check

**Example Workflow:**
```
[After local commit]
Claude: "로컬 커밋 완료했습니다. Push할까요?"
User: "아니야, 아직 안 돼" → ❌ Don't push
User: "좋아, push 해줘" → ✅ Proceed with push
```

### 3. Allowed Git Operations

**YOU CAN SAFELY:**
- ✅ `git commit` - Commit locally anytime (no approval needed)
- ✅ `git checkout dev` - Work on dev branch
- ✅ `git checkout -b feat/ai-xxx` - Create feature branches
- ✅ `git merge feat/xxx` into dev - Merge features to dev locally
- ✅ `git push origin dev` - **ONLY after user approval** ⚠️
- ✅ Create PR (dev → main) - **But cannot approve/merge it yourself**

---

## 🌱 Branch Strategy (For L Role)

```text
main  ←  [PR ONLY, P approves]  ←  dev  ←  feat/*
                                    ↑
                                 YOU WORK HERE
```

### 🚨 CRITICAL: Safe Workflow to Prevent Code Conflicts

**LESSON LEARNED (2025-11-19):**
> Never create a feature branch without `git pull origin dev` first!
> Old local dev state can restore previously deleted files and cause conflicts.

---

## ⚠️ Phase 0: Pre-Work Safety Checklist (MANDATORY)

**Execute EVERY TIME before starting new work:**

```bash
# Step 1: Verify current location
git branch
# ✅ Confirm you're on 'dev'
# ❌ If on 'main', STOP and switch to dev

# Step 2: Check for uncommitted changes
git status
# ✅ "nothing to commit, working tree clean"
# ❌ If dirty, commit or stash first

# Step 3: ⚠️ MOST CRITICAL - Always fetch and pull!
git fetch origin
git pull origin dev
# 🔴 NEVER SKIP THIS STEP!
# Even if it says "Already up to date", run it!

# Step 4: Verify you have latest commits
git log --oneline -5
# Check H and P teammates' recent work

# Step 5: NOW create feature branch
git checkout -b feat/your-feature-name

# Step 6: Double-check you're on correct branch
git branch
# ✅ * feat/your-feature-name
```

**Why This Matters:**
- Teammates (H, P) push to dev while you work
- Without `git pull`, your local dev is outdated
- Creating branch from old dev = old deleted code comes back
- Merge conflicts and restored deleted files = BAD! ❌

---

### Daily Workflow for L

1. **Always start from dev with Phase 0 checklist**
   ```bash
   git checkout dev
   git fetch origin        # Check remote state
   git pull origin dev     # ⚠️ NEVER SKIP!
   ```

2. **Work on dev or feature branch**
   ```bash
   # Option 1: Direct on dev
   git checkout dev
   # ... make changes ...
   git add .
   git commit -m "feat: implement xxx"
   git push origin dev

   # Option 2: Feature branch
   git checkout -b feat/ai-parser-v2
   # ... make changes ...
   git checkout dev
   git merge feat/ai-parser-v2
   git push origin dev
   ```

3. **When ready for production**
   - Create PR: dev → main
   - Assign to **P** for review
   - **Wait for P's approval** - DO NOT merge yourself

---

## 🚨 Pre-Commit Safety Check

**Before EVERY git push, verify:**

```bash
# Check current branch
git branch

# Output should show:
# * dev          ✅ SAFE to push
# * feat/xxx     ✅ SAFE to push
# * main         ⛔ DANGER! Do NOT push!
```

**If you see `* main` highlighted:**
1. ⛔ STOP IMMEDIATELY
2. Switch back to dev: `git checkout dev`
3. Never commit/push on main

---

## 📁 Your Working Directories

**Primary work areas for L role:**
- `ai_worker/` - AI Worker Lambda/service code
- `leh-ai-pipeline/` - Previous AI pipeline reference
- `docs/specs/AI_PIPELINE_DESIGN.md` - AI architecture
- `tests/ai_worker/` - AI Worker tests

**Avoid direct changes to:**
- `backend/` - H's responsibility (Backend/Infra)
- `frontend/` - P's responsibility (React dashboard)

---

## 🔄 Collaboration Rules

### With H (Backend)
- Coordinate on API contracts
- H manages: FastAPI, RDS, S3 integration
- L manages: AI Worker, parsers, RAG

### With P (Frontend/PM)
- P is your **PR approver**
- P manages GitHub operations
- Communicate before creating dev → main PR

---

## 🛡️ Safety Guidelines

### Git Safety (Updated 2025-11-19)

#### 🔴 Phase 0: Before Starting Work
1. **ALWAYS git pull origin dev first**: Prevents old code resurrection ⚠️
2. **Never skip git fetch**: Even if "Already up to date" ⚠️
3. **Check teammates' recent commits**: `git log --oneline -5` ✅

#### 🟡 During Work
1. **Use dev for experiments**: dev is your playground ✅
2. **Create feat/* for big changes**: Isolate complex work ✅
3. **Commit frequently**: Small, focused commits ✅

#### 🟢 Before Commit (Triple Check)
```bash
# Step 1: Review ALL changes
git diff
# Read every line - no surprises!

# Step 2: Stage files carefully
git add [specific-files]
# ❌ AVOID: git add .
# ✅ PREFER: git add ai_worker/handler.py src/parser.py

# Step 3: Review staged changes
git diff --staged
# Final check before commit

# Step 4: Commit with clear message
git commit -m "feat: [detailed description]"
```

#### 🔵 Before Push (Final Safety Check)
```bash
# Step 1: Verify current branch (MOST CRITICAL!)
git branch
# ✅ * dev or * feat/xxx
# ❌ * main → STOP IMMEDIATELY!

# Step 2: Check for remote updates
git fetch origin

# Step 3: Pull if needed
git pull origin dev

# Step 4: NOW safe to push
git push origin dev
```

#### ❌ Absolute Don'ts
1. **Never force push to main**: `git push -f origin main` ❌
2. **Never git add . blindly**: Review each file ❌
3. **Never skip git pull before feature branch**: Old code resurrection ❌
4. **Never push to main directly**: L role forbidden ❌

---

### 📝 Local-First Development (로컬 우선 개발)

**핵심 원칙 (2025-11-19):**
> Commit은 자주, Push는 신중하게!
> 로컬에서 충분히 테스트하고, 확신이 생길 때만 GitHub에 올리자.

#### Why Local-First?

**문제상황:**
- 테스트 안 된 코드를 dev에 push → 팀원(H, P) 작업 방해
- 실험적 코드가 remote에 올라감 → 혼란 발생
- 버그 있는 코드 push → 팀 전체 시간 낭비

**해결책:**
- ✅ **로컬 = 실험장**: 마음껏 시도하고 커밋
- ✅ **Remote = 검증된 코드만**: 테스트 통과한 것만 push
- ✅ **커밋 = 세이브 포인트**: 롤백 가능하게 자주 커밋
- ✅ **Push = 팀 공유**: 책임감 있게 공유

---

#### 🔄 Local-First Workflow

```bash
# ========================================
# Phase 1: 작업 시작 (Local)
# ========================================
git checkout dev
git pull origin dev
git checkout -b feat/new-feature  # 또는 dev에서 직접

# ========================================
# Phase 2: 개발 + 로컬 커밋 (반복 가능)
# ========================================

# 첫 번째 시도
# ... 코드 작성 ...
git add ai_worker/parser.py
git commit -m "feat: add initial parser structure"

# 두 번째 시도
# ... 수정 ...
git commit -m "refactor: improve error handling"

# 세 번째 시도
# ... 버그 수정 ...
git commit -m "fix: handle edge case for empty input"

# 🔑 핵심: commit은 자주! 아직 push 안 함!

# ========================================
# Phase 3: 로컬 테스트 (필수!)
# ========================================

# 단위 테스트
pytest tests/test_parser.py

# 전체 테스트
pytest ai_worker/tests/ -v

# 커버리지 체크
pytest --cov=ai_worker --cov-report=term

# 린트 체크 (선택)
flake8 ai_worker/
black --check ai_worker/

# ✅ 모든 테스트 통과 확인!

# ========================================
# Phase 4: Push 전 최종 검증
# ========================================

# 커밋 히스토리 확인
git log --oneline -5

# 변경사항 총정리
git diff origin/dev...HEAD

# 브랜치 확인 (절대 main 아닌지!)
git branch
# ✅ * dev or * feat/xxx

# Remote 상태 확인
git fetch origin
git status

# ========================================
# Phase 5: Push (확신이 생겼을 때만!)
# ========================================

# ✅ 체크리스트:
# - 모든 테스트 통과?
# - 코드 리뷰 (본인)?
# - 팀에 영향 없나?
# - 커밋 메시지 명확한가?

# 이제 push!
git push origin dev
```

---

#### 🧪 Push 전 필수 체크리스트

**절대 push하면 안 되는 경우:**
- ❌ 테스트 실패
- ❌ 린트 에러
- ❌ 실험적/불완전한 코드
- ❌ TODO 주석만 잔뜩
- ❌ 디버깅 print문 남아있음
- ❌ 하드코딩된 테스트 데이터

**Push해도 되는 조건:**
- ✅ 모든 테스트 통과
- ✅ 로컬에서 충분히 검증
- ✅ 코드 리뷰 완료 (본인)
- ✅ 커밋 메시지 명확
- ✅ 팀원에게 영향 최소화

---

#### 🎯 실전 시나리오

**시나리오 1: 새로운 파서 구현**
```bash
# 1. 작업 시작
git checkout dev && git pull origin dev

# 2. 개발 (여러 번 커밋)
# ... BaseParser 구조 작성 ...
git commit -m "feat: add BaseParser abstract class"

# ... ImageParser 구현 ...
git commit -m "feat: implement ImageParser with Vision API"

# ... 버그 수정 ...
git commit -m "fix: handle None response from API"

# 3. 로컬 테스트
pytest tests/test_image_parser.py -v
# ✅ 5 passed

# 4. 확신이 생김! Push
git push origin dev
```

**시나리오 2: 버그 수정 (긴급)**
```bash
# 1. 빠르게 수정
# ... 버그 수정 ...
git commit -m "fix: critical bug in audio parsing"

# 2. 최소 테스트만 빠르게
pytest tests/test_audio_parser.py
# ✅ passed

# 3. 긴급이므로 바로 push (단, 테스트는 필수!)
git push origin dev

# 4. 팀에 알림
# "긴급 버그 수정 push했습니다. 확인 부탁드립니다."
```

**시나리오 3: 실험적 기능 (아직 불확실)**
```bash
# 1. 실험적 시도
# ... 새로운 알고리즘 시도 ...
git commit -m "experiment: try new emotion detection approach"

# 2. 테스트 결과가 애매함
pytest tests/
# ⚠️ Some tests fail, accuracy not good

# 3. ❌ Push 하지 않음!
# 로컬에만 커밋 유지, 계속 실험

# 4. 나중에 개선 후
# ... 알고리즘 개선 ...
git commit -m "refactor: improve emotion detection accuracy"
pytest tests/  # ✅ All passed

# 5. 이제 push
git push origin dev
```

---

#### 💡 유용한 팁

**1. 로컬 커밋 정리하기 (push 전)**
```bash
# 여러 커밋을 하나로 합치기 (squash)
git rebase -i HEAD~3  # 최근 3개 커밋 정리

# 또는 커밋 메시지만 수정
git commit --amend -m "feat: complete image parser implementation"
```

**2. Push 실수 방지**
```bash
# Push 전에 미리 보기
git push --dry-run origin dev

# 강제 push 비활성화 (안전장치)
git config --global push.default simple
```

**3. 로컬 테스트 자동화**
```bash
# .git/hooks/pre-push 생성
#!/bin/bash
echo "🧪 Running tests before push..."
pytest ai_worker/tests/
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Push cancelled."
    exit 1
fi
echo "✅ Tests passed! Proceeding with push."
```

---

#### 🚨 Anti-Patterns (하지 말 것!)

**❌ Bad: 테스트 없이 바로 push**
```bash
# ... 코드 작성 ...
git add . && git commit -m "feat: new feature"
git push origin dev  # ❌ 테스트 안 함!
```

**✅ Good: 테스트 후 push**
```bash
# ... 코드 작성 ...
git commit -m "feat: new feature"
pytest tests/ -v     # ✅ 테스트 먼저!
git push origin dev
```

**❌ Bad: 실험 코드를 바로 push**
```bash
git commit -m "trying something..."
git push origin dev  # ❌ 불확실한 코드 공유
```

**✅ Good: 확신이 생길 때까지 로컬에만**
```bash
git commit -m "experiment: trying new approach"
# ... 여러 번 시도 ...
# ... 테스트 통과 후에만 ...
git push origin dev  # ✅ 검증 완료
```

---

### Code Safety
1. **Test before pushing to dev**: Run local tests
2. **Use pytest for AI Worker**: `pytest ai_worker/tests/`
3. **Document breaking changes**: Inform team in commits
4. **Follow commit conventions**:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `refactor:` - Code restructure
   - `docs:` - Documentation
   - `chore:` - Build/config

---

## 🎯 Quick Reference Commands

### Safe Daily Workflow
```bash
# Morning routine
git checkout dev
git pull origin dev

# Work
# ... code changes ...

# Commit
git add .
git commit -m "feat: implement AI feature xxx"

# Safety check (CRITICAL!)
git branch  # Ensure you're on 'dev' or 'feat/*'

# Push (ONLY if on dev/feat/*)
git push origin dev
```

### Creating Features
```bash
# Start feature
git checkout dev
git pull origin dev
git checkout -b feat/ai-emotion-analysis

# Work on feature
# ... code changes ...

# Merge to dev
git checkout dev
git merge feat/ai-emotion-analysis
git push origin dev

# Clean up
git branch -d feat/ai-emotion-analysis
```

### Creating PR to Main (When Ready for Production)
```bash
# Ensure dev is up to date
git checkout dev
git pull origin dev

# Create PR on GitHub
# dev → main
# Assign: P (for review)
# DO NOT MERGE YOURSELF - Wait for P's approval
```

---

## ⚠️ Emergency Protocol

**If you accidentally pushed to main:**

1. **STOP all git operations**
2. Contact P (PM) immediately
3. P will handle revert/rollback
4. Never attempt force push to fix

**If you're unsure about a git operation:**

1. Check current branch: `git branch`
2. Check what will be pushed: `git log origin/dev..dev`
3. Ask team in chat before pushing
4. Better safe than sorry!

---

## 📝 Commit Message Templates

### Feature Implementation
```
feat: implement GPT-4o Vision emotion analysis

- Add emotion detection for image evidence
- Integrate with OpenAI Vision API
- Store emotion tags in DynamoDB
```

### Bug Fix
```
fix: correct timestamp parsing in STT pipeline

- Fix timezone handling for Whisper output
- Ensure consistent UTC timestamps
- Add test cases for edge cases
```

### Refactoring
```
refactor: unify parser interface across all types

- Create BaseParser abstract class
- Migrate text/image/audio parsers to new interface
- Remove duplicate code in parsing logic
```

---

## 🔍 Self-Check Before Any Git Push

**Ask yourself:**

1. ✅ Am I on `dev` or `feat/*` branch?
2. ✅ Have I tested the code locally?
3. ✅ Is my commit message descriptive?
4. ✅ Did I check `git branch` output?
5. ✅ Am I pushing to dev, not main?

**If ANY answer is NO or uncertain:**
- ⛔ STOP
- Fix the issue
- Re-verify checklist

---

**Remember**: As L role, you are a critical part of the AI pipeline, but main branch access is restricted for production stability. Work freely on dev, communicate with team, and let P handle main branch management.

**Last Updated**: 2025-11-19
**Your Role**: L (AI / Data)
**Branch Access**: dev ✅, feat/* ✅, main ❌
