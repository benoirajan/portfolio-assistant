# FolioGuard — Pre-Publish Security Audit Report

**Auditor:** Senior Software Engineer Review  
**Date:** 2026-10-30  
**Scope:** Backend (FastAPI/Python) + Frontend (Next.js/TypeScript)  
**Severity Legend:** 🔴 Critical · 🟠 High · 🟡 Medium · 🔵 Low

---

## Executive Summary

FolioGuard has a solid architectural foundation — JWT auth, Fernet AES-256 encryption, per-user quota, and a tier gating module are all _built and correct_. However, **none of the rate-limiting infrastructure is wired to production routes**, **real secrets are committed in `.env`**, and **several premium features are either ungated or trivially bypassable**. Shipping as-is would allow any free-tier user to exhaust your Gemini budget, bypass subscription checks, and expose live API keys.

**18 findings across 5 categories. 4 Critical · 5 High · 5 Medium · 4 Low.**

---

## Category 1 — Secret & Credential Exposure 🔴

### CRIT-01 · Live Secrets Committed to Repository

| Field | Detail |
|---|---|
| **Files** | [`backend/.env`](file:///home/benoi/Projects/Folio_guard/backend/.env), [`frontend/.env`](file:///home/benoi/Projects/Folio_guard/frontend/.env) |
| **Severity** | 🔴 Critical |

**What's exposed in the committed `.env` files:**

| Secret | Status |
|---|---|
| `KITE_API_KEY` / `KITE_API_SECRET` | Live Zerodha credentials |
| `GEMINI_API_KEY` | Live Google AI key |
| `DATABASE_URL` | Full Supabase Postgres URI + password |
| `REDIS_URL` | Full Upstash URI + password |
| `GOOGLE_CLIENT_SECRET` | Live OAuth secret |
| `SMTP_PASSWORD` | Gmail app password |
| `ENCRYPTION_SECRET_KEY` | Fernet AES key (same as hardcoded default) |
| `JWT_SECRET_KEY` | Weak placeholder value |

**Risk:** Anyone with repo access (including any future GitHub push) can impersonate users, drain your Gemini quota, read/modify every user's Supabase database, and decrypt all stored Zerodha enctokens.

4. Change hardcoded fallback defaults in [`config.py` L32–58](file:///home/benoi/Projects/Folio_guard/backend/src/core/config.py#L32-L58) to raise `ValueError` if not set in production:

```python
def _require(name: str) -> str:
    raise ValueError(f"Required env var '{name}' is not set. Refusing to start.")

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or _require("JWT_SECRET_KEY")
ENCRYPTION_SECRET_KEY: str = os.getenv("ENCRYPTION_SECRET_KEY") or _require("ENCRYPTION_SECRET_KEY")
```

---

### CRIT-02 · Hardcoded Fallback Fernet Key in `security.py`

| Field | Detail |
|---|---|
| **File** | [`backend/src/core/security.py` L77](file:///home/benoi/Projects/Folio_guard/backend/src/core/security.py#L77) |
| **Severity** | 🔴 Critical |

```python
# CURRENT — hardcoded fallback used when ENCRYPTION_SECRET_KEY is unset
raw_key = "vXz7e9K3N4P1Q8R6T2U5W7Y9A1B3C5E7G9I1K3M5O7Q="
```

This is the **exact same key** as the `.env` default. Any attacker who reads the source code can decrypt every Zerodha enctoken stored in Supabase.

**Fix:** Remove the hardcoded fallback entirely:

```python
def _get_fernet() -> Fernet:
    raw_key = settings.ENCRYPTION_SECRET_KEY
    if not raw_key:
        raise RuntimeError("ENCRYPTION_SECRET_KEY is required and must not be empty")
    try:
        return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
    except Exception as e:
        raise RuntimeError(f"Invalid ENCRYPTION_SECRET_KEY: {e}")
```

---

## Category 2 — Rate Limiting (Missing Entirely) 🔴

### CRIT-03 · No HTTP Rate Limiting on Any Endpoint

| Field | Detail |
|---|---|
| **Files** | [`main.py`](file:///home/benoi/Projects/Folio_guard/backend/src/main.py), all routers |
| **Severity** | 🔴 Critical |

There is **zero HTTP-level rate limiting** anywhere. This enables:

- **OTP brute-force** — 6-digit OTP = 1,000,000 combinations, no lockout on `/verify-otp` or `/resend-otp`.
- **Login credential stuffing** — `/login` can be hammered without limit.
- **AI cost abuse** — `/recommendations` calls Gemini with no quota gate (see CRIT-04).
- **DDoS amplification** — Each request fans out to Zerodha + Yahoo Finance APIs.

**Fix — Add `slowapi` globally:**

```python
# requirements.txt
slowapi==0.1.9

# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Decorate critical endpoints in `auth.py`:**

```python
from src.main import limiter

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginPayload): ...

@router.post("/verify-otp")
@limiter.limit("5/minute")
def verify_otp(request: Request, payload: VerifyOtpPayload): ...

@router.post("/resend-otp")
@limiter.limit("3/minute")
def resend_otp(request: Request, payload: ResendOtpPayload): ...

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterPayload): ...
```

---

### CRIT-04 · `/advisory/recommendations` Has No AI Quota Gate

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/advisory.py` L36–78](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py#L36-L78) |
| **Severity** | 🔴 Critical |

`/advisory/pipeline` and `/advisory/stream` correctly use `Depends(check_and_consume_ai_quota)`.  
`/advisory/recommendations` uses **only** `Depends(get_current_user)` — **quota gate is completely skipped**.

A FREE user can call `/recommendations` thousands of times, burning your entire Gemini budget.

**Fix (5-minute change):**

```python
# advisory.py — change the dependency on the recommendations endpoint
from src.core.entitlements import check_and_consume_ai_quota

@router.get("/recommendations")
def recommendations(
    ...,
    current_user: User = Depends(check_and_consume_ai_quota)  # was: get_current_user
):
```

---

## Category 3 — Premium Plan Gating Gaps 🟠

### HIGH-01 · Basket & Export Endpoints Are Ungated (PRO Features)

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/advisory.py` L236–392](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py#L236-L392) |
| **Severity** | 🟠 High |

`POST /advisory/basket`, `GET /advisory/zerodha-baskets`, and `POST /advisory/export-zerodha-basket` are documented as PRO features in `billing.py` but all use `Depends(get_current_user)` — **any FREE user can call them freely**.

**Fix:**

```python
from src.core.entitlements import require_tier

@router.post("/basket", response_model=BasketResponse)
def create_basket(
    body: BasketRequest,
    x_enctoken: Optional[str] = Header(None),
    current_user: User = Depends(require_tier("PRO"))  # was: get_current_user
):

@router.get("/zerodha-baskets")
def list_zerodha_baskets(
    x_enctoken: Optional[str] = Header(None),
    current_user: User = Depends(require_tier("PRO"))  # was: get_current_user
):

@router.post("/export-zerodha-basket", response_model=ExportZerodhaBasketResponse)
def export_zerodha_basket(
    body: ExportZerodhaBasketRequest,
    x_enctoken: Optional[str] = Header(None),
    current_user: User = Depends(require_tier("PRO"))  # was: get_current_user
):
```

---

### HIGH-02 · `/advisory/pipeline` Consumed Quota Without Enforcing PRO Tier

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/advisory.py` L81–114](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py#L81-L114) |
| **Severity** | 🟠 High |

`check_and_consume_ai_quota` enforces monthly quota counts but does **not** check that the 3-Stage Pipeline is a PRO-only feature. A FREE user with 3 remaining quota slots can run the most expensive endpoint.

**Fix — Chain both dependencies:**

```python
@router.get("/pipeline")
def multi_stage_pipeline(
    ...,
    _tier_check: User = Depends(require_tier("PRO")),           # gate first
    current_user: User = Depends(check_and_consume_ai_quota),   # then deduct quota
):
```

---

### HIGH-03 · `/analytics/performance` Ungated Despite Expensive Compute

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/analytics.py` L42–78](file:///home/benoi/Projects/Folio_guard/backend/src/api/analytics.py#L42-L78) |
| **Severity** | 🟠 High |

XIRR / Sharpe / Sortino calculations hit Yahoo Finance and are CPU-bound. No rate limit or tier gate. This should either be a PRO feature or rate-limited aggressively.

**Quick fix (add rate limiting):**

```python
@router.get("/performance")
@limiter.limit("10/minute")
def get_portfolio_performance_metrics(request: Request, ...):
```

---

### HIGH-04 · Payment Verification Trusts Client-Supplied `target_tier`

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/billing.py` L292–339](file:///home/benoi/Projects/Folio_guard/backend/src/api/billing.py#L292-L339) |
| **Severity** | 🟠 High |

`RAZORPAY_MOCK_MODE=true` is the **default**. In mock mode, `_verify_razorpay_signature` always returns `True`. The `target_tier` field comes from the **client request body** with no server-side cross-check.

**Exploit:** `POST /api/v1/billing/verify-payment` with `{"target_tier": "ELITE", "razorpay_order_id": "anything", "razorpay_payment_id": "anything", "razorpay_signature": "anything"}` → instant free ELITE upgrade.

**Fix:**

1. Set `RAZORPAY_MOCK_MODE=false` in production.
2. Store `target_tier` server-side at order creation time:

```python
# create_order endpoint — after order is created
cache.set(f"order_tier:{order['id']}", target_tier, ttl=3600)

# verify_payment endpoint — retrieve server-side, never trust client
server_tier = cache.get(f"order_tier:{payload.razorpay_order_id}")
if not server_tier:
    raise HTTPException(400, "Order not found or expired")
target_tier = server_tier  # Override client value
```

---

### HIGH-05 · No Fresh JWT Issued After Tier Upgrade

| Field | Detail |
|---|---|
| **Files** | [`billing.py` L334](file:///home/benoi/Projects/Folio_guard/backend/src/api/billing.py#L334), [`security.py` L111](file:///home/benoi/Projects/Folio_guard/backend/src/core/security.py#L111) |
| **Severity** | 🟠 High |

After upgrading to PRO, the backend upgrades `user.tier` in Postgres but does not return a new JWT. The frontend's cached token still contains `tier: "FREE"` — premium UI gates remain locked until the user re-logs in.

**Fix — Return a fresh access token in the upgrade response:**

```python
# billing.py — verify_payment
from src.core.security import create_access_token

new_token = create_access_token(
    data={"sub": current_user.id, "email": current_user.email, "tier": target_tier}
)
return {
    "status": "success",
    "message": f"Plan upgraded to {target_tier}.",
    "tier": target_tier,
    "access_token": new_token,   # <-- frontend stores this and refreshes
    "mock_mode": settings.RAZORPAY_MOCK_MODE,
}
```

---

## Category 4 — Auth & Session Vulnerabilities 🟡

### MED-01 · OTP Comparison Is Not Constant-Time

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/auth.py` L238](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py#L238) |
| **Severity** | 🟡 Medium |

```python
# Current — timing oracle risk
if not user.verification_otp or user.verification_otp != clean_otp:
```

**Fix:**
```python
import hmac
if not user.verification_otp or not hmac.compare_digest(user.verification_otp, clean_otp):
```

---

### MED-02 · `resend-otp` Leaks User Existence (Enumeration)

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/auth.py` L294–298](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py#L294-L298) |
| **Severity** | 🟡 Medium |

HTTP 404 is returned when the email doesn't exist — enables mass email enumeration.

**Fix:** Always return HTTP 200 with a generic message:

```python
if not user:
    # Don't reveal whether the email is registered
    return {"status": "success", "message": "If this email is registered, a code has been sent."}
```

---

### MED-03 · Zerodha OAuth Callback Is Unauthenticated

| Field | Detail |
|---|---|
| **File** | [`backend/src/api/auth.py` L494–504](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py#L494-L504) |
| **Severity** | 🟡 Medium |

`POST /api/v1/auth/callback` accepts a `request_token` without requiring a logged-in user. Any client can invoke this endpoint and potentially hijack an in-flight OAuth flow.

**Fix:** Require authentication or bind the request_token to a server-side state/nonce generated during `/login-url`:

```python
@router.post("/callback")
def auth_callback(
    payload: CallbackPayload,
    current_user: User = Depends(get_current_user)  # Add auth requirement
):
```

---

### MED-04 · Tokens Stored in `localStorage` (XSS Exposure)

| Field | Detail |
|---|---|
| **File** | [`frontend/lib/auth-context.tsx` L102, L118, L143](file:///home/benoi/Projects/Folio_guard/frontend/lib/auth-context.tsx#L102-L143) |
| **Severity** | 🟡 Medium |

JWT `access_token` and `enctoken` are stored in `localStorage`. Any XSS vulnerability (compromised npm package, reflected XSS) can exfiltrate both tokens, granting full account + Zerodha access.

**Fix:** Migrate to `httpOnly; Secure; SameSite=Strict` cookies set by the backend — JavaScript cannot read these even under XSS.

---

### MED-05 · 24-Hour JWT with No Revocation Mechanism

| Field | Detail |
|---|---|
| **File** | [`backend/src/core/config.py` L34](file:///home/benoi/Projects/Folio_guard/backend/src/core/config.py#L34) |
| **Severity** | 🟡 Medium |

`ACCESS_TOKEN_EXPIRE_MINUTES=1440`. A stolen token is valid for 24 hours with no revocation path.

**Pragmatic fix:** Reduce to 60 minutes. Add a `jti` (JWT ID) claim stored in Redis as a blocklist to enable per-token revocation on logout or compromise.

---

## Category 5 — Infrastructure & Configuration 🔵

### LOW-01 · OpenAPI Docs (`/docs`) Exposed in Production

| File | [`backend/src/main.py` L22–26](file:///home/benoi/Projects/Folio_guard/backend/src/main.py#L22-L26) |
|---|---|
| **Fix** | `app = FastAPI(docs_url="/docs" if settings.DEMO_MODE else None, redoc_url=None)` |

---

### LOW-02 · CORS Defaults to `allow_origins=["*"]`

| File | [`backend/src/main.py` L28–38](file:///home/benoi/Projects/Folio_guard/backend/src/main.py#L28-L38) |
|---|---|
| **Fix** | Always set `ALLOWED_ORIGINS=https://your-app.vercel.app` in production. The fallback `*` should raise on startup if not configured. |

---

### LOW-03 · Quota Fail-Open on Redis Outage

| File | [`backend/src/core/entitlements.py` L95–102](file:///home/benoi/Projects/Folio_guard/backend/src/core/entitlements.py#L95-L102) |
|---|---|
| **Fix** | Intentional design (documented) but consider an in-process request counter as a circuit-breaker fallback to cap at 1 request during Redis outage. |

---

### LOW-04 · `/health` Exposes Internal State Unauthenticated

| File | [`backend/src/main.py` L71–87](file:///home/benoi/Projects/Folio_guard/backend/src/main.py#L71-L87) |
|---|---|
| **Fix** | Require a monitoring token header, or serve a minimal `{"status":"ok"}` response without DB/cache details to anonymous callers. |

---

## Priority Fix Checklist

| Priority | Finding | Files | Est. Effort |
|---|---|---|---|
| 🔴 P0 | Rotate ALL committed secrets | `.env` files | 30 min |
| 🔴 P0 | Remove hardcoded Fernet fallback | [`security.py`](file:///home/benoi/Projects/Folio_guard/backend/src/core/security.py) | 5 min |
| 🔴 P0 | Add `slowapi` rate limiting to auth routes | [`main.py`](file:///home/benoi/Projects/Folio_guard/backend/src/main.py), [`auth.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py) | 2 hrs |
| 🔴 P0 | Gate `/recommendations` with AI quota | [`advisory.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py) | 5 min |
| 🟠 P1 | Gate basket/export with `require_tier("PRO")` | [`advisory.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py) | 10 min |
| 🟠 P1 | Chain tier + quota on `/pipeline` | [`advisory.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/advisory.py) | 5 min |
| 🟠 P1 | Set `RAZORPAY_MOCK_MODE=false` + server-side `target_tier` | [`billing.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/billing.py) | 1 hr |
| 🟠 P1 | Return fresh JWT after upgrade | [`billing.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/billing.py) | 30 min |
| 🟡 P2 | `hmac.compare_digest` for OTP | [`auth.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py) | 2 min |
| 🟡 P2 | Fix user enumeration on `resend-otp` | [`auth.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py) | 5 min |
| 🟡 P2 | Add auth to Zerodha OAuth callback | [`auth.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/auth.py) | 30 min |
| 🟡 P2 | Migrate tokens to `httpOnly` cookies | [`auth-context.tsx`](file:///home/benoi/Projects/Folio_guard/frontend/lib/auth-context.tsx) | 2 hrs |
| 🔵 P3 | Disable `/docs` in production | [`main.py`](file:///home/benoi/Projects/Folio_guard/backend/src/main.py) | 2 min |
| 🔵 P3 | Enforce `ALLOWED_ORIGINS` strictly | [`main.py`](file:///home/benoi/Projects/Folio_guard/backend/src/main.py) | 5 min |
| 🔵 P3 | Rate-limit `/analytics/performance` | [`analytics.py`](file:///home/benoi/Projects/Folio_guard/backend/src/api/analytics.py) | 15 min |
| 🔵 P3 | Reduce JWT expiry to 1 hr + add refresh | [`config.py`](file:///home/benoi/Projects/Folio_guard/backend/src/core/config.py) | 3 hrs |

---

## What Is Already Correct ✅

- ✅ PBKDF2-HMAC-SHA256 password hashing with random 16-byte salt
- ✅ `hmac.compare_digest` for JWT signature verification (no timing oracle)
- ✅ Fernet AES-256 for Zerodha enctoken encryption at rest
- ✅ `require_tier("PRO")` correctly gates `/analytics/tax-harvesting`
- ✅ `check_and_consume_ai_quota` correctly gates `/advisory/pipeline` and `/advisory/stream`
- ✅ Google ID token verified against Google's JWKS (issuer + audience validated)
- ✅ Razorpay webhook signature verified with `hmac.compare_digest`
- ✅ Webhook idempotency via `webhook_event_id` — prevents double-upgrades
- ✅ OTP expiry after 10 minutes
- ✅ Inactive users blocked at `get_current_user` dependency
- ✅ Per-user quota keys scoped by `user_id` — no cross-user leakage

---

*Generated by automated codebase analysis. All file references are clickable. Fixes are production-ready code snippets.*
