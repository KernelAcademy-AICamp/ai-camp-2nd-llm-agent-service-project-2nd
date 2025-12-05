# LEH Development Makefile
# Quick setup and development commands

.PHONY: setup setup-backend setup-ai-worker setup-frontend
.PHONY: dev dev-backend dev-frontend
.PHONY: test test-backend test-ai-worker test-frontend
.PHONY: lint clean help

# =============================================================================
# SETUP COMMANDS (Idempotent - safe to run multiple times)
# =============================================================================

## Install all dependencies for all services
setup: setup-backend setup-ai-worker setup-frontend
	@echo "All services set up successfully!"

## Setup Backend (FastAPI) - skips if venv exists
setup-backend:
	@echo "Setting up Backend..."
	@if [ ! -d "backend/.venv" ]; then \
		cd backend && python3 -m venv .venv; \
	else \
		echo "  Backend venv already exists, skipping creation..."; \
	fi
	cd backend && . .venv/bin/activate && pip install -q -r requirements.txt
	@echo "Backend setup complete!"

## Setup AI Worker (Lambda) - skips if venv exists
setup-ai-worker:
	@echo "Setting up AI Worker..."
	@if [ ! -d "ai_worker/.venv" ]; then \
		cd ai_worker && python3 -m venv .venv; \
	else \
		echo "  AI Worker venv already exists, skipping creation..."; \
	fi
	cd ai_worker && . .venv/bin/activate && pip install -q -r requirements.txt
	@echo "AI Worker setup complete!"

## Setup Frontend (Next.js) - skips if node_modules exists
setup-frontend:
	@echo "Setting up Frontend..."
	@if [ ! -d "frontend/node_modules" ]; then \
		cd frontend && npm install; \
	else \
		echo "  Frontend node_modules already exists, skipping install..."; \
	fi
	@echo "Frontend setup complete!"

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

## Run all services (requires multiple terminals)
dev:
	@echo "Run these commands in separate terminals:"
	@echo "  Terminal 1: make dev-backend"
	@echo "  Terminal 2: make dev-frontend"

## Run Backend development server
dev-backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

## Run Frontend development server
dev-frontend:
	cd frontend && npm run dev

# =============================================================================
# TEST COMMANDS
# =============================================================================

## Run all tests
test: test-backend test-ai-worker test-frontend
	@echo "All tests completed!"

## Run Backend tests
test-backend:
	cd backend && . .venv/bin/activate && pytest

## Run AI Worker tests
test-ai-worker:
	cd ai_worker && . .venv/bin/activate && pytest

## Run Frontend tests
test-frontend:
	cd frontend && npm test

# =============================================================================
# LINT COMMANDS
# =============================================================================

## Run linters on all services
lint:
	cd backend && . .venv/bin/activate && ruff check app/ tests/
	cd ai_worker && . .venv/bin/activate && ruff check src/ tests/
	cd frontend && npm run lint

# =============================================================================
# CLEANUP COMMANDS
# =============================================================================

## Clean up virtual environments and node_modules
clean:
	rm -rf backend/.venv
	rm -rf ai_worker/.venv
	rm -rf frontend/node_modules
	rm -rf backend/test.db
	@echo "Cleanup complete!"

# =============================================================================
# HELP
# =============================================================================

## Show this help message
help:
	@echo "LEH Development Commands"
	@echo "========================"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Install all dependencies"
	@echo "  make setup-backend   - Setup Backend only"
	@echo "  make setup-ai-worker - Setup AI Worker only"
	@echo "  make setup-frontend  - Setup Frontend only"
	@echo ""
	@echo "Development:"
	@echo "  make dev-backend     - Run Backend server"
	@echo "  make dev-frontend    - Run Frontend server"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-backend    - Run Backend tests"
	@echo "  make test-ai-worker  - Run AI Worker tests"
	@echo "  make test-frontend   - Run Frontend tests"
	@echo ""
	@echo "Other:"
	@echo "  make lint            - Run linters"
	@echo "  make clean           - Remove venvs and node_modules"
