import json
import logging
from typing import Any, Optional
from src.core.config import settings

logger = logging.getLogger("portfolio_assistant.cache")

_redis_client = None


def _get_client():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Redis connected — %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis unavailable — caching disabled: %s", e)
            _redis_client = False  # sentinel: don't retry on every call
    return _redis_client if _redis_client else None


def get(key: str) -> Optional[Any]:
    client = _get_client()
    if not client:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning("Cache GET failed for key=%s: %s", key, e)
        return None


def set(key: str, value: Any, ttl: int) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning("Cache SET failed for key=%s: %s", key, e)


def delete(key: str) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.delete(key)
    except Exception as e:
        logger.warning("Cache DELETE failed for key=%s: %s", key, e)


def delete_pattern(pattern: str) -> int:
    """Deletes all keys matching a glob pattern. Returns count deleted."""
    client = _get_client()
    if not client:
        return 0
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning("Cache DELETE pattern=%s failed: %s", pattern, e)
        return 0
