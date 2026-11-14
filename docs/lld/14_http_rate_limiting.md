# Low-Level Design — 14: HTTP Rate Limiting & API Quota Protection

**Module:** HTTP Rate Limiting & Abuse Prevention  
**Phase:** Security Hardening (Audit Category 2 — CRIT-03 & CRIT-04)  
**Files Covered:**
- `backend/requirements.txt`
- `backend/src/core/rate_limit.py`
- `backend/src/main.py`
- `backend/src/api/auth.py`
- `backend/src/api/advisory.py`
- `backend/src/api/analytics.py`
- `backend/tests/test_rate_limiting.py`

---

## 1. Architectural Overview

Prior to this implementation, FolioGuard lacked application-level HTTP rate limiting. This left sensitive authentication and expensive computation endpoints vulnerable to:
1. **OTP Brute-Force & Credential Stuffing:** Unbounded attempts against `/verify-otp`, `/resend-otp`, and `/login`.
2. **AI & Financial API Cost Spikes:** Direct calls to Google Gemini (`/pipeline`, `/stream`), Zerodha KiteConnect, and Yahoo Finance with no request throttling.
3. **Denial-of-Service / Resource Starvation:** CPU-bound portfolio performance computations (XIRR, Sharpe, Sortino) could be repeatedly triggered.

The rate limiting infrastructure introduces a centralized `slowapi` limiter backed by Redis (with graceful in-memory fallback) and explicit AI quota gating on multi-stage Gemini AI advisory endpoints.

```mermaid
graph TD
    Client["Incoming Client Request"] --> Gateway["FastAPI Gateway (src/main.py)"]
    Gateway --> Middleware["slowapi Rate Limiter Middleware"]
    
    Middleware --> KeyFunc["Key Function: Client IP (get_remote_address)"]
    KeyFunc --> Storage[("Storage Backend:\nUpstash Redis (Prod) / In-Memory (Dev)")]
    
    Storage --> Evaluation{"Within Rate Limit?"}
    Evaluation -->|Yes| RouteHandler["Execute Route Logic:\n- Auth Endpoints (/login, /verify-otp)\n- Analytics & Compute (/performance)\n- AI Advisory Pipeline (check_and_consume_ai_quota)"]
    Evaluation -->|No| Handler429["Return HTTP 429:\nRateLimitExceeded Handler"]
```

---

## 2. Centralized Rate Limiter (`backend/src/core/rate_limit.py`)

A dedicated module creates a decoupled `limiter` instance, avoiding circular import cycles between `main.py` and API routers:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.config import settings

def _get_storage_uri() -> str | None:
    if settings.REDIS_URL:
        return settings.REDIS_URL
    return None

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_storage_uri(),
    default_limits=["200/minute"],  # Global safety net
)
```

- **Identification Key:** Client IP address via `get_remote_address`.
- **Storage:** Upstash / Local Redis URI via `settings.REDIS_URL`. If unset, defaults to local memory.
- **Global Default:** 200 requests/minute for undeclared routes.

---

## 3. Rate Limit Enforcement Matrix

| Endpoint | Method | Rate Limit | Protection Target |
|---|---|---|---|
| `/api/v1/auth/login` | `POST` | `10/minute` | Credential stuffing / password dictionary attacks |
| `/api/v1/auth/verify-otp` | `POST` | `5/minute` | 6-digit OTP brute-force lockout |
| `/api/v1/auth/resend-otp` | `POST` | `3/minute` | Email delivery throttling / notification spam |
| `/api/v1/auth/register` | `POST` | `5/minute` | Bulk bot registration spam |
| `/api/v1/auth/google` | `POST` | `10/minute` | Google IAM token exchange flooding |
| `/api/v1/advisory/recommendations` | `GET` | `10/minute` | Gemini AI LLM call quota abuse |
| `/api/v1/advisory/pipeline` | `GET` | `5/minute` | 3-stage heavy pipeline execution abuse |
| `/api/v1/advisory/stream` | `GET` | `5/minute` | Persistent SSE connection flood |
| `/api/v1/analytics/performance` | `GET` | `10/minute` | CPU-intensive XIRR / Sharpe computation |

---

## 4. Advisory Quota Enforcement & Route Gating Architecture

Endpoints in `backend/src/api/advisory.py` are partitioned into two distinct categories based on whether they invoke Google Gemini LLM:

1. **Rule-Based Advisory (`GET /api/v1/advisory/recommendations`):**
   - Evaluates portfolio constraints deterministically via `evaluate_rules` and `_rule_based_recommendations` (`source: "rule_engine"`).
   - Does **not** invoke Google Gemini or consume AI tokens.
   - Protected against abuse using standard authentication (`get_current_user`) and HTTP rate limiting (`@limiter.limit("10/minute")`). It does **not** consume user monthly AI quota.

2. **3-Stage Gemini AI Advisory Pipeline (`GET /pipeline` & `GET /stream`):**
   - Executes multi-stage LLM generation (Stage 1 Diagnosis, Stage 2 Opportunity Screening, Stage 3 Bounded Execution Decision).
   - Injects `check_and_consume_ai_quota` to enforce monthly entitlement quotas (FREE: 3/mo, PRO: 50/mo, ELITE: unlimited) via Redis.

---

## 5. Verification & Testing

Tests are housed in `backend/tests/test_rate_limiting.py`:
- `test_rate_limiter_exceeded_returns_429`: Verifies hitting `/resend-otp` 4 times in 1 minute triggers HTTP 429 `Rate limit exceeded`.
- `test_advisory_recommendations_uses_auth_without_consuming_ai_quota`: Introspects the route dependencies of `/recommendations` to assert `get_current_user` is attached and `check_and_consume_ai_quota` is strictly excluded.
- `test_advisory_pipeline_enforces_ai_quota_gate`: Introspects `/advisory/pipeline` and `/advisory/stream` to assert `check_and_consume_ai_quota` is strictly attached.

