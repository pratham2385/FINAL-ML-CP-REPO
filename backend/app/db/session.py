"""
backend/app/db/session.py
Database engine initialization, connection pooling, and FastAPI session dependency.
"""

from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.app.config import settings
from backend.app.db.base import Base
# Ensure all models are registered with Base.metadata
import backend.app.db.models # noqa: F401
from backend.app.utils.logger import logger

# Create PostgreSQL engine with connection pooling and health-check pinging
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False
)

def init_db(target_engine=None) -> None:
    """Creates all database tables defined in SQLAlchemy metadata."""
    eng = target_engine or engine
    logger.info("Verifying and creating PostgreSQL database schema...")
    Base.metadata.create_all(bind=eng)
    logger.info("Database schema initialized successfully.")

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection(target_engine=None) -> Dict[str, Any]:
    """Tests connectivity to PostgreSQL and returns telemetry status."""
    eng = target_engine or engine
    try:
        with eng.connect() as conn:
            row = conn.execute(text("SELECT current_database(), current_user, version()")).fetchone()
            return {
                "status": "connected",
                "database_name": row[0] if row else "unknown",
                "user": row[1] if row else "unknown",
                "dialect": eng.dialect.name
            }
    except Exception as e:
        logger.warning(f"Database connection check failed: {str(e)}")
        return {
            "status": "disconnected",
            "error": str(e),
            "dialect": eng.dialect.name
        }
