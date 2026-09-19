# Action Items & TODO Tasks
## 📋 Upcoming TODO Tasks

### 1. 🗄️ Container-Ready Free Database Persistence (Priority: P0 - Infrastructure & State)
* **Architectural Rationale:** Foundational database layer. Containerized environments (Docker, Railway, Render, Fly.io) are ephemeral; storing portfolio data in local JSON files causes state loss across container restarts and redeployments. A free database (PostgreSQL container in `docker-compose.yml` for self-hosting / local development, or Neon / Supabase free tier for cloud) with SQLAlchemy 2.0 and Alembic migrations provides durable, production-ready persistence.
* **Objective:** Replace file-based local storage with a free, container-friendly relational database (PostgreSQL).
* **Details:**
  * Add a `postgres:16-alpine` service with persistent volume to `backend/docker-compose.yml`.
  * Configure SQLAlchemy 2.0 engine, declarative base, and Alembic migration scripts in `backend/`.
  * Define core tables: `users`, `user_holdings`, `portfolios`, and `sessions`.
  * Refactor `backend/src/services/portfolio_repository.py` to persist and re-hydrate holdings through database queries rather than JSON files.

---

### 2. 🔐 Multi-Tenant Authentication & Session Management (Priority: P0 - Security & Identity)
* **Architectural Rationale:** Security prerequisite for public hosting. Before hosting the application publicly, multi-user isolation is mandatory so that users access only their own portfolios and broker credentials. Sensitive tokens (Zerodha enctoken, API keys) must be encrypted at rest.
* **Objective:** Implement full authentication and user identity across backend and frontend.
* **Details:**
  * Implement FastAPI auth routes (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`) using OAuth2 password bearer and JWT tokens.
  * Secure password hashing with `bcrypt` (`passlib`) and encrypt broker session credentials using Fernet AES-256.
  * Build Next.js authentication context (`AuthContext.tsx`), route protection middleware, and login/registration modal or pages.
  * Attach `Authorization: Bearer <token>` automatically to all frontend Axios API calls.

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
