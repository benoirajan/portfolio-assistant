# Low-Level Design — 11: SaaS Monetization & Tier Gating

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
- Evaluates key `usage:gemini:{user_id}:{YYYY_MM}` in Redis.
- Free tier limit: 3/mo; Pro: 50/mo; Elite: unlimited (999,999/mo).
- Automatically increments counter via Redis atomic operations.
- Raises `HTTPException(status_code=429, detail="Monthly AI Advisory quota exceeded")` if limit reached.

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

Unit and integration tests are located in `backend/tests/test_billing.py` (16 tests):
- `test_get_plans`: Verifies tier prices and entitlement specs.
- `test_create_order_mock`: Verifies mock order ID generation.
- `test_verify_payment_upgrades_user`: Verifies tier elevation to PRO/ELITE upon valid signature.
- `test_quota_limits`: Verifies rate limiter enforcement and 429 response upon exhaustion.
- `test_require_tier_gate`: Verifies 403 Forbidden for insufficient subscription tier.
