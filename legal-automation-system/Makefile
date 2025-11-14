# Makefile for Legal Automation System

.PHONY: help install dev prod test clean docker-up docker-down migrate crawl

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.dev.yml

# Default target
help:
	@echo "Legal Automation System - Available Commands:"
	@echo "============================================="
	@echo "  make install       - Install all dependencies"
	@echo "  make dev          - Run development environment"
	@echo "  make prod         - Run production environment"
	@echo "  make test         - Run all tests"
	@echo "  make clean        - Clean temporary files"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make migrate      - Run database migrations"
	@echo "  make crawl        - Crawl legal data"
	@echo "============================================="

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && $(PIP) install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && $(PIP) install -r requirements.txt
	@echo "Installation complete!"

# Development environment
dev:
	@echo "Starting development environment..."
	$(DOCKER_COMPOSE_DEV) up -d postgres redis
	@echo "Waiting for database..."
	sleep 5
	@echo "Running migrations..."
	cd backend && alembic upgrade head
	@echo "Starting backend server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend server..."
	cd frontend && streamlit run app.py --server.port 8501 &
	@echo "Development environment is running!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	@echo "API Docs: http://localhost:8000/docs"

# Production environment
prod:
	@echo "Starting production environment..."
	$(DOCKER_COMPOSE) up -d
	@echo "Production environment is running!"
	@echo "Application: http://localhost"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v --cov=app --cov-report=html
	@echo "Test results available in backend/htmlcov/index.html"

# Run specific test categories
test-unit:
	cd backend && pytest tests/ -m unit -v

test-integration:
	cd backend && pytest tests/ -m integration -v

test-e2e:
	cd backend && pytest tests/ -m e2e -v

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

# Docker commands
docker-up:
	$(DOCKER_COMPOSE) up -d
	@echo "Docker containers started!"

docker-down:
	$(DOCKER_COMPOSE) down
	@echo "Docker containers stopped!"

docker-build:
	$(DOCKER_COMPOSE) build --no-cache
	@echo "Docker images rebuilt!"

docker-logs:
	$(DOCKER_COMPOSE) logs -f

# Database commands
migrate:
	cd backend && alembic upgrade head
	@echo "Database migrations complete!"

migrate-create:
	@read -p "Enter migration name: " name; \
	cd backend && alembic revision --autogenerate -m "$$name"

db-reset:
	cd backend && alembic downgrade base && alembic upgrade head
	@echo "Database reset complete!"

# Data management
crawl:
	cd backend && $(PYTHON) scripts/crawl_laws.py
	@echo "Law crawling complete!"

load-templates:
	cd backend && $(PYTHON) scripts/init_templates.py
	@echo "Templates loaded!"

build-vectors:
	cd backend && $(PYTHON) scripts/build_vectors.py
	@echo "Vector database built!"

# Utility commands
format:
	@echo "Formatting Python code..."
	black backend/ frontend/ --line-length 100
	isort backend/ frontend/
	@echo "Code formatting complete!"

lint:
	@echo "Linting Python code..."
	flake8 backend/ frontend/
	mypy backend/
	@echo "Linting complete!"

security-check:
	@echo "Running security checks..."
	bandit -r backend/app/
	safety check
	@echo "Security check complete!"

# Environment setup
env-setup:
	cp .env.example .env
	@echo "Environment file created. Please edit .env with your configuration."

# Quick start for new developers
quickstart: env-setup install migrate load-templates
	@echo "Quick start complete! Edit .env file and run 'make dev' to start."

# Monitoring
logs-backend:
	docker logs legal-backend -f

logs-frontend:
	docker logs legal-frontend -f

logs-db:
	docker logs legal-postgres -f

# Backup and restore
backup:
	@echo "Creating backup..."
	docker exec legal-postgres pg_dump -U legal_user legal_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created!"

restore:
	@read -p "Enter backup file name: " file; \
	docker exec -i legal-postgres psql -U legal_user legal_db < $$file
	@echo "Restore complete!"

# Health check
health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health | jq '.' || echo "Backend not responding"
	@curl -s http://localhost:8501 > /dev/null && echo "Frontend: OK" || echo "Frontend not responding"
	@docker exec legal-postgres pg_isready -U legal_user && echo "Database: OK" || echo "Database not responding"
	@docker exec legal-redis redis-cli ping > /dev/null && echo "Redis: OK" || echo "Redis not responding"

# Performance testing
perf-test:
	@echo "Running performance tests..."
	cd backend && locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Documentation
docs:
	@echo "Generating API documentation..."
	cd backend && python -m mkdocs build
	@echo "Documentation available in backend/site/"

docs-serve:
	cd backend && python -m mkdocs serve

# CI/CD helpers
ci-test:
	@make lint
	@make security-check
	@make test

ci-build:
	@make docker-build
	@docker tag legal-backend:latest legal-backend:$(shell git rev-parse --short HEAD)
	@docker tag legal-frontend:latest legal-frontend:$(shell git rev-parse --short HEAD)