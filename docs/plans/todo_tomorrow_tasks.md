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


### 3. 💳 SaaS Monetization, Tier Gating & Payment Strategy (Priority: P1 - Monetization)
* **Architectural Rationale:** Commercial sustainability and API cost control. Advanced features (unlimited Gemini AI multi-stage advisory, automated tax-loss harvesting, 1-click execution) incur compute and LLM token costs. Gating these behind a freemium model with payment processing ensures viable unit economics.
* **Objective:** Set up tiered monetization, subscription management, payment processing, and usage quotas.
* **Details:**
  * Define subscription tiers: **Free** (rule-based advisory, 1 broker, 3 AI runs/mo), **Pro** (₹299/mo: 50 AI reviews, tax harvesting, multi-broker), and **Elite** (₹799/mo: unlimited AI, priority alerts).
  * Integrate Razorpay Subscriptions / UPI Autopay API and webhook handlers for recurring billing and automatic tier upgrades.
  * Implement FastAPI entitlement middleware (`@require_tier`) to protect premium endpoints.
  * Implement a Redis-backed sliding-window quota rate limiter to cap Gemini LLM consumption per user tier.

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
