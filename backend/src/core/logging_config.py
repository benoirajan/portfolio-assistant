"""
Central logging configuration for Portfolio Assistant.
Call setup_logging() once at application startup (main.py).
All modules obtain their logger via: logger = logging.getLogger(__name__)
"""
import logging
import logging.handlers
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "DEBUG") -> None:
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler — stdout logging for Cloud Run, Docker, and terminal
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(console)

    # Rotating file handler — optional, if log directory is writable
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except (OSError, PermissionError):
        pass  # Cloud Run or container environments fallback gracefully to stdout

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore", "urllib3", "yfinance"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("portfolio_assistant").info("Logging initialised — level=%s", level)
