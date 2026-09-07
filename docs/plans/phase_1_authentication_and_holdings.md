# Implementation Plan - Phase 1: Zerodha Authentication & Holdings Ingestion (MVP)

---

## 1. Overview & Objectives
Phase 1 establishes the core foundation of the Portfolio Assistant application. It delivers Zerodha Kite Connect OAuth 2.0 authentication, REST API data ingestion endpoints via FastAPI, and a real-time Streamlit dashboard with full support for both Live Demat syncing and a fallback Demo Mode.

> **Architecture decisions locked in Phase 1 (non-negotiable for later phases):**
> - PostgreSQL + SQLAlchemy + Alembic is the database from day one. SQLite is not used.
> - All Kite API calls use `tenacity` retry with exponential backoff.
> - Structured logging via `structlog` with `request_id` propagation is set up from the start.
> - AES-encrypted token storage in Redis — raw `access_token` is never stored in plaintext.

---

## 2. Technical Components & Specifications

### 2.1 Dependencies (`requirements.txt`)
- `fastapi` & `uvicorn`: High-performance asynchronous web framework and ASGI server.
- `kiteconnect`: Official Python client for Zerodha Kite Connect API (v3).
- `pandas` & `plotly`: Data frame processing and interactive charts for portfolio analytics.
- `streamlit`: Rapid web application dashboard UI.
- `python-dotenv` & `pydantic`: Environment configuration loading and schema validation.
- `sqlalchemy` & `alembic`: ORM and database migration management (PostgreSQL from day one).
- `psycopg2-binary`: PostgreSQL adapter for Python.
- `redis` & `cryptography`: Redis client and AES encryption for secure token storage.
- `tenacity`: Retry-with-exponential-backoff for all external API calls.
- `structlog`: Structured JSON logging with request context propagation.
- `apscheduler`: Background job scheduler for daily sync and re-auth reminder tasks.

### 2.2 Configuration Management (`src/core/config.py`)
Loads settings from `.env` or system environment variables:
- `KITE_API_KEY`, `KITE_API_SECRET`, `KITE_REDIRECT_URL`
- `DEMO_MODE` (boolean flag to toggle realistic sample holdings without API keys)
- `DATABASE_URL` (PostgreSQL connection string, e.g. `postgresql://user:pass@localhost:5432/portfolio`)
- `REDIS_URL` (Redis connection string)
- `TOKEN_ENCRYPTION_KEY` (AES-256 key for encrypting the Zerodha access token in Redis)

### 2.3 Zerodha Client Wrapper (`src/services/zerodha_client.py`)
Implements official Kite Connect v3 endpoints:
- `get_login_url()`: Returns `https://kite.zerodha.com/connect/login?v=3&api_key=...`
- `generate_session(request_token)`: Exchanges token for session `access_token`. Encrypts and stores in Redis immediately — never returns raw token to caller.
- `get_holdings()`: Ingests long-term delivery equity holdings (`GET /portfolio/holdings`).
- `get_positions()`: Ingests intraday & net positions (`GET /portfolio/positions`).
- `get_margins()`: Ingests cash balance & collateral margins (`GET /user/margins`).

All methods are decorated with `@retry` from `tenacity` (exponential backoff, max 3 attempts) and guarded by a token-bucket rate limiter (max 3 req/sec).

### 2.4 FastAPI API Routes (`src/api/`)
- `GET /health`: Backend health check — used by Streamlit UI on startup to verify connectivity.
- `GET /api/v1/auth/login-url`: Generates Zerodha OAuth URL.
- `POST /api/v1/auth/callback`: Handles OAuth redirect token exchange.
- `GET /api/v1/holdings`: Returns portfolio summary stats & enriched holdings list.
- `GET /api/v1/margins`: Returns cash margin balances.

### 2.5 Streamlit Dashboard UI (`src/ui/app.py`)
- **Startup Health Check**: Calls `GET /health` on load. Displays a clear error banner if the backend is unreachable — no unhandled exceptions.
- **Header KPI Cards**: Total Invested (₹), Current Value (₹), Overall P&L (₹ & %), Cash Balance (₹), Holdings Count.
- **Holdings Table**: Sortable DataFrame with color-coded profit/loss indicators and symbol/sector search filters.
- **Analytics Tab**: Sector breakdown pie chart & stock concentration risk bar chart with 15% threshold alerts.

### 2.6 Database Setup (`src/core/database.py` + `alembic/`)
- PostgreSQL connection via SQLAlchemy engine.
- Alembic migration scripts for initial schema: `users`, `portfolio_snapshots`, `holdings`, `orders`, `trade_transactions`.
- A `docker-compose.yml` is provided for local PostgreSQL + Redis setup.

### 2.7 Background Scheduler (`src/core/scheduler.py`)
- `APScheduler` instance initialized at FastAPI startup.
- Jobs registered in Phase 1:
  - Daily 5:30 AM IST: Zerodha re-auth reminder log/notification.
  - On-demand: Holdings sync triggered post-login.

---

## 3. Status & Verification
- **Status**: ⚠️ Revised — Phase 1 must be re-verified against updated architecture decisions.
- **Verification Checklist**:
  - [ ] PostgreSQL schema created via Alembic migration (no SQLite).
  - [ ] `access_token` stored AES-encrypted in Redis, not in plaintext.
  - [ ] All Kite API calls retry on failure via `tenacity`.
  - [ ] `GET /health` endpoint returns 200 and is checked by Streamlit on startup.
  - [ ] `structlog` emits structured JSON logs with `request_id` on all API requests.
  - [ ] `APScheduler` starts with FastAPI and registers the 5:30 AM re-auth reminder job.
