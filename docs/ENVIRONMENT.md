# Development & Operation Environment Documentation

This document outlines the technical environment, dependencies, and infrastructure for the Legal Evidence Hub (LEH) project.

**Last Updated:** 2025-12-01

---

## 1. Core Technology Stack

### Backend (`/backend`)
- **Language:** Python 3.12+
- **Framework:** FastAPI (>=0.110)
- **Server:** Uvicorn (ASGI)
- **Database ORM:** SQLAlchemy 2.0+
- **Authentication:** JWT (python-jose), Password Hashing (passlib + bcrypt)
- **Validation:** Pydantic V2
- **Testing:** Pytest

### Frontend (`/frontend`)
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **UI Library:** React 18
- **Styling:** Tailwind CSS 3.4
- **State Management:** Zustand, TanStack Query
- **Testing:** Jest, React Testing Library

### AI Worker (`/ai_worker`)
- **Language:** Python 3.12+
- **Key Libraries:**
    - `openai`: LLM integration
    - `qdrant-client`: Vector search
    - `boto3`: AWS services (S3, DynamoDB)
    - `ffmpeg-python`: Audio/Video processing
    - `pypdf`: PDF processing

---

## 2. Infrastructure & Services

### Database
- **Primary DB:** PostgreSQL (Relational Data) or SQLite (Local Dev)
    - Driver: `psycopg2-binary`
    - Migrations: Alembic
- **Vector DB:** Qdrant (Semantic Search)
- **NoSQL:** DynamoDB (Evidence Metadata)

### External Services (AWS)
- **S3:** File storage (Evidence files)
- **DynamoDB:** Evidence metadata storage
- **Lambda:** AI Worker execution (S3 Event triggered)
- **CloudFront:** Frontend CDN

---

## 3. Environment Variables (Unified Configuration)

### 3.1 Unified `.env` Structure

LEH uses a **single unified `.env` file** at the project root. Each service directory has a symlink pointing to this root file:

```
project-root/
├── .env                  # Unified environment variables (actual file)
├── .env.example          # Template for new setups
├── backend/.env          # → symlink to ../.env
├── ai_worker/.env        # → symlink to ../.env
└── frontend/.env         # → symlink to ../.env
```

### 3.2 Setup Instructions

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Symlinks are already configured.** If missing, recreate them:
   ```bash
   ln -sf ../.env backend/.env
   ln -sf ../.env ai_worker/.env
   ln -sf ../.env frontend/.env
   ```

3. **Edit `.env` and fill in your values:**
   - AWS credentials
   - OpenAI API key
   - Database URL
   - Other service configurations

### 3.3 Environment Variable Categories

| Category | Variables | Services |
|----------|-----------|----------|
| **AWS** | `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | All |
| **S3** | `S3_EVIDENCE_BUCKET`, `S3_EVIDENCE_PREFIX` | Backend, AI Worker |
| **DynamoDB** | `DDB_EVIDENCE_TABLE`, `DYNAMODB_TABLE` | Backend, AI Worker |
| **Qdrant** | `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_API_KEY` | Backend, AI Worker |
| **OpenAI** | `OPENAI_API_KEY`, `OPENAI_MODEL_*` | Backend, AI Worker |
| **Database** | `DATABASE_URL` | Backend |
| **Auth** | `JWT_SECRET`, `JWT_ALGORITHM` | Backend |
| **Frontend** | `NEXT_PUBLIC_*` | Frontend |

### 3.4 Variable Naming Conventions

Some variables have different names between services for historical reasons. The unified `.env` includes both:

| Backend | AI Worker | Value |
|---------|-----------|-------|
| `DDB_EVIDENCE_TABLE` | `DYNAMODB_TABLE` | Same value |
| `DDB_CASE_SUMMARY_TABLE` | `DYNAMODB_TABLE_CASE_SUMMARY` | Same value |
| `QDRANT_CASE_INDEX_PREFIX` | `QDRANT_COLLECTION_PREFIX` | Same value |
| `OPENAI_MODEL_CHAT` | `OPENAI_GPT_MODEL` | Same value |

### 3.5 Security Notes

- **NEVER commit `.env` to Git** - it's in `.gitignore`
- Use `.env.example` as a reference template
- For production, use GitHub Actions Secrets/Variables or AWS Secrets Manager
- See [Issue #33](https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/issues/33) for GitHub Actions setup

---

## 4. Development Environment Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Git

### Local Setup Steps

1. **Clone Repository**
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

5. **AI Worker Setup**
   ```bash
   cd ai_worker
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 5. Running Services

### Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
# Available at http://localhost:8000
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev
# Available at http://localhost:3000
```

### AI Worker (Local Testing)
```bash
cd ai_worker
source .venv/bin/activate
python -m handler
```

---

## 6. Common Commands

| Component | Command | Description |
|-----------|---------|-------------|
| Backend | `uvicorn app.main:app --reload` | Start dev server |
| Backend | `pytest` | Run tests |
| Backend | `alembic upgrade head` | Apply DB migrations |
| Frontend | `npm run dev` | Start dev server |
| Frontend | `npm test` | Run tests |
| Frontend | `npm run build` | Production build |
| AI Worker | `pytest` | Run tests |

---

## 7. Production Environment

### Deployment Strategy
- **Backend:** AWS Lambda with Mangum or ECS Fargate
- **Frontend:** S3 + CloudFront static hosting
- **AI Worker:** Lambda (S3 Event triggered)

### CI/CD
- GitHub Actions for automated testing and deployment
- See `.github/workflows/` for pipeline configurations

### Security Considerations
- Use IAM Roles instead of access keys in production
- Enable VPC endpoints for AWS services
- Configure strict CORS policies
- Use HTTPS everywhere

---

## 8. Cross-Platform Notes

### Windows (WSL2 Recommended)
```bash
# In WSL terminal
sudo apt update && sudo apt install python3 python3-venv python3-pip
```

### macOS
```bash
brew install python node
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install python3 python3-venv python3-pip nodejs npm
```

### Line Endings
```bash
# Configure git for your platform
git config --global core.autocrlf input  # Mac/Linux
git config --global core.autocrlf true   # Windows
```
