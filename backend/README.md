# LEH Backend

FastAPI backend service for Legal Evidence Hub.

## Requirements

- Python 3.12+
- PostgreSQL (or SQLite for local development)
- AWS credentials (S3, DynamoDB)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Or use the shortcut
python -m app.main
```

## Development Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -k test_auth         # Specific test pattern

# Database migrations
alembic upgrade head        # Apply migrations
alembic downgrade -1        # Rollback one
alembic revision --autogenerate -m "description"
```

## Project Structure

```
backend/
├── app/
│   ├── api/            # Route handlers
│   ├── core/           # Config, security, dependencies
│   ├── db/             # SQLAlchemy models, schemas
│   ├── middleware/     # Security headers, error handlers
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   └── utils/          # Helpers (s3, dynamo, qdrant, openai)
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
└── alembic/            # Database migrations
```

## Environment Variables

Uses unified `.env` file from project root (symlinked to `backend/.env`).

Key variables:
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - JWT signing secret (min 32 chars)
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `S3_EVIDENCE_BUCKET` - S3 bucket for evidence files
- `OPENAI_API_KEY` - OpenAI API key

See `../.env.example` for full list.

## API Documentation

When running locally, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
