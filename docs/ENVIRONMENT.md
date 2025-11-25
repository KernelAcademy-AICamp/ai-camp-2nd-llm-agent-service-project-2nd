# Development & Operation Environment Documentation

This document outlines the technical environment, dependencies, and infrastructure for the Legal Evidence Hub (LEH) project.

## 1. Core Technology Stack

### Backend (`/backend`)
- **Language:** Python 3.11+ 
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
- **Language:** Python 3.11+
- **Key Libraries:**
    - `openai`: LLM integration
    - `opensearch-py`: Vector search
    - `boto3`: AWS services (S3, DynamoDB)
    - `ffmpeg-python`: Audio/Video processing
    - `pypdf`: PDF processing

## 2. Infrastructure & Services

### Containerization (Docker)
The project uses Docker for containerization.
- **Orchestration:** `docker-compose.yml` defines the multi-container setup.
- **Services:**
    - `backend`: FastAPI application
    - `frontend`: Next.js application
    - `ai_worker`: Background worker for AI tasks
    - `db`: PostgreSQL database
    - `opensearch`: Vector database (if self-hosted)

### Database
- **Primary DB:** PostgreSQL (Relational Data)
    - Driver: `psycopg2-binary`
    - Migrations: Alembic
- **Vector DB:** OpenSearch (Semantic Search)
- **NoSQL:** DynamoDB (Metadata - optional/hybrid)

### External Services (AWS)
- **S3:** File storage (Evidence files)
- **DynamoDB:** High-throughput metadata (optional)

## 3. Development Environment Setup

### Prerequisites
- Python 3.11+ (권장)
- Node.js 18+
- Docker & Docker Compose
- Git

### Local Setup Steps

1.  **Clone Repository**
    ```bash
    git clone <repo-url>
    cd <repo-name>
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    ```

4.  **Environment Variables**
    - Copy `.env.example` to `.env` in `backend` and `ai_worker`.
    - Configure database URLs and API keys.

5.  **Running Locally**
    - Backend: `uvicorn app.main:app --reload`
    - Frontend: `npm run dev`

## 4. Operational/Production Environment

### Deployment Strategy
- **Containerized Deployment:** All services are built as Docker images.
- **Reverse Proxy:** Nginx (recommended) or cloud load balancer (ALB) in front of Frontend/Backend.
- **CI/CD:** GitHub Actions (recommended) for automated testing and building images.

### Security Considerations
- **Secrets Management:** Use environment variables or AWS Secrets Manager.
- **Network:** Backend and Database should be in private subnets; only Frontend/Load Balancer public.
- **CORS:** Configure strict CORS policies in FastAPI.

## 5. Common Commands

| Component | Command | Description |
|-----------|---------|-------------|
| Frontend | `npm run dev` | Start dev server |
| Frontend | `npm test` | Run tests |
| Backend | `uvicorn app.main:app --reload` | Start dev server |
| Backend | `pytest` | Run tests |
| Docker | `docker-compose up --build` | Start all services |

## 6. Cross-Platform Setup Guide

This project is designed to run on Windows, macOS, and Linux. We recommend using **Docker** for the most consistent experience across all platforms.

### 🪟 Windows
**Recommended:** Use **WSL2 (Windows Subsystem for Linux)**.
1.  **Install WSL2:** Open PowerShell as Administrator and run `wsl --install`. Restart your computer.
2.  **Install Docker Desktop:** Download and install Docker Desktop for Windows. Ensure "Use the WSL 2 based engine" is checked in Settings > General.
3.  **Terminal:** Use the Ubuntu terminal (or your installed distro) for all commands.
4.  **Python:**
    ```bash
    # In WSL terminal
    sudo apt update && sudo apt install python3 python3-venv python3-pip
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 🍎 macOS
1.  **Install Docker Desktop:** Download and install Docker Desktop for Mac (Apple Silicon or Intel).
2.  **Terminal:** Use Terminal or iTerm2.
3.  **Python:**
    ```bash
    # Using Homebrew (recommended)
    brew install python
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 🐧 Linux (Ubuntu/Debian)
1.  **Install Docker Engine:** Follow the official Docker documentation to install Docker Engine and Docker Compose plugin.
    - Add your user to the docker group: `sudo usermod -aG docker $USER` (Log out and back in).
2.  **Python:**
    ```bash
    sudo apt update && sudo apt install python3 python3-venv python3-pip
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### ⚠️ Key Differences to Note
- **File Paths:** Windows uses backslashes (`\`), but inside WSL2, it uses forward slashes (`/`) like Linux/Mac. Always use forward slashes in code and config files.
- **Line Endings (CRLF vs LF):** Git may convert line endings. Configure git to handle this:
    ```bash
    git config --global core.autocrlf input  # Mac/Linux
    git config --global core.autocrlf true   # Windows
    ```
- **Localhost:**
    - On Mac/Linux, `localhost` usually works fine between containers if mapped ports are used.
    - On Windows (WSL2), accessing `localhost` from Windows browsers works, but sometimes networking quirks occur. Docker Desktop handles this well.

