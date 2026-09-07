# Architecture Review: Portfolio Assistant

**Reviewer**: Amazon Q (AI Architect Review)
**Scope**: README.md, HLD.md, Phase 1–4 Implementation Plans

---

## Summary

The phased delivery approach is well-structured, the human-in-the-loop order guard is the correct design for a financial application, and the hybrid deterministic + LLM advisory model is sound. The issues below are grouped by severity and should be addressed before or during the relevant phase.

---

## 🔴 Critical Issues

### C1. Unencrypted Session Token Storage
**Affects**: HLD §3.1, Phase 1

The Zerodha `access_token` is planned to be stored in memory or Redis without encryption. This is a security risk — Redis is often accessible within a network without per-key auth.

**Recommendation**:
- Store only an AES-encrypted reference in Redis, not the raw token.
- For production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault).
- Implement a proactive re-auth notification before the 6 AM daily token expiry, rather than relying on silent failure.

---

### C2. Deferred Database Setup
**Affects**: Phase 1 Plan

Phase 1 mentions "SQLite/PostgreSQL" as interchangeable, but the HLD already defines a full relational schema (`USERS`, `PORTFOLIO_SNAPSHOTS`, `HOLDINGS`, `ORDERS`). Migrating from SQLite to PostgreSQL mid-project is painful and error-prone.

**Recommendation**:
- Start with PostgreSQL + SQLAlchemy + Alembic from day one, even locally via Docker (`docker-compose`).
- The schema is already designed — there is no justification for deferring it.

---

### C3. Sensitive Financial Data Sent to External LLM
**Affects**: Phase 3 §3.2

The plan sends holdings, entry prices, and allocation percentages to the Google Gemini API. Describing this as "anonymized" because stock symbols are masked is insufficient — entry price + allocation % is still personally identifiable financial data.

**Recommendation**:
- Define a formal data minimization policy: send only ratios and relative weights, never absolute monetary values.
- Review and accept Google's data processing and privacy terms before enabling this feature.
- Evaluate a self-hosted alternative (e.g., Ollama + Mistral/LLaMA) as a privacy-preserving option for a personal finance tool.

---

## 🟡 Design Gaps

### D1. No Background Job Scheduler
**Affects**: HLD §3.2, Phase 2, Phase 4

The HLD describes "daily ingestion" and Phase 4 requires weekly digest notifications, but no scheduler component exists in any phase plan. There is no Celery, APScheduler, or cron equivalent defined anywhere.

**Recommendation**:
- Add `APScheduler` (lightweight, no broker needed) or `Celery + Redis` (if task queue complexity grows).
- Define scheduled jobs explicitly:
  - Daily: Holdings sync, token refresh reminder.
  - Weekly: Portfolio digest notification.
  - On-demand: Historical candle download, fundamentals refresh.

---

### D2. yfinance Used as Primary Data Source
**Affects**: Phase 2 §3.1

`yfinance` is an unofficial web scraper with no SLA, no rate limit guarantees, and a history of breaking silently when Yahoo Finance changes its internal API.

**Recommendation**:
- Implement a fallback data provider chain:
  1. Primary: A paid/official API (e.g., Twelve Data, Polygon.io, or NSE official data feed).
  2. Fallback: `yfinance` for non-critical or cached data.
- Cache all fundamental data aggressively (TTL: 24h minimum) to reduce dependency on live calls.

---

### D3. XIRR Calculation Missing Its Data Source
**Affects**: Phase 2 §3.2

XIRR requires historical transaction dates and amounts (buy/sell cash flows), not just current holdings. The `GET /portfolio/holdings` endpoint only returns the current state — it does not provide transaction history.

**Recommendation**:
- Use Zerodha's tradebook endpoint (`GET /trades`) or `GET /portfolio/positions` history to retrieve historical cash flows.
- Document this data dependency explicitly in the Phase 2 plan before implementation begins.

---

### D4. Single-User vs. Multi-User Architecture Ambiguity
**Affects**: HLD §8 (Database Schema)

The DB schema includes a `USERS` table, implying multi-user support, but the entire application is designed and documented as a personal single-user tool. This creates unnecessary complexity without a clear migration path.

**Recommendation**:
- **If single-user**: Remove the `USERS` table. Use a single config-driven user identity. Simplifies all queries and removes the need for auth middleware.
- **If multi-user is a future goal**: Explicitly plan for JWT-based auth middleware, per-user data isolation in all queries, and per-user rate limiting. This is a significant scope addition and should be its own phase.

