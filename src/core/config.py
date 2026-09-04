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

settings = Settings()
