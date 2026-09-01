# Implementation Plan - Phase 1: Zerodha Authentication & Holdings Ingestion (MVP)

---

## 1. Overview & Objectives
Phase 1 establishes the core foundation of the Portfolio Assistant application. It delivers Zerodha Kite Connect OAuth 2.0 authentication, REST API data ingestion endpoints via FastAPI, and a real-time Streamlit dashboard with full support for both Live Demat syncing and a fallback Demo Mode.

---

## 2. Technical Components & Specifications

### 2.1 Dependencies (`requirements.txt`)
- `fastapi` & `uvicorn`: High-performance asynchronous web framework and ASGI server.
- `kiteconnect`: Official Python client for Zerodha Kite Connect API (v3).
- `pandas` & `plotly`: Data frame processing and interactive charts for portfolio analytics.
- `streamlit`: Rapid web application dashboard UI.
- `python-dotenv` & `pydantic`: Environment configuration loading and schema validation.

### 2.2 Configuration Management (`src/core/config.py`)
Loads settings from `.env` or system environment variables:
- `KITE_API_KEY`, `KITE_API_SECRET`, `KITE_REDIRECT_URL`
- `DEMO_MODE` (boolean flag to toggle realistic sample holdings without API keys)

### 2.3 Zerodha Client Wrapper (`src/services/zerodha_client.py`)
Implements official Kite Connect v3 endpoints:
- `get_login_url()`: Returns `https://kite.zerodha.com/connect/login?v=3&api_key=...`
- `generate_session(request_token)`: Exchanges token for session `access_token`.
- `get_holdings()`: Ingests long-term delivery equity holdings (`GET /portfolio/holdings`).
- `get_positions()`: Ingests intraday & net positions (`GET /portfolio/positions`).
- `get_margins()`: Ingests cash balance & collateral margins (`GET /user/margins`).

### 2.4 FastAPI API Routes (`src/api/`)
- `GET /api/v1/auth/login-url`: Generates Zerodha OAuth URL.
- `POST /api/v1/auth/callback`: Handles OAuth redirect token exchange.
- `GET /api/v1/holdings`: Returns portfolio summary stats & enriched holdings list.
- `GET /api/v1/margins`: Returns cash margin balances.

### 2.5 Streamlit Dashboard UI (`src/ui/app.py`)
- **Header KPI Cards**: Total Invested (₹), Current Value (₹), Overall P&L (₹ & %), Cash Balance (₹), Holdings Count.
- **Holdings Table**: Sortable DataFrame with color-coded profit/loss indicators and symbol/sector search filters.
- **Analytics Tab**: Sector breakdown pie chart & stock concentration risk bar chart with 15% threshold alerts.

---

## 3. Status & Verification
- **Status**: ✅ Completed & Verified.
- **Verification**: Code syntax compiled cleanly via `py_compile`. Backend API and Streamlit UI components operational.
