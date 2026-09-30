import os
import logging
from contextlib import contextmanager
from typing import Generator, Tuple
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.config import settings

logger = logging.getLogger("portfolio_assistant.db")


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy compatibility with psycopg2."""
    if not url:
        return "sqlite:///:memory:"
    # Replace deprecated postgres:// with postgresql+psycopg2://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def create_db_engine(url: str = None) -> Engine:
    """Creates a configured SQLAlchemy Engine."""
    target_url = url or os.getenv("DATABASE_URL") or settings.DATABASE_URL
    is_testing = os.getenv("TESTING", "false").lower() in ("true", "1", "t")

    if is_testing or not target_url:
        target_url = "sqlite:///:memory:"

    normalized_url = _normalize_database_url(target_url)

    engine_kwargs = {
        "echo": settings.DB_ECHO,
    }

    if normalized_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL settings for cloud environments (Supabase / Neon)
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    try:
        eng = create_engine(normalized_url, **engine_kwargs)
        return eng
    except Exception as e:
        logger.error("Failed to create engine for %s: %s. Falling back to SQLite.", normalized_url, e)
        return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def bind_engine(new_engine: Engine):
    """Rebinds SessionLocal to a new engine (useful for testing)."""
    global engine, SessionLocal
    engine = new_engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for standalone repository and service operations."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, str]:
    """Tests connectivity to the database and returns status and detail."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "connected"
    except Exception as e:
        logger.warning("Database health check failed: %s", e)
        return False, str(e)
