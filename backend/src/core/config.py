import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load .env from backend directory or project root
    backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
    root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env)
    elif root_env.exists():
        load_dotenv(dotenv_path=root_env)
    else:
        load_dotenv()
except ImportError:
    pass

class Settings:
    KITE_API_KEY: str = os.getenv("KITE_API_KEY", "")
    KITE_API_SECRET: str = os.getenv("KITE_API_SECRET", "")
    KITE_REDIRECT_URL: str = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:8000/api/v1/auth/callback")
    ZERODHA_ENCTOKEN: str = os.getenv("ZERODHA_ENCTOKEN", os.getenv("ENCTOKEN", os.getenv("KITE_ENCTOKEN", "")))
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "t")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Google IAM & OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Security, JWT & Encryption (Fernet AES-256)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "portfolio-assistant-jwt-secret-key-2026-production-grade")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    ENCRYPTION_SECRET_KEY: str = os.getenv("ENCRYPTION_SECRET_KEY", "vXz7e9K3N4P1Q8R6T2U5W7Y9A1B3C5E7G9I1K3M5O7Q=")  # 32-byte Fernet key

    # Phase 3 — LLM Advisory
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "ollama"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    # Database (Supabase PostgreSQL / Local Postgres)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio_db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "t")
    # Cache (Upstash Redis / Local Redis)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    HOLDINGS_CACHE_TTL: int = int(os.getenv("HOLDINGS_CACHE_TTL", "300"))   # 5 min
    ADVISORY_CACHE_TTL: int = int(os.getenv("ADVISORY_CACHE_TTL", "1800"))  # 30 min

settings = Settings()

