"""
Legal Evidence Hub (LEH) - FastAPI Backend
Main application entry point

Version: 0.2.0
Updated: 2025-11-19
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import configuration and middleware
from app.core.config import settings
from app.middleware import (
    register_exception_handlers,
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    AuditLogMiddleware
)


# ============================================
# Logging Configuration
# ============================================
from app.core.logging_filter import SensitiveDataFilter

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply sensitive data filter to root logger
root_logger = logging.getLogger()
root_logger.addFilter(SensitiveDataFilter())


# ============================================
# Lifespan Context Manager (Startup/Shutdown)
# ============================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Legal Evidence Hub API starting...")
    logger.info("📍 Environment: %s", settings.APP_ENV)
    logger.info("📍 Debug mode: %s", settings.APP_DEBUG)
    logger.info("📍 CORS origins: %s", settings.cors_origins_list)

    # Note: Database connection pool is managed per-request via get_db()
    # Note: AWS services (S3, DynamoDB, OpenSearch) currently use mock implementations
    # Note: OpenAI client is initialized on-demand in utils/openai_client.py

    logger.info("✅ Startup complete")

    yield  # Application runs here

    # Shutdown
    logger.info("👋 Legal Evidence Hub API shutting down...")
    # Note: Database connections and logs are automatically cleaned up by FastAPI/SQLAlchemy

    logger.info("✅ Shutdown complete")


# ============================================
# FastAPI Application Instance
# ============================================
app = FastAPI(
    title="Legal Evidence Hub API",
    description="AI 파라리걸 & 증거 허브 백엔드 API - 이혼 사건 전용 증거 분석 및 초안 생성 시스템",
    version="0.2.0",
    docs_url="/docs" if settings.APP_DEBUG else None,  # Disable in production
    redoc_url="/redoc" if settings.APP_DEBUG else None,  # Disable in production
    lifespan=lifespan,  # Modern lifespan handler (replaces on_event)
    contact={
        "name": "Team H·P·L",
        "url": "https://github.com/ORG/REPO",
    }
)


# ============================================
# Middleware Registration (Order matters!)
# ============================================

# 1. HTTPS Redirect (Production only)
app.add_middleware(HTTPSRedirectMiddleware)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Audit Log Middleware (Must be before CORS to log all requests)
app.add_middleware(AuditLogMiddleware)

# 4. CORS (Must be after security headers and audit log)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Note: JWT authentication is handled per-endpoint via get_current_user_id() dependency
# Note: Rate limiting can be added later if needed for production


# ============================================
# Exception Handlers
# ============================================
register_exception_handlers(app)


# ============================================
# Root & Health Check Endpoints
# ============================================
@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트 - API 정보
    """
    return {
        "service": "Legal Evidence Hub API",
        "version": "0.2.0",
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.APP_DEBUG else "disabled",
        "health": "/health",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    헬스 체크 엔드포인트

    모니터링 시스템 및 로드밸런서가 서버 상태를 확인하기 위해 사용

    API_SPEC.md 기준:
    - 200 OK: 서버 정상 동작
    - 간단한 응답 형식 (에러 처리 불필요)
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "Legal Evidence Hub API",
            "version": "0.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# ============================================
# Router Registration (API Endpoints)
# ============================================
# API 엔드포인트는 app/api/ 디렉토리에 위치 (BACKEND_SERVICE_REPOSITORY_GUIDE.md 기준)

# 인증 라우터
from app.api import auth
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 관리자 라우터
from app.api import admin
app.include_router(admin.router, tags=["Admin"])

# 사건 라우터
from app.api import cases
app.include_router(cases.router, prefix="/cases", tags=["Cases"])

# 증거 라우터
from app.api import evidence
app.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])

# Note: Draft endpoints are integrated into cases router (POST /cases/{case_id}/draft-preview)
# Note: RAG search is integrated into draft generation service (draft_service.py)


# ============================================
# Development Server (직접 실행 시에만)
# ============================================
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.APP_DEBUG,  # Auto-reload in debug mode
        log_level=settings.BACKEND_LOG_LEVEL.lower(),
        access_log=True
    )
