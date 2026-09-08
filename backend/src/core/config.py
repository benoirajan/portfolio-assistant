import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings:
    KITE_API_KEY: str = os.getenv("KITE_API_KEY", "")
    KITE_API_SECRET: str = os.getenv("KITE_API_SECRET", "")
    KITE_REDIRECT_URL: str = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:8000/api/v1/auth/callback")
    ZERODHA_ENCTOKEN: str = os.getenv("ZERODHA_ENCTOKEN", os.getenv("ENCTOKEN", os.getenv("KITE_ENCTOKEN", "")))
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "t")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    # Phase 3 — LLM Advisory
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "ollama"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    # Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    HOLDINGS_CACHE_TTL: int = int(os.getenv("HOLDINGS_CACHE_TTL", "300"))   # 5 min
    ADVISORY_CACHE_TTL: int = int(os.getenv("ADVISORY_CACHE_TTL", "1800"))  # 30 min

settings = Settings()