---

### D5. No Order Status Polling After Execution
**Affects**: Phase 4 §3.2

After `POST /orders/regular` is called, the plan has no mechanism to track the order lifecycle. Zerodha orders transition through states: `OPEN` → `COMPLETE` → `REJECTED` / `CANCELLED`. Without polling, the application has no way to confirm execution or handle rejections.

**Recommendation**:
- After order submission, store the returned `order_id` in the `ORDERS` table with status `SUBMITTED`.
- Implement a polling job using `GET /orders/{order_id}` to sync final order status back to the DB.
- Surface order status updates in the UI and trigger a notification on `COMPLETE` or `REJECTED`.

---

## 🟢 Improvements & Recommendations

### I1. Streamlit → FastAPI Connection Resilience
**Affects**: Phase 1, all phases

The Streamlit UI calls the FastAPI backend over HTTP. If the backend is unavailable, the UI will crash with an unhandled exception and no user-friendly message.

**Recommendation**:
- Add a `GET /health` endpoint to the FastAPI backend.
- Add a connection status check in the Streamlit UI on startup, with a clear error banner if the backend is unreachable.

---

### I2. No API Rate Limit Handling
**Affects**: HLD §5, all phases using Kite API

The HLD documents Kite's 3 req/sec rate limit, but none of the service layer files implement a rate limiter or retry-with-backoff strategy. Under normal usage (multiple API calls on dashboard load), this limit will be hit.

**Recommendation**:
- Add `tenacity` retry decorators with exponential backoff on all Kite API call wrappers in `zerodha_client.py`.
- Add a token-bucket or leaky-bucket rate limiter at the service layer to proactively throttle outgoing requests.

---

### I3. LLM Output Guardrails Are Insufficient
**Affects**: Phase 3 §3.3

The only defined guardrail is "no > 20% allocation to small-cap." This does not protect against common LLM failure modes.

**Recommendation**:
- Add Pydantic schema validation on the full LLM response, enforcing:
  - `action` is strictly one of `BUY | SELL | HOLD | TRIM`.
  - `confidence_score` is a float in range `[0.0, 1.0]`.
  - `symbol` exists in the current holdings list (prevents hallucinated tickers).
  - `target_allocation_pct` sum across all recommendations does not exceed 100%.
- Reject and log any response that fails validation rather than passing it through.

---

### I4. No Observability Strategy
**Affects**: All phases

There is no logging, metrics, or tracing strategy defined across any phase. Debugging production issues in a financial application without structured logs is extremely difficult.

**Recommendation**:
- Adopt `structlog` for structured JSON logging across FastAPI and all service modules.
- Propagate a `request_id` from FastAPI middleware through all downstream service and Kite API calls.
- Log all order staging, approval, and execution events with full context as an audit trail.

---

### I5. Frontend Migration Path is Undefined
**Affects**: HLD §7

The tech stack table mentions "Next.js (Phase 2)" as a frontend upgrade, but Phase 2's implementation plan only modifies the existing Streamlit `app.py`. A Streamlit → Next.js migration is a full frontend rewrite, not an incremental change.

**Recommendation**:
- Remove the Next.js reference from the current tech stack table to avoid confusion.
- If a production-grade UI is desired, define it as an explicit **Phase 5** with its own scope, API contract definition (OpenAPI spec), and delivery plan.

---

## Recommended Resolution Priority

| Priority | Issue | Blocking Phase |
| :--- | :--- | :--- |
| 1 | **C2** — PostgreSQL + Alembic from day one | Phase 1 |
| 2 | **C1** — Token encryption / secrets manager | Phase 1 |
| 3 | **D1** — Add background job scheduler | Phase 2 |
| 4 | **D3** — XIRR transaction history data source | Phase 2 |
| 5 | **D2** — yfinance fallback strategy | Phase 2 |
| 6 | **I2** — Rate limit handling with `tenacity` | Phase 2 |
| 7 | **C3** — LLM data minimization policy | Phase 3 |
| 8 | **I3** — Strengthen LLM output guardrails | Phase 3 |
| 9 | **D5** — Order status polling | Phase 4 |
| 10 | **I4** — Structured logging & observability | All phases |
| 11 | **D4** — Resolve single vs. multi-user ambiguity | Phase 1 |
| 12 | **I1** — Streamlit health check & error handling | Phase 1 |
| 13 | **I5** — Remove/defer Next.js from tech stack | HLD cleanup |
