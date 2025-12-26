"""
Legal Evidence Hub (LEH) - FastAPI Backend
Main application entry point

Version: 0.2.0
Updated: 2025-11-19
"""

import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

from fastapi import FastAPI, Depends  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from mangum import Mangum  # noqa: E402 - AWS Lambda handler

# Import configuration and middleware
from app.core.config import settings  # noqa: E402

# Import API routers
from app.api import (  # noqa: E402
    auth,
    admin,
    assets,
    billing,
    calendar,
    cases,
    client_portal,
    clients,
    consultation,
    dashboard,
    detective_portal,
    detectives,
    drafts,
    evidence,
    evidence_links,
    fact_summary,
    lawyer_portal,
    lawyer_investigators,
    license,
    messages,
    notifications,
    party,
    precedent,
    procedure,
    properties,
    relationships,
    search,
    settings as settings_router,
    staff_progress,
    summary,
)
from app.api.lssp import router as lssp_router  # noqa: E402 - LSSP v2.01-v2.15
from app.core.dependencies import require_admin  # noqa: E402
from app.middleware import (  # noqa: E402
    register_exception_handlers,
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    AuditLogMiddleware,
    LatencyLoggingMiddleware,
    CorrelationIdMiddleware
)
from app.api import health  # noqa: E402 - Health check router


# ============================================
# Logging Configuration
# ============================================
from app.core.logging_filter import SensitiveDataFilter  # noqa: E402

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply sensitive data filter to root logger
root_logger = logging.getLogger()
root_logger.addFilter(SensitiveDataFilter())


# ============================================
# Sentry SDK Initialization (Error Tracking)
# ============================================
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            environment=settings.APP_ENV,
            release="leh-backend@0.2.0",
            traces_sample_rate=0.1 if settings.APP_ENV in ("prod", "production") else 1.0,
            send_default_pii=False,  # 개인정보 전송 방지
        )
        logger.info("Sentry initialized for environment: %s", settings.APP_ENV)
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logger.error("Failed to initialize Sentry: %s", e)


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
    # Note: AWS services (S3, DynamoDB) currently use mock implementations
    # Note: Qdrant client is initialized on-demand in utils/qdrant.py (in-memory mode for local dev)
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

# 3. Latency Logging Middleware (Logs request duration)
app.add_middleware(LatencyLoggingMiddleware)

# 4. Correlation ID Middleware (Request tracing)
app.add_middleware(CorrelationIdMiddleware)

# 5. Audit Log Middleware (Must be before CORS to log all requests)
app.add_middleware(AuditLogMiddleware)

# 6. CORS (Must be after security headers and audit log)
# Note: For cross-origin cookie authentication, allow_credentials=True is required
# API Gateway also has CORS config - they should match
# Security: Production uses explicit methods/headers, dev uses wildcard for convenience
_cors_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"] if settings.APP_ENV in ("prod", "production") else ["*"]
_cors_headers = ["Content-Type", "Authorization", "Cookie", "X-Request-ID"] if settings.APP_ENV in ("prod", "production") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=_cors_methods,
    allow_headers=_cors_headers,
    expose_headers=["X-Request-ID", "Set-Cookie"]
)

# Note: JWT authentication is handled per-endpoint via get_current_user_id() dependency
# Note: Rate limiting can be added later if needed for production


# ============================================
# Exception Handlers
# ============================================
register_exception_handlers(app)


# ============================================
# Root Endpoint
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
        "health": "/api/health",
        "health_ready": "/api/health/ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================
# Health Check Router (Liveness + Readiness probes)
# ============================================
# Note: Health endpoints use /api prefix for CloudFront routing compatibility
# CloudFront routes /api/* to API Gateway, so health checks must be at /api/health/*
app.include_router(health.router, prefix="/api")


# ============================================
# Router Registration (API Endpoints)
# ============================================
# API 엔드포인트는 app/api/ 디렉토리에 위치 (BACKEND_SERVICE_REPOSITORY_GUIDE.md 기준)
# 모든 API 엔드포인트는 /api prefix를 가짐 (CloudFront 라우팅용)

# API prefix 상수
API_PREFIX = "/api"

# 인증 라우터
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])

# 사건 라우터
app.include_router(cases.router, prefix=f"{API_PREFIX}/cases", tags=["Cases"])

# 재산분할 라우터 (US2 - Asset Division)
app.include_router(assets.router, prefix=f"{API_PREFIX}/cases/{{case_id}}/assets", tags=["Assets"])

# 절차 단계 라우터 (US3 - Procedure Stage Tracking)
app.include_router(procedure.router, prefix=API_PREFIX, tags=["Procedure"])
app.include_router(procedure.deadlines_router, prefix=API_PREFIX, tags=["Procedure"])

