# Branch Protection Setup Guide

## Overview

This guide documents the required branch protection rules for the LEH repository to enforce the workflow defined in CLAUDE.md.

**Critical Rule**: "NEVER push directly to main or dev branches"

## Required Protection Rules

### 1. `main` Branch (Production)

Navigate to: **Settings** > **Branches** > **Add branch protection rule**

**Branch name pattern**: `main`

**Required settings**:

- [x] **Require a pull request before merging**
  - [x] Require approvals: `1`
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Required status checks:
    - `Frontend (Lint, Test, Build)`
    - `Backend (Lint, Test)`
    - `AI Worker (Lint, Test)`

- [x] **Require conversation resolution before merging**

- [x] **Do not allow bypassing the above settings**
  - This prevents even admins from pushing directly

- [ ] **Require signed commits** (Optional, recommended for production)

- [x] **Restrict who can push to matching branches**
  - No direct pushes allowed (only via PR merge)

### 2. `dev` Branch (Staging)

Navigate to: **Settings** > **Branches** > **Add branch protection rule**

**Branch name pattern**: `dev`

**Required settings**:

- [x] **Require a pull request before merging**
  - [x] Require approvals: `1`
  - [ ] Dismiss stale pull request approvals (optional for dev)

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Required status checks:
    - `Frontend (Lint, Test, Build)`
    - `Backend (Lint, Test)`
    - `AI Worker (Lint, Test)`

- [x] **Do not allow bypassing the above settings**

## Setup Steps (GitHub UI)

### Step 1: Navigate to Branch Settings

```
GitHub Repository → Settings → Branches → Add branch protection rule
```

### Step 2: Configure `main` Branch

1. Enter `main` in "Branch name pattern"
2. Enable all checkboxes as listed above
3. Add required status checks by typing:
   - `Frontend (Lint, Test, Build)`
   - `Backend (Lint, Test)`
   - `AI Worker (Lint, Test)`
4. Click "Create" or "Save changes"

### Step 3: Configure `dev` Branch

1. Click "Add branch protection rule" again
2. Enter `dev` in "Branch name pattern"
3. Enable checkboxes as listed above
4. Add same required status checks
5. Click "Create" or "Save changes"

## Verification

After setup, verify that:

1. **Direct push to main fails**:
   ```bash
   git checkout main
   git commit --allow-empty -m "test"
   git push origin main
   # Should fail with: "protected branch hook declined"
   ```

2. **Direct push to dev fails**:
   ```bash
   git checkout dev
   git commit --allow-empty -m "test"
   git push origin dev
   # Should fail with: "protected branch hook declined"
   ```

3. **PR merge works**:
   - Create branch, push changes
   - Open PR to `dev`
   - Wait for CI to pass
   - Get 1 approval
   - Merge succeeds

## GitHub CLI Alternative

If you prefer CLI:

```bash
# Install GitHub CLI
brew install gh

# Login
gh auth login

# Set branch protection for main
gh api repos/KernelAcademy-AICamp/leh/branches/main/protection \
  --method PUT \
  -f required_status_checks='{"strict":true,"contexts":["Frontend (Lint, Test, Build)","Backend (Lint, Test)","AI Worker (Lint, Test)"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  -f restrictions=null

# Set branch protection for dev
gh api repos/KernelAcademy-AICamp/leh/branches/dev/protection \
  --method PUT \
  -f required_status_checks='{"strict":true,"contexts":["Frontend (Lint, Test, Build)","Backend (Lint, Test)","AI Worker (Lint, Test)"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f restrictions=null
```

## Troubleshooting

### "Status check not found"

If status checks don't appear in the dropdown:
1. Run CI at least once by pushing to a feature branch
2. Open a PR (this triggers the checks)
3. After CI runs, the checks will be available in the dropdown

### "Cannot push to protected branch"

This is expected behavior. Use the proper workflow:
```bash
git checkout -b feat/my-feature
git add . && git commit -m "feat: my changes"
git push origin feat/my-feature
# Then create PR on GitHub
```

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Git workflow rules
- [CONTRIBUTING.md](../../docs/CONTRIBUTING.md) - Contribution guidelines
- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
