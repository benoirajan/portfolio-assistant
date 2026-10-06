import os
import logging
from contextlib import contextmanager
from typing import Generator, Tuple, Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.config import settings
from src.db.base import Base

logger = logging.getLogger("portfolio_assistant.db")


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy compatibility with psycopg2."""
    if not url:
        return "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    # Replace deprecated postgres:// with postgresql+psycopg2://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def create_db_engine(url: Optional[str] = None) -> Engine:
    """Creates a configured SQLAlchemy Engine for production PostgreSQL."""
    target_url = url or os.getenv("DATABASE_URL") or settings.DATABASE_URL
    is_testing = os.getenv("TESTING", "false").lower() in ("true", "1", "t")

    if is_testing and not url and not os.getenv("DATABASE_URL"):
        target_url = "sqlite:///:memory:"

    normalized_url = _normalize_database_url(target_url)

    engine_kwargs = {
        "echo": settings.DB_ECHO,
    }

    if normalized_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Production PostgreSQL connection pool configuration
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    eng = create_engine(normalized_url, **engine_kwargs)
    logger.info("Database engine initialized for: %s", normalized_url.split("@")[-1] if "@" in normalized_url else normalized_url)
    return eng


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def bind_engine(new_engine: Engine):
    """Rebinds SessionLocal to a new engine (for testing environments)."""
    global engine, SessionLocal
    engine = new_engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for repository and service database operations."""
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
