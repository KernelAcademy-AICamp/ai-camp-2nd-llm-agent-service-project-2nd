"""
Legal Evidence Hub (LEH) - Configuration
Environment variables and application settings using Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables
    """

    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = Field(default="legal-evidence-hub", env="APP_NAME")
    APP_ENV: str = Field(default="local", env="APP_ENV")  # local | dev | prod
    APP_DEBUG: bool = Field(default=True, env="APP_DEBUG")

    # ============================================
    # Backend Server Settings
    # ============================================
    BACKEND_HOST: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    BACKEND_PORT: int = Field(default=8000, env="BACKEND_PORT")
    BACKEND_LOG_LEVEL: str = Field(default="INFO", env="BACKEND_LOG_LEVEL")

    # ============================================
    # CORS Settings
    # ============================================
    CORS_ALLOW_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://localhost:3005,http://localhost:5173",
        env="CORS_ALLOW_ORIGINS"
    )
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins as a list"""
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",")]

    # ============================================
    # JWT Settings
    # ============================================
    JWT_SECRET: str = Field(default="CHANGE_ME_IN_PROD", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # ============================================
    # Cookie Settings
    # ============================================
    COOKIE_SECURE: bool = Field(default=False, env="COOKIE_SECURE")  # True in production (HTTPS)
    COOKIE_SAMESITE: str = Field(default="lax", env="COOKIE_SAMESITE")  # lax | strict | none
    COOKIE_DOMAIN: str = Field(default="", env="COOKIE_DOMAIN")  # Empty = current domain

    # ============================================
    # Database Settings (PostgreSQL)
    # ============================================
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="leh_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="leh_db", env="POSTGRES_DB")

    DATABASE_URL: str = Field(default="", env="DATABASE_URL")

    @property
    def database_url_computed(self) -> str:
        """
        Construct database URL from individual components if DATABASE_URL is not set
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ============================================
    # AWS Settings
    # ============================================
    AWS_REGION: str = Field(default="ap-northeast-2", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")

    # ============================================
    # S3 Settings
    # ============================================
    S3_EVIDENCE_BUCKET: str = Field(default="leh-evidence-dev", env="S3_EVIDENCE_BUCKET")
    S3_EVIDENCE_PREFIX: str = Field(default="cases/", env="S3_EVIDENCE_PREFIX")
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = Field(default=300, env="S3_PRESIGNED_URL_EXPIRE_SECONDS")  # 5 minutes max

    # ============================================
    # DynamoDB Settings
    # ============================================
    DDB_EVIDENCE_TABLE: str = Field(default="leh_evidence", env="DDB_EVIDENCE_TABLE")
    DDB_CASE_SUMMARY_TABLE: str = Field(default="leh_case_summary", env="DDB_CASE_SUMMARY_TABLE")

    # ============================================
    # Qdrant Settings (Vector Database for RAG)
    # ============================================
    QDRANT_HOST: str = Field(default="", env="QDRANT_HOST")  # Empty = in-memory mode
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_API_KEY: str = Field(default="", env="QDRANT_API_KEY")
    QDRANT_USE_HTTPS: bool = Field(default=False, env="QDRANT_USE_HTTPS")
    QDRANT_COLLECTION_PREFIX: str = Field(default="case_rag_", env="QDRANT_COLLECTION_PREFIX")
    QDRANT_DEFAULT_TOP_K: int = Field(default=5, env="QDRANT_DEFAULT_TOP_K")

    # ============================================
    # OpenAI / LLM Settings
    # ============================================
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    OPENAI_MODEL_CHAT: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL_CHAT")
    OPENAI_MODEL_EMBEDDING: str = Field(default="text-embedding-3-small", env="OPENAI_MODEL_EMBEDDING")

    LLM_REQUEST_TIMEOUT_SECONDS: int = Field(default=60, env="LLM_REQUEST_TIMEOUT_SECONDS")

    # ============================================
    # Feature Flags
    # ============================================
    FEATURE_DRAFT_PREVIEW_ONLY: bool = Field(default=True, env="FEATURE_DRAFT_PREVIEW_ONLY")
    FEATURE_ENABLE_RAG_SEARCH: bool = Field(default=True, env="FEATURE_ENABLE_RAG_SEARCH")
    FEATURE_ENABLE_TIMELINE_VIEW: bool = Field(default=True, env="FEATURE_ENABLE_TIMELINE_VIEW")

    # ============================================
    # Logging / Monitoring
    # ============================================
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json | text
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields in .env
    }


# ============================================
# Global settings instance
# ============================================
settings = Settings()
