import json
import logging
import os
import time
import glob
from typing import Any, Optional
from src.core.config import settings

logger = logging.getLogger("portfolio_assistant.cache")

_redis_client = None
_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cache")

def _ensure_cache_dir():
    if not os.path.exists(_CACHE_DIR):
        os.makedirs(_CACHE_DIR, exist_ok=True)

def _get_client():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Redis connected — %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis unavailable — falling back to local disk cache: %s", e)
            _redis_client = False  # sentinel: don't retry on every call
            _ensure_cache_dir()
    return _redis_client

def _get_file_path(key: str) -> str:
    # safe filename
    safe_key = "".join(c if c.isalnum() else "_" for c in key)
    return os.path.join(_CACHE_DIR, f"{safe_key}.json")


def get(key: str) -> Optional[Any]:
    client = _get_client()
    if client:
        try:
            raw = client.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.warning("Cache GET failed for key=%s: %s", key, e)
            return None
    else:
        # File-based fallback
        try:
            file_path = _get_file_path(key)
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Check TTL
            if "expire_at" in data and data["expire_at"] < time.time():
                os.remove(file_path)
                return None
                
            return data.get("value")
        except Exception as e:
            logger.warning("Disk Cache GET failed for key=%s: %s", key, e)
            return None


def set(key: str, value: Any, ttl: int) -> None:
    client = _get_client()
    if client:
        try:
            client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning("Cache SET failed for key=%s: %s", key, e)
    else:
        try:
            file_path = _get_file_path(key)
            data = {
                "value": value,
                "expire_at": time.time() + ttl
            }
            with open(file_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Disk Cache SET failed for key=%s: %s", key, e)


def delete(key: str) -> None:
    client = _get_client()
    if client:
        try:
            client.delete(key)
        except Exception as e:
            logger.warning("Cache DELETE failed for key=%s: %s", key, e)
    else:
        try:
            file_path = _get_file_path(key)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning("Disk Cache DELETE failed for key=%s: %s", key, e)


def delete_pattern(pattern: str) -> int:
    """Deletes all keys matching a glob pattern. Returns count deleted."""
    client = _get_client()
    if client:
        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("Cache DELETE pattern=%s failed: %s", pattern, e)
            return 0
    else:
        try:
            # simple translation of redis glob pattern to file glob
            safe_pattern = "".join(c if c.isalnum() or c in ("*", "?") else "_" for c in pattern)
            file_pattern = os.path.join(_CACHE_DIR, f"{safe_pattern}.json")
            files = glob.glob(file_pattern)
            count = 0
            for f in files:
                os.remove(f)
                count += 1
            return count
        except Exception as e:
            logger.warning("Disk Cache DELETE pattern=%s failed: %s", pattern, e)
            return 0
