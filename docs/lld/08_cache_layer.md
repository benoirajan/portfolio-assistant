# LLD 08 — Redis Cache Layer

**File:** `backend/src/core/cache.py`
**Phase:** Cross-cutting (used from Phase 1 onwards)

---

## Overview

Thin Redis wrapper providing `get / set / delete / delete_pattern` operations with JSON serialisation. Designed to degrade gracefully — if Redis is unavailable the application continues without caching (no crash, no exception propagation).

---

## 1. `backend/src/core/cache.py` — Cache Client

### Connection strategy

- Uses a module-level singleton `_redis_client` initialised lazily on first call.
- Connects via `redis.from_url(settings.REDIS_URL)` — URL comes from the `REDIS_URL` env var (default: `redis://localhost:6379/0`).
- On successful `ping()` the client is stored; on failure the sentinel value `False` is stored so subsequent calls skip the connection attempt entirely (no per-call retry storm).

### Graceful degradation

All public functions check `_get_client()` before acting. If Redis is down:
- `get` returns `None` — callers treat a cache miss and fetch from source.
- `set` / `delete` / `delete_pattern` are no-ops.
- A `WARNING` log is emitted once on connection failure; per-operation failures are also logged at `WARNING` but never raised.

### Public API

| Function | Signature | Description |
|---|---|---|
| `get` | `(key: str) → Any \| None` | Deserialise JSON value for key; `None` on miss or error |
| `set` | `(key: str, value: Any, ttl: int) → None` | Serialise value as JSON and store with TTL (seconds) |
| `delete` | `(key: str) → None` | Remove a single key |
| `delete_pattern` | `(pattern: str) → int` | Remove all keys matching a glob pattern; returns count deleted |

---

## 2. Cache Key Conventions & TTLs

| Data | Key pattern | TTL |
|---|---|---|
| Stock fundamentals (P/E, ROE, sector) | `fundamentals:{symbol}` | 86 400 s (24 h) |
| Market quote / LTP | `quote:{symbol}` | 60 s (1 min) |
| Holdings snapshot | `holdings:{user_id}` | 300 s (5 min) |
| Zerodha access token (AES-encrypted) | `token:{user_id}` | Until 6 AM IST (set dynamically) |
| AI recommendations | `advisory:{user_id}` | 3 600 s (1 h) |

> TTLs are passed by the calling service — `cache.py` itself is TTL-agnostic.

---

## 3. Token Storage Security

The Zerodha `access_token` is **AES-encrypted before being passed to `cache.set`**. The cache layer stores and retrieves the ciphertext as-is; decryption happens in `zerodha_client.py`. The raw token is never written to Redis in plaintext.

---

## 4. Configuration

`REDIS_URL` is read from `backend/src/core/config.py` (`Settings.REDIS_URL`). Default value: `redis://localhost:6379/0`.

```ini
# .env
REDIS_URL=redis://localhost:6379/0
```

For production, use a TLS-enabled URL:

```ini
REDIS_URL=rediss://:password@your-redis-host:6380/0
```

---

## 5. Interaction with Other Services

| Caller | Operation | Key pattern |
|---|---|---|
| `market_data.py` | `get` / `set` | `fundamentals:{symbol}`, `quote:{symbol}` |
| `zerodha_client.py` | `get` / `set` / `delete` | `token:{user_id}` |
| `holdings.py` (router) | `get` / `set` / `delete` | `holdings:{user_id}` |
| `llm_advisor.py` | `get` / `set` | `advisory:{user_id}` |
