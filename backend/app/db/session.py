"""
Database session management for SQLAlchemy
Connection pooling and session lifecycle
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


# ============================================
# Database Engine & Session Factory
# ============================================

# Create engine with connection pooling
engine = None
SessionLocal = None


def init_db():
    """
    Initialize database engine and session factory
    Should be called during application startup
    """
    global engine, SessionLocal

    try:
        # Use DATABASE_URL from environment (PostgreSQL)
        # Falls back to SQLite only if not configured
        database_url = settings.database_url_computed
        if not database_url:
            database_url = "sqlite:///./leh_local.db"
            logger.warning("DATABASE_URL not set, using SQLite fallback")

        # Log URL without credentials
        log_url = database_url.split('@')[-1] if '@' in database_url else database_url
        logger.info(f"Initializing database: {log_url}")

        connect_args = {}
        if "sqlite" in database_url:
            connect_args = {"check_same_thread": False}

        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=settings.APP_DEBUG
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        # Create tables
        from app.db.models import Base
        Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session

    Yields:
        SQLAlchemy Session

    Usage:
        @router.get("/cases")
        def get_cases(db: Session = Depends(get_db)):
            ...
    """
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
