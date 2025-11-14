# FastAPI Backend Project

Production-ready FastAPI backend with authentication, database integration, and Docker support.

## 🚀 Features

- **FastAPI** framework for high-performance async API
- **SQLAlchemy** with async support for database operations
- **JWT Authentication** with secure password hashing
- **PostgreSQL** as primary database (with SQLite for development)
- **Redis** for caching (optional)
- **Docker** and Docker Compose for containerization
- **Alembic** for database migrations
- **Pytest** for comprehensive testing
- **Pre-commit hooks** for code quality
- **Type checking** with mypy
- **Code formatting** with Black and isort
- **Linting** with Flake8
- **API documentation** with automatic OpenAPI/Swagger UI

## 📁 Project Structure

```
fastapi-backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core configuration
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI application
├── tests/             # Test suite
├── scripts/           # Utility scripts
├── docs/              # Documentation
├── docker-compose.yml # Docker composition
├── Dockerfile         # Docker image definition
├── requirements.txt   # Python dependencies
├── pyproject.toml     # Project configuration
├── Makefile          # Development commands
└── README.md         # Project documentation
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, can use SQLite for development)
- Redis (optional, for caching)
- Docker and Docker Compose (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fastapi-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   make run
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build and start containers:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop containers:**
   ```bash
   docker-compose down
   ```

## 📚 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔒 Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Register a new user:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password",
    "full_name": "Full Name"
  }'
```

### Login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"
```

### Use the token:
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your-token>"
```

## 🧪 Testing

### Run tests:
```bash
make test
```

### Run tests with coverage:
```bash
make test-cov
```

### Run specific test file:
```bash
pytest tests/test_auth.py -v
```

## 🛠️ Development Commands

The project includes a Makefile with useful commands:

```bash
make help          # Show available commands
make install       # Install dependencies
make dev-install   # Install dev dependencies
make format        # Format code with black and isort
make lint          # Run linting with flake8
make type-check    # Run type checking with mypy
make test          # Run tests
make test-cov      # Run tests with coverage
make clean         # Clean up generated files
make run           # Run the application
make docker-build  # Build Docker image
make docker-up     # Start Docker containers
make docker-down   # Stop Docker containers
```

## 📝 Environment Variables

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: Secret key for JWT encoding
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (optional)
- `PRODUCTION`: Set to `true` for production
- `DEBUG`: Set to `false` for production
- `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed origins

## 🚀 Deployment

### Production Considerations

1. **Security:**
   - Change `SECRET_KEY` to a secure random value
   - Set `PRODUCTION=true` and `DEBUG=false`
   - Configure CORS origins properly
   - Use HTTPS in production

2. **Database:**
   - Use PostgreSQL in production (not SQLite)
   - Set up proper database backups
   - Configure connection pooling

3. **Performance:**
   - Use a production WSGI server (Gunicorn/Uvicorn workers)
   - Configure Redis for caching
   - Set up monitoring and logging

### Example production Docker Compose:

```yaml
version: '3.8'
services:
  app:
    image: fastapi-backend:latest
    environment:
      - PRODUCTION=true
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - "80:8000"
    restart: always
```

## 📜 License

[Add your license here]

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

[Add support information here]