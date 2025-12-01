"""
Database session management for SQLAlchemy
Connection pooling and session lifecycle
"""

import os
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
# TODO: Implement actual database connection when RDS is ready
# For now, we'll use an in-memory SQLite for testing
engine = None
SessionLocal = None


def init_db():
    """
    Initialize database engine and session factory
    Should be called during application startup
    """
    global engine, SessionLocal

    try:
        # Priority: environment variable DATABASE_URL > settings.database_url_computed
        # This ensures CI/testing environments can override the URL at runtime
        database_url = os.environ.get("DATABASE_URL") or settings.database_url_computed

        logger.info(f"Initializing database with URL: {database_url.split('@')[0]}@...")

        # PostgreSQL connection args with timeout
        connect_args = {}
        if "sqlite" in database_url:
            connect_args = {"check_same_thread": False}
        else:
            # PostgreSQL: add connection timeout (5 seconds)
            connect_args = {"connect_timeout": 5}

        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_timeout=10,  # Wait max 10s for connection from pool
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