# 증거 라우터
app.include_router(evidence.router, prefix=f"{API_PREFIX}/evidence", tags=["Evidence"])

# 초안 라우터 (케이스별 초안 CRUD)
app.include_router(drafts.router, prefix=f"{API_PREFIX}/cases/{{case_id}}/drafts", tags=["Drafts"])

# 변호사/스태프 포털 라우터
app.include_router(lawyer_portal.router, prefix=f"{API_PREFIX}/lawyer", tags=["Lawyer Portal"])
app.include_router(staff_progress.router, prefix=API_PREFIX, tags=["Staff Progress"])

# 의뢰인 관리 라우터 (005-lawyer-portal-pages US2)
app.include_router(clients.router, prefix=API_PREFIX, tags=["Clients"])

# 변호사 탐정 관리 라우터 (005-lawyer-portal-pages US3)
app.include_router(lawyer_investigators.router, prefix=API_PREFIX, tags=["Lawyer Investigators"])

# 의뢰인/탐정 포털 라우터
app.include_router(client_portal.router, prefix=API_PREFIX, tags=["Client Portal"])
app.include_router(detective_portal.router, prefix=API_PREFIX, tags=["Detective Portal"])

# 재산분할 라우터 (Phase 1: Property Division)
app.include_router(properties.router, prefix=API_PREFIX, tags=["Properties"])

# 사용자 설정 라우터
app.include_router(settings_router.router, prefix=API_PREFIX, tags=["Settings"])

# 007-lawyer-portal-v1: Party Graph 라우터
app.include_router(party.router, prefix=API_PREFIX, tags=["Party Graph"])
app.include_router(party.graph_router, prefix=API_PREFIX, tags=["Party Graph"])
app.include_router(relationships.router, prefix=API_PREFIX, tags=["Party Relationships"])

# 007-lawyer-portal-v1: Evidence Links 라우터 (US4)
app.include_router(evidence_links.router, prefix=API_PREFIX, tags=["Evidence Links"])

# 007-lawyer-portal-v1: Global Search 라우터 (US6)
app.include_router(search.router, prefix=API_PREFIX, tags=["Search"])

# 007-lawyer-portal-v1: Dashboard (Today View - US7)
app.include_router(dashboard.router, prefix=API_PREFIX, tags=["Dashboard"])

# 메시지 라우터
app.include_router(messages.router, prefix=f"{API_PREFIX}/messages", tags=["Messages"])

# 청구/결제 라우터
app.include_router(billing.router, prefix=API_PREFIX, tags=["Billing"])
app.include_router(billing.client_router, prefix=API_PREFIX, tags=["Client Billing"])

# Calendar 라우터
app.include_router(calendar.router, prefix=API_PREFIX, tags=["Calendar"])

# Summary 라우터 (US8 - Progress Summary Cards)
app.include_router(summary.router, prefix=API_PREFIX, tags=["Summary"])

# 012-precedent-integration: Precedent Search 라우터 (T023)
app.include_router(precedent.router, prefix=API_PREFIX, tags=["Precedent"])

# 014-case-fact-summary: Fact Summary 라우터 (사건 사실관계 요약)
app.include_router(fact_summary.router, prefix=API_PREFIX, tags=["Fact Summary"])

# Admin 라우터 (User Management & Audit Log)
app.include_router(admin.router, prefix=API_PREFIX, tags=["Admin"])

# License & Code Tracking 라우터 (저작권 및 추적)
app.include_router(license.router, prefix=API_PREFIX, tags=["License & Tracking"])

# Notification 라우터 (Issue #295 - FR-007)
app.include_router(notifications.router, prefix=API_PREFIX, tags=["Notifications"])

# Client/Detective Contact 라우터 (Issue #297, #298 - FR-009~012, FR-015~016)
app.include_router(clients.router, prefix=API_PREFIX, tags=["Client Contacts"])
app.include_router(detectives.router, prefix=API_PREFIX, tags=["Detective Contacts"])

# Consultation 라우터 (Issue #399 - 상담내역)
app.include_router(consultation.router, prefix=API_PREFIX, tags=["Consultations"])

# LSSP 라우터 (Legal Service Standardization Protocol v2.01-v2.15)
app.include_router(lssp_router, prefix=API_PREFIX, tags=["LSSP"])


# Note: Timeline router removed (002-evidence-timeline feature incomplete)
# Draft preview endpoint (POST /cases/{case_id}/draft-preview) remains in cases router
# Note: RAG search is integrated into draft generation service (draft_service.py)


# ============================================
# AWS Lambda Handler (Mangum)
# ============================================
# Lambda handler for API Gateway
handler = Mangum(app, lifespan="off")


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
