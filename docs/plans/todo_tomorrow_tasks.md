# Action Items & TODO Tasks
## 📋 Upcoming TODO Tasks

### 1. 🗄️ Container-Ready Free Database Persistence (Priority: P0 - Infrastructure & State) — [COMPLETED ✅]
* **Architectural Rationale:** Foundational database layer. Containerized environments (Docker, Railway, Render, Fly.io) are ephemeral; storing portfolio data in local JSON files causes state loss across container restarts and redeployments. A free database (Managed Supabase PostgreSQL with SQLAlchemy 2.0 and Alembic migrations) provides durable, production-ready persistence.
* **Objective:** Replace file-based local storage with a managed cloud relational database (PostgreSQL / Supabase).
* **Implementation Status:**
  * ✅ SQLAlchemy 2.0 declarative base (`src/db/base.py`) & resilient session pool (`src/db/session.py`) with Supabase pooler compatibility.
  * ✅ Core ORM models defined in `src/models/` (`User`, `Portfolio`, `UserHolding`, `UserSession`).
  * ✅ Alembic version-controlled migrations initialized (`alembic/versions/0001_initial_schema.py`).
  * ✅ Refactored `src/services/portfolio_repository.py` to persist and re-hydrate holdings through database queries with self-healing file fallback.
  * ✅ Automated pre-boot testing script `backend/run_dev.sh` and 10 comprehensive tests in `backend/tests/test_portfolio.py`.
  * 📖 Documented in [LLD 09](../lld/09_database_persistence.md).

---

