"""
법률 자동화 시스템 설정 관리
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 프로젝트 정보
    PROJECT_NAME: str = "Legal Automation System"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "AI 기반 법률 문서 자동화 시스템"
    API_V1_PREFIX: str = "/api/v1"

    # 환경 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # 보안
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 데이터베이스
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/legal_db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Vector Database (Pinecone)
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENV", "us-east-1")
    PINECONE_INDEX_NAME: str = "legal-documents"

    # LLM API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # LLM 설정
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_TEMPERATURE: float = 0.3  # 법률 문서는 낮은 temperature
    LLM_MAX_TOKENS: int = 4000

    # OCR 설정
    OCR_ENGINE: str = "tesseract"  # tesseract, easyocr
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    OCR_LANGUAGES: List[str] = ["kor", "eng"]

    # 크롤링 설정
    LAW_CRAWLER_BASE_URL: str = "https://www.law.go.kr"
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    CRAWLER_DELAY: int = 1  # 초

    # 파일 업로드
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".hwp", ".jpg", ".png"]
    UPLOAD_DIR: str = "data/uploads"
    DOCUMENT_OUTPUT_DIR: str = "data/documents"

    # 템플릿 설정
    TEMPLATE_DIR: str = "data/templates"
    DEFAULT_TEMPLATE_LANGUAGE: str = "korean"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://localhost:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000"
    ]

    # 로깅
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/legal_system.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"

    # 캐싱
    CACHE_TTL: int = 3600  # 1시간
    CACHE_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # 법률 데이터 설정
    LAW_DB_UPDATE_INTERVAL: int = 86400  # 24시간마다 업데이트
    LAW_CATEGORIES: List[str] = [
        "민법", "형법", "상법", "민사소송법", "형사소송법",
        "근로기준법", "건축법", "도로교통법", "개인정보보호법"
    ]

    # 문서 생성 설정
    DOCUMENT_FORMATS: List[str] = ["pdf", "docx", "hwp", "html"]
    DEFAULT_DOCUMENT_FORMAT: str = "pdf"
    DOCUMENT_WATERMARK: bool = True
    DOCUMENT_ENCRYPTION: bool = True

    # 리스크 분석 설정
    RISK_ANALYSIS_ENABLED: bool = True
    RISK_THRESHOLD_HIGH: float = 0.8
    RISK_THRESHOLD_MEDIUM: float = 0.5
    RISK_THRESHOLD_LOW: float = 0.3

    # 세션 관리
    SESSION_TIMEOUT: int = 3600  # 1시간
    MAX_SESSIONS_PER_USER: int = 5

    # 결제 설정 (향후 확장용)
    PAYMENT_ENABLED: bool = False
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    SUBSCRIPTION_PLANS: dict = {
        "basic": {"price": 50000, "documents": 10},
        "pro": {"price": 150000, "documents": 50},
        "enterprise": {"price": 500000, "documents": -1}  # unlimited
    }

    # 이메일 설정
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = 587
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = "legal-system@example.com"

    # 모니터링
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    PROMETHEUS_ENABLED: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스
settings = Settings()