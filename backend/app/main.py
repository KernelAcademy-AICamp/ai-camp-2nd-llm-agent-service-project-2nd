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
    HTTPSRedirectMiddleware
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

    # TODO: Initialize database connection pool
    # TODO: Test AWS service connections (S3, DynamoDB, OpenSearch)
    # TODO: Initialize OpenAI client
    # TODO: Load any required ML models or embeddings

    logger.info("✅ Startup complete")

    yield  # Application runs here

    # Shutdown
    logger.info("👋 Legal Evidence Hub API shutting down...")
    # TODO: Close database connections
    # TODO: Clean up any background tasks
    # TODO: Flush logs

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

# 3. CORS (Must be after security headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# TODO: Add JWT authentication middleware (after auth system is implemented)
# TODO: Add Audit Log middleware (after database is connected)
# TODO: Add Rate Limiting middleware (optional, for production)


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

# 사건 라우터
from app.api import cases
app.include_router(cases.router, prefix="/cases", tags=["Cases"])

# 증거 라우터
from app.api import evidence
app.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])

# TODO: Draft 라우터
# from app.api import draft
# app.include_router(draft.router, prefix="/draft", tags=["Draft"])

# TODO: 검색 라우터 (RAG 기반)
# from app.api import search
# app.include_router(search.router, prefix="/search", tags=["Search"])


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
