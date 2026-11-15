s# Low-Level Design — 11: SaaS Monetization & Tier Gating

**Module:** Billing, Subscriptions & Feature Entitlements  
**Phase:** Phase 7 / Monetization  
**Files Covered:**
- `backend/src/models/subscription.py`
- `backend/alembic/versions/0002_add_subscriptions_table.py`
- `backend/src/core/entitlements.py`
- `backend/src/api/billing.py`
- `backend/tests/test_billing.py`
- `frontend/components/pricing/PricingModal.tsx`
- `frontend/components/layout/Header.tsx`
- `frontend/lib/api.ts`, `frontend/lib/types.ts`

---

## 1. Architectural Overview

To control API costs (especially Gemini LLM calls) and build a sustainable SaaS model, the application enforces subscription tiers (`FREE`, `PRO`, `ELITE`). The billing subsystem provides:

1. **Tier Hierarchy & Entitlements:**
   - **FREE:** Standard rule-based rebalancing, 1 broker connection, 3 AI reviews per month.
   - **PRO (₹299/mo):** Advanced analytics, tax-loss harvesting, 50 AI portfolio rebalances per month.
   - **ELITE (₹799/mo):** Priority rebalancing, unlimited AI advisory queries, multi-broker family support.
2. **Payment Processing:** Razorpay Orders API for checkout, webhook event handling, and automated tier elevation upon signature verification.
3. **Mock Mode Support:** Toggleable via `RAZORPAY_MOCK_MODE=true` to allow full end-to-end development testing without live payment gateway credentials.

```
+-----------------------------------------------------------------------------------------+
|                                     Frontend UI                                         |
|  [Header.tsx] Tier Badge & Quota Pill  <--->  [PricingModal.tsx] Razorpay / Mock Modal  |
+-----------------------------------------------------------------------------------------+
                                         │
                                         ▼ (JWT Authenticated REST)
+-----------------------------------------------------------------------------------------+
|                                FastAPI Billing Layer                                    |
|   /api/v1/billing/plans      - Returns tier specs & pricing                             |
|   /api/v1/billing/create-order  - Creates Razorpay order (or mock order)                |
|   /api/v1/billing/verify-payment - Cryptographic signature check & tier update          |
|   /api/v1/billing/status     - Current active subscription & expiration                 |
|   /api/v1/billing/quota      - AI queries consumed vs allowance                         |
|   /api/v1/billing/webhook    - Asynchronous payment event webhook handler               |
+-----------------------------------------------------------------------------------------+
        │                                         │
        ▼                                         ▼
+──────────────────────────+             +─────────────────────────+
| PostgreSQL Persistence   |             | Redis Quota Counter     |
| - subscriptions table    |             | - usage:gemini:{uid}:{M}|
| - users.tier column      |             | - TTL: End of month     |
+──────────────────────────+             +─────────────────────────+
```

---

## 2. Database Schema (`backend/src/models/subscription.py`)

Alembic migration `0002_add_subscriptions_table.py` establishes the `subscriptions` table:

```sql
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL DEFAULT 'FREE',
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_sub_id VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    webhook_event_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX ix_subscriptions_razorpay_order_id ON subscriptions(razorpay_order_id);
```

---

## 3. Entitlement Middleware (`backend/src/core/entitlements.py`)

### A. Tier Gating Factory: `require_tier(minimum_tier)`
Protects endpoints such as `/api/v1/analytics/tax-harvesting` by evaluating `user.tier`:
- If `user_rank < required_rank`, raises `HTTPException(status_code=403, detail="...")` with header `X-Required-Tier`.

### B. AI Quota Consumption: `check_and_consume_ai_quota`
Injected into `/api/v1/advisory/pipeline` and `/api/v1/advisory/stream`:
- Managed directly in **PostgreSQL** on the `users` table (`ai_quota_used` INT, `ai_quota_reset_at` TIMESTAMPTZ) via migration `0004_add_user_ai_quota_tracking`.
- Free tier limit: 3/mo; Pro: 50/mo; Elite: unlimited (999,999/mo).
- Race-condition safety: Evaluated with database row locking (`SELECT ... FOR UPDATE`).
- Anchored 30-Day Window: The first query sets `ai_quota_reset_at = now + 30 days`. Consecutive queries on Day 15 and Day 28 increment `ai_quota_used` but **never extend** `ai_quota_reset_at`, completely preventing sliding-window TTL bugs.
- Natural Expiry: When `now >= ai_quota_reset_at`, `ai_quota_used` resets to 0 and a new 30-day window starts.
- Tier Upgrades: Automatically resets `ai_quota_used = 0` and aligns `ai_quota_reset_at` with `current_period_end`.
- Raises `HTTPException(status_code=429, detail="Monthly AI Advisory quota exceeded")` if limit reached, including response headers:
  - `X-Quota-Limit`: Quota allowance for user tier.
  - `X-Quota-Used`: Quota consumed in current cycle.
  - `X-Quota-Reset`: Remaining seconds until cycle reset.
  - `X-Required-Tier`: Required tier to unlock more runs.

---

## 4. API Endpoints Reference (`backend/src/api/billing.py`)

| Endpoint | Method | Security | Description |
|---|---|---|---|
| `/api/v1/billing/plans` | GET | Public / Bearer | Returns tier pricing and features |
| `/api/v1/billing/create-order` | POST | Bearer JWT | Generates Razorpay order or mock order |
| `/api/v1/billing/verify-payment` | POST | Bearer JWT | Validates HMAC-SHA256 signature and upgrades user tier |
| `/api/v1/billing/status` | GET | Bearer JWT | Returns user subscription status and billing window |
| `/api/v1/billing/quota` | GET | Bearer JWT | Returns used vs total monthly AI queries |
| `/api/v1/billing/webhook` | POST | Secret Header | Razorpay webhook processing with idempotency check |

---

## 5. Verification & Tests

Unit and integration tests are located in `backend/tests/test_billing.py` and `backend/tests/test_entitlements_postgres.py`:
- `test_day_1_initial_query_anchors_30_day_window`: Verifies Day 1 query anchors 30-day window (`ai_quota_used = 1`, `ai_quota_reset_at = now + 30d`).
- `test_day_15_and_day_28_do_not_slide_window`: Asserts consecutive queries increment usage to 2 and 3 without sliding `ai_quota_reset_at`.
- `test_day_29_exhausted_quota_raises_429_with_headers`: Asserts 4th query on FREE plan blocks with HTTP 429 and accurate `X-Quota-Reset` header.
- `test_day_32_natural_window_reset`: Asserts that when clock passes `ai_quota_reset_at`, quota automatically resets to 0 and starts fresh.
- `test_tier_upgrade_resets_quota_and_aligns_window`: Asserts tier upgrade clears usage to 0 and aligns reset date to subscription period end.
- `test_get_ai_quota_endpoint_reflects_postgres_data`: Validates `GET /api/v1/billing/quota` returns usage, limit, remaining, and TTL seconds.
- `test_get_plans`: Verifies tier prices and entitlement specs.
- `test_verify_payment_upgrades_user`: Verifies tier elevation to PRO/ELITE upon valid signature.
- `test_require_tier_gate`: Verifies 403 Forbidden for insufficient subscription tier.
