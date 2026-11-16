"""
Global HTTP rate limiter backed by Redis (Upstash) when available,
falling back to in-memory storage for local dev.

Usage in routers:
    from src.core.rate_limit import limiter

    @router.post("/login")
    @limiter.limit("10/minute")
    def login(request: Request, ...):
        ...
"""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.config import settings

logger = logging.getLogger("folioguard.rate_limit")


def _get_storage_uri() -> str | None:
    """Returns Redis URL for rate limit storage, or None for in-memory."""
    if settings.REDIS_URL:
        logger.info("Rate limiter using Redis backend")
        return settings.REDIS_URL
    logger.warning("Rate limiter using in-memory storage (not suitable for multi-process)")
    return None


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_storage_uri(),
    default_limits=["200/minute"],  # Global safety net for all endpoints
)