### 2. 🔐 Multi-Tenant Authentication & Session Management (Priority: P0 - Security & Identity) — [COMPLETED ✅]
* **Architectural Rationale:** Security prerequisite for public hosting. Before hosting the application publicly, multi-user isolation is mandatory so that users access only their own portfolios and broker credentials. Sensitive tokens (Zerodha enctoken, API keys) must be encrypted at rest.
* **Objective:** Implement full authentication and user identity across backend and frontend with Google IAM / OAuth 2.0 and JWT.
* **Implementation Status:**
  * ✅ Security engine (`src/core/security.py`) supporting PBKDF2-HMAC-SHA256 password hashing, Fernet AES-256 broker token encryption, HS256 JWT generation, and Google IAM ID token verification via `google-auth`.
  * ✅ FastAPI auth routes in `src/api/auth.py` (`/api/v1/auth/google`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/broker/enctoken`, `/api/v1/auth/broker/status`, `/api/v1/auth/broker/disconnect`).
  * ✅ Strict multi-tenant isolation across `/api/v1/holdings`, `/api/v1/advisory/*`, `/api/v1/analytics/*`, scoping database queries, holdings, and cache keys by `user_id`. (Legacy Demo Mode deprecated).
  * ✅ Next.js AuthContext (`frontend/lib/auth-context.tsx`), Axios Bearer token interceptor (`frontend/lib/api.ts`), interactive Google + Email modal (`AuthModal.tsx`), and dynamic user profile/tier header (`Header.tsx`).
  * ✅ Full test coverage with 28 passing unit & integration tests (`tests/test_auth.py`, `tests/test_security.py`, `tests/test_portfolio.py`) and clean Next.js production build.
  * 📖 Documented in [LLD 10](../lld/10_multi_tenant_auth.md).

---


### 3. 💳 SaaS Monetization, Tier Gating & Payment Strategy (Priority: P1 - Monetization) — [COMPLETED ✅]
* **Architectural Rationale:** Commercial sustainability and API cost control. Advanced features (unlimited Gemini AI multi-stage advisory, automated tax-loss harvesting, 1-click execution) incur compute and LLM token costs. Gating these behind a freemium model with payment processing ensures viable unit economics.
* **Objective:** Set up tiered monetization, subscription management, payment processing, and usage quotas.
* **Implementation Status:**
  * ✅ Subscription tiers defined: **Free** (rule-based advisory, 1 broker, 3 AI runs/mo), **Pro** (₹299/mo: 50 AI reviews, tax harvesting), **Elite** (₹799/mo: unlimited AI, priority alerts).
  * ✅ `Subscription` ORM model (`src/models/subscription.py`) with Razorpay IDs, billing period, webhook idempotency key.
  * ✅ Alembic migration `0002_add_subscriptions_table.py` — adds `subscriptions` table with FK cascade on `users`.
  * ✅ Entitlement middleware (`src/core/entitlements.py`) — `require_tier()` factory and `check_and_consume_ai_quota()` dependency.
  * ✅ Billing API (`src/api/billing.py`) — `/api/v1/billing/plans`, `/create-order`, `/verify-payment`, `/status`, `/quota`, `/webhook`.
  * ✅ Razorpay **mock mode** (`RAZORPAY_MOCK_MODE=true`) — full flow works without a live account; set to `false` once keys are provisioned.
  * ✅ `/api/v1/advisory/pipeline` and `/api/v1/advisory/stream` gated with `check_and_consume_ai_quota`.
  * ✅ `/api/v1/analytics/tax-harvesting` gated with `require_tier("PRO")`.
  * ✅ Next.js `PricingModal.tsx` — three tier cards, mock/live Razorpay checkout, upgrade flow.
  * ✅ `Header.tsx` updated with AI quota pill, Upgrade button, and tier-coloured badge.
  * ✅ `frontend/lib/api.ts` + `types.ts` — billing API client functions and TypeScript interfaces.
  * ✅ 16 unit tests in `backend/tests/test_billing.py`.
  * ⚠️ **Multi-broker entitlement** is a placeholder in `TIER_DEFINITIONS` (see Task 7 below).
  * ⚠️ **Live Razorpay keys** not yet integrated (see Task 6 below).

---

### 4. 📰 Fix Redundancy in News Fetch (Priority: P2 - AI Context Quality)
* **Architectural Rationale:** The Google News RSS fetcher currently duplicates the headline text for each snippet (due to mapping both `title` and `snippet` to the article title), making the LLM prompt unnecessarily repetitive.
* **Objective:** Clean up the news text injection in the AI Advisory prompt.
* **Details:**
  * Refactor the format string in `backend/src/services/llm_advisor.py` where `news_text` is constructed.
  * Remove the duplicate `snippet` injection so the prompt lists only `[Source - Date] Headline`.

---

### 5. 🎨 Update UI Theme System (Priority: P2 - UI/UX)
* **Architectural Rationale:** The frontend theme toggle (the "N" button) should support standard modern web paradigms (Light, Dark, and System preference) for better accessibility and user experience.
* **Objective:** Ensure the Next.js theme provider supports three-way toggling.
* **Details:**
  * Configure `next-themes` (or the equivalent context provider) to recognize and handle `system` preference alongside `light` and `dark`.
  * Update the "N" toggle button component to correctly cycle through these three states or present a dropdown menu.

---

### 6. 💳 Integrate Live Razorpay Keys & Recurring Subscriptions (Priority: P1 - Monetization Follow-up)
* **Architectural Rationale:** Task 3 implemented billing with `RAZORPAY_MOCK_MODE=true`. To take real payments, live Razorpay credentials must be provisioned and the `PricingModal.tsx` Razorpay checkout widget must be verified end-to-end.
* **Objective:** Switch from mock mode to live Razorpay payment processing.
* **Details:**
  * Create a Razorpay account at [dashboard.razorpay.com](https://dashboard.razorpay.com) and obtain `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
  * Set `RAZORPAY_MOCK_MODE=false` in the production `.env` / deployment secrets.
  * Configure the Razorpay webhook URL (pointing to `POST /api/v1/billing/webhook`) in the Razorpay dashboard and set `RAZORPAY_WEBHOOK_SECRET`.
  * Test the full end-to-end payment flow with a Razorpay test card before going live.
  * Optionally migrate from one-time orders to Razorpay Subscriptions for UPI Autopay recurring billing.

---

### 7. 🔗 Multi-Broker Entitlement Support (Priority: P2 - Monetization)
* **Architectural Rationale:** Task 3 defined `PRO` as allowing "multi-broker" connections. Currently only Zerodha is integrated. This task adds the entitlement check as a gating placeholder and implements support for a second broker.
* **Objective:** Allow PRO/ELITE users to connect more than one broker account.
* **Details:**
  * Add a `MAX_BROKER_CONNECTIONS` entitlement check in the broker session management logic (currently `src/api/auth.py` `/broker/enctoken`).
  * FREE users: 1 broker connection. PRO/ELITE: unlimited.
  * Implement a second broker adapter (e.g., Angel One or Groww) as a concrete integration alongside the existing `zerodha_client.py`.
  * The `TIER_DEFINITIONS` list in `src/api/billing.py` already shows "1 broker" for FREE — update once the second broker is implemented.
