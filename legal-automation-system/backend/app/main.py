"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1 import api_router
from app.database.session import engine
from app.database.base import Base
from app.services.crawler.update_scheduler import UpdateScheduler

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 스케줄러 인스턴스
scheduler = UpdateScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("Starting Legal Automation System...")

    # 데이터베이스 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 스케줄러 시작
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # 종료 시
    logger.info("Shutting down...")
    scheduler.stop()
    logger.info("Scheduler stopped")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI 기반 법률 문서 자동화 시스템",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Production에서는 구체적인 호스트 지정
)

# API 라우터 포함
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Legal Automation System API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "scheduler": "running" if scheduler.scheduler.running else "stopped"
    }


@app.get("/info")
async def system_info():
    """시스템 정보"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "ocr": True,
            "document_generation": True,
            "risk_analysis": True,
            "law_search": True,
            "compliance_check": True
        },
        "ai_providers": {
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "google": bool(settings.GOOGLE_API_KEY)
        },
        "integrations": {
            "pinecone": bool(settings.PINECONE_API_KEY),
            "law_api": bool(settings.LAW_API_KEY)
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )