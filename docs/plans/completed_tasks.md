# Completed Tasks & Roadmap Archive

This document maintains the historical record of completed engineering tasks, architectural milestones, and bug fixes for the Portfolio Assistant project.

---

## 🗄️ Task 1: Container-Ready Free Database Persistence (Priority: P0 - Infrastructure & State)
* **Status:** Completed ✅
* **Architectural Rationale:** Foundational database layer. Containerized environments (Docker, Railway, Render, Fly.io) are ephemeral; storing portfolio data in local JSON files caused state loss across container restarts and redeployments. Managed Supabase PostgreSQL with SQLAlchemy 2.0 and Alembic migrations provides durable, production-ready persistence.
* **Objective:** Replace file-based local storage with a managed cloud relational database (PostgreSQL / Supabase).
* **Implementation Details:**
  * SQLAlchemy 2.0 declarative base (`backend/src/db/base.py`) & resilient session pool (`backend/src/db/session.py`) compatible with Supabase poolers.
  * Core ORM models defined in `backend/src/models/` (`User`, `Portfolio`, `UserHolding`, `UserSession`).
  * Alembic version-controlled migrations initialized (`backend/alembic/versions/0001_initial_schema.py`).
  * Refactored `backend/src/services/portfolio_repository.py` to persist and re-hydrate holdings via database queries with self-healing file fallback.
  * Automated pre-boot testing script `backend/run_dev.sh` and 10 comprehensive tests in `backend/tests/test_portfolio.py`.
* **Documentation:** Detailed in [LLD 09: Database Persistence](../lld/09_database_persistence.md) and [Phase 6 Plan](./phase_6_multi_tenant_and_universal_ingestion.md).

---

## 🔐 Task 2: Multi-Tenant Authentication & Session Management (Priority: P0 - Security & Identity)
* **Status:** Completed ✅
* **Architectural Rationale:** Security prerequisite for public hosting. Multi-user isolation is mandatory so users access only their own portfolios and broker credentials. Sensitive tokens (Zerodha enctoken, API keys) must be encrypted at rest using AES-256.
* **Objective:** Implement full authentication and user identity across backend and frontend with Google IAM / OAuth 2.0 and JWT.
* **Implementation Details:**
  * Security engine (`backend/src/core/security.py`) supporting PBKDF2-HMAC-SHA256 password hashing, Fernet AES-256 broker token encryption, HS256 JWT generation, and Google IAM ID token verification via `google-auth`.
  * FastAPI auth routes in `backend/src/api/auth.py` (`/api/v1/auth/google`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/broker/enctoken`, `/api/v1/auth/broker/status`, `/api/v1/auth/broker/disconnect`).
  * Strict multi-tenant isolation across `/api/v1/holdings`, `/api/v1/advisory/*`, `/api/v1/analytics/*`, scoping database queries, holdings, and cache keys by `user_id`. (Legacy Demo Mode deprecated).
  * Next.js AuthContext (`frontend/lib/auth-context.tsx`), Axios Bearer token interceptor (`frontend/lib/api.ts`), interactive Google + Email modal (`AuthModal.tsx`), and dynamic user profile/tier header (`Header.tsx`).
  * Full test coverage with 28 passing unit & integration tests (`tests/test_auth.py`, `tests/test_security.py`, `tests/test_portfolio.py`) and clean Next.js production build.
* **Documentation:** Detailed in [LLD 10: Multi-Tenant Auth](../lld/10_multi_tenant_auth.md) and [Phase 6 Plan](./phase_6_multi_tenant_and_universal_ingestion.md).

---

## 💳 Task 3: SaaS Monetization, Tier Gating & Payment Strategy (Priority: P1 - Monetization)
* **Status:** Completed ✅
* **Architectural Rationale:** Commercial sustainability and API cost control. Advanced features (unlimited Gemini AI multi-stage advisory, automated tax-loss harvesting, 1-click execution) incur compute and LLM token costs. Gating these behind a freemium model with payment processing ensures viable unit economics.
* **Objective:** Set up tiered monetization, subscription management, payment processing, and usage quotas.
* **Implementation Details:**
  * Subscription tiers defined: **Free** (rule-based advisory, 1 broker, 3 AI runs/mo), **Pro** (₹299/mo: 50 AI reviews, tax harvesting), **Elite** (₹799/mo: unlimited AI, priority alerts).
  * `Subscription` ORM model (`backend/src/models/subscription.py`) with Razorpay IDs, billing period, and webhook idempotency key.
  * Alembic migration `0002_add_subscriptions_table.py` — adds `subscriptions` table with FK cascade on `users`.
  * Entitlement middleware (`backend/src/core/entitlements.py`) — `require_tier()` factory and `check_and_consume_ai_quota()` dependency with Redis counter.
  * Billing API (`backend/src/api/billing.py`) — `/api/v1/billing/plans`, `/create-order`, `/verify-payment`, `/status`, `/quota`, `/webhook`.
  * Razorpay mock mode (`RAZORPAY_MOCK_MODE=true`) allows full flow validation without live credentials until keys are provisioned.
  * `/api/v1/advisory/pipeline` and `/api/v1/advisory/stream` gated with `check_and_consume_ai_quota`.
  * `/api/v1/analytics/tax-harvesting` gated with `require_tier("PRO")`.
  * Next.js `PricingModal.tsx` — three tier cards, mock/live Razorpay checkout integration, upgrade flow.
  * `Header.tsx` updated with AI quota pill, Upgrade button, and tier-coloured badge.
  * `frontend/lib/api.ts` + `types.ts` — billing API client functions and TypeScript interfaces.
  * 16 unit tests in `backend/tests/test_billing.py`.
* **Documentation:** Detailed in [LLD 11: SaaS Monetization & Billing](../lld/11_saas_monetization.md) and [Phase 7 Plan](./phase_7_monetization_and_saas.md).

---

## 📰 Task 4: Fix Redundancy in News Fetch (Priority: P2 - AI Context Quality)
* **Status:** Completed ✅
* **Architectural Rationale:** The Google News RSS fetcher previously set both `title` and `snippet` to the article headline, causing `backend/src/services/llm_advisor.py` to produce redundant strings like `- [Source - Date] Headline: Headline`. This bloated LLM prompt tokens and degraded context clarity.
* **Objective:** Clean up the news text injection in the Stage 1 AI Advisory prompt.
* **Implementation Details:**
  * Refactored `news_text` format string in `backend/src/services/llm_advisor.py` (`run_stage1_diagnosis`) to `f"- [{item['source']}] {item['title']}"`.
  * Eliminated redundant duplicate snippet text in Stage 1 prompts.
  * Verified with live Google News RSS query and full test suite passing (49 tests).
* **Documentation:** Documented in [LLD 03: AI Advisory (§3)](../lld/03_phase3_ai_advisory.md) and [Prompt Comparison Report](../reports/prompt_comparison.md).

---

## 🎨 Task 5: Three-Way UI Theme System (Light, Dark, and System Preference) (Priority: P2 - UI/UX)
* **Status:** Completed ✅
* **Architectural Rationale:** The frontend theme toggle needed support for modern web paradigms (Light, Dark, and System preference) for better accessibility, ergonomics, and visual polish across different devices and lighting conditions.
* **Objective:** Implement full three-way theme toggling (`light`, `dark`, `system`) with matching icons, zero hydration flicker, and automatic system preference detection.
* **Implementation Details:**
  * Installed and integrated `next-themes` with a React 19 client wrapper `ThemeProvider` in `frontend/components/theme/ThemeProvider.tsx`.
  * Wrapped the root layout tree in `frontend/app/layout.tsx` with `<ThemeProvider attribute="class" defaultTheme="system" enableSystem>`, adding `suppressHydrationWarning` on `<html>`.
  * Updated `frontend/app/globals.css` with Tailwind CSS v4 `@custom-variant dark (&:where(.dark, .dark *))` and cohesive light/dark color palette tokens for `--bg`, `--surface`, `--surface-hover`, `--border`, `--text`, `--muted`, `--blue`, `--green`, `--red`, and `--yellow`.
  * Created `frontend/components/layout/ThemeToggle.tsx` providing a dropdown menu displaying matching Lucide icons:
    * ☀️ **Light:** `Sun` (amber accent)
    * 🌙 **Dark:** `Moon` (indigo accent)
    * 💻 **System:** `Monitor` (sky accent)
  * Mounted guard prevents hydration mismatch, and active choice is highlighted with a `Check` icon and dynamic resolution badge (e.g. `System (Dark)`).
  * Positioned `ThemeToggle` in `frontend/components/layout/Header.tsx` adjacent to the backend health pill and user authentication controls.
* **Verification Results:**
  * Clean TypeScript type check (`tsc --noEmit` exited with code 0).
  * Successful Turbopack production build (`npm run build` compiled all 5 static pages cleanly).
  * ESLint validation passed (`npm run lint` with 0 errors).
  * Dev server verified via HTTP health checks.
* **Documentation:** Documented in [LLD 07: React Frontend (§4–5)](../lld/07_phase5_react_frontend.md) and registered in [LLD Index](../lld/00_INDEX.md).

