<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0

Modified principles: None

Added sections:
- Principle VII: TDD Cycle

Removed sections: None

Templates validated:
- .specify/templates/plan-template.md ✅ (Constitution Check section exists)
- .specify/templates/spec-template.md ✅ (No updates needed)
- .specify/templates/tasks-template.md ✅ (Tests-first guidance already present)

Follow-up TODOs: None
-->

# Legal Evidence Hub (LEH) Constitution

## Core Principles

### I. Evidence Integrity (NON-NEGOTIABLE)

All evidence uploads MUST generate SHA-256 hash stored in audit logs. Chain of Custody MUST be maintained for all evidence files. All CRUD operations MUST be logged in the immutable `audit_logs` table.

**Rationale**: Legal evidence requires cryptographic verification and complete audit trail for court admissibility. Any compromise of evidence integrity invalidates the platform's core value proposition.

### II. Case Isolation (NON-NEGOTIABLE)

Each case MUST have an isolated RAG index using the pattern `case_rag_{case_id}` in Qdrant. Cross-case data queries are FORBIDDEN. On case closure, the Qdrant collection MUST be deleted and DynamoDB records MUST be soft-deleted.

**Rationale**: Divorce cases contain sensitive personal information. Accidental cross-case data leakage could violate attorney-client privilege and privacy regulations (PIPA).

### III. No Auto-Submit (NON-NEGOTIABLE)

AI-generated outputs (drafts, summaries, labels) MUST be presented as "Preview Only". The system MUST NOT auto-submit any AI output to external systems. Lawyers MUST manually review and approve all generated content before any external use.

**Rationale**: Legal liability requires human attorney oversight. AI assistance is advisory only; final document decisions are the attorney's sole responsibility.

### IV. AWS-Only Data Storage

All evidence data MUST remain within AWS infrastructure (S3, DynamoDB, Qdrant on EC2). External storage services (Google Drive, Dropbox, etc.) are FORBIDDEN. All data MUST stay within a single AWS account.

**Rationale**: Centralized AWS storage ensures consistent security controls, audit capabilities, and compliance with data sovereignty requirements.

### V. Clean Architecture

Backend code MUST follow the pattern: Routers → Services → Repositories → DB/External Services. Routers handle HTTP concerns only. Services contain business logic. Repositories handle data persistence. Utils are stateless helpers.

**Rationale**: Separation of concerns enables independent testing, clear dependency flow, and maintainable codebase as the platform grows.

### VI. Branch Protection

Direct pushes to `main` and `dev` branches are FORBIDDEN. All code changes to protected branches MUST go through Pull Requests. Documentation-only changes (*.md files) MAY be pushed directly to main.

**Rationale**: PR-based workflow ensures code review, prevents accidental production deployments, and maintains clear audit trail of changes.

### VII. TDD Cycle

When tests are requested or specified in a feature, tests MUST be written FIRST and MUST FAIL before implementation begins. The Red-Green-Refactor cycle MUST be followed:
1. **Red**: Write a failing test that defines expected behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve code quality while keeping tests green

Test files MUST be committed separately or alongside implementation with clear commit messages indicating TDD phase.

**Rationale**: Test-Driven Development ensures code correctness from inception, prevents regression, documents expected behavior, and produces inherently testable designs. Writing tests first forces developers to think about API contracts and edge cases before implementation.

## Development Constraints

### Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **Storage**: PostgreSQL (RDS), AWS S3, DynamoDB, Qdrant
- **AI**: OpenAI (GPT-4o, Whisper, Vision)
- **CDN**: AWS CloudFront

### Security Requirements

- JWT-based authentication with HTTP-only cookies
- Role-based access control (RBAC) at case level
- S3 presigned URLs for evidence uploads (5-minute expiry)
- Security headers via middleware
- No sensitive data in logs

### Testing Requirements

- Backend: pytest with 80% coverage target for AI Worker
- Frontend: Jest + React Testing Library
- Unit tests for services/repositories with mocked dependencies
- Integration tests for full API endpoints
- E2E tests with Playwright for critical user flows
- TDD cycle MUST be followed when tests are specified in feature requirements

## Collaboration & Branch Strategy

### Branch Hierarchy

```
main ← dev ← feat/*
```

- **main**: Production-ready code, deployed to CloudFront production
- **dev**: Staging integration, deployed to CloudFront staging
- **feat/***: Feature branches for active development

### PR Rules

- Direction: Always `feat/* → dev → main`
- Minimum 1 reviewer required
- Tests MUST pass before merge
- Use PR template from `.github/PULL_REQUEST_TEMPLATE.md`

### Team Responsibilities

| Role | Responsibility |
|:-----|:---------------|
| H (Backend/Infra) | FastAPI, RDS, S3, authentication, deployment |
| L (AI/Data) | AI Worker, STT/OCR, parsers, embeddings, RAG |
| P (Frontend/PM) | Next.js, UX, GitHub operations, PR approval |

## Governance

### Amendment Process

1. Proposed changes MUST be documented with rationale
2. Changes affecting NON-NEGOTIABLE principles require team consensus
3. All amendments MUST update the version and Last Amended date
4. Dependent templates MUST be reviewed for consistency after amendments

### Versioning Policy

- **MAJOR**: Backward incompatible changes to NON-NEGOTIABLE principles
- **MINOR**: New principle or section added, material guidance expansion
- **PATCH**: Clarifications, wording fixes, non-semantic refinements

### Compliance Review

- All PRs MUST verify compliance with Constitution principles
- Code reviews SHOULD reference relevant principles when requesting changes
- Complexity additions MUST be justified against Clean Architecture principle
- Test-related PRs MUST demonstrate TDD cycle compliance when applicable

**Version**: 1.1.0 | **Ratified**: 2025-12-03 | **Last Amended**: 2025-12-04
