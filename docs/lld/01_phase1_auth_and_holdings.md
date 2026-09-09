# LLD 01 — Phase 1: Authentication & Holdings Ingestion

**Files covered:**
`src/core/config.py` · `src/services/zerodha_client.py` · `src/api/auth.py` · `src/api/holdings.py` · `src/main.py`

**Cross-references:**
- Retry policies used here → [LLD 05 — Retry & Fallback](./05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry)
- Log lines emitted here → [LLD 04 — Logging](./04_logging.md#3-api-routers--structured-log-lines)
- Zerodha API endpoint specs → [HLD §5](../architecture/HLD.md#5-zerodha-kite-connect-api-specification)
- Zerodha API key setup guide → [guides/zerodha_api_setup_guide.md](../guides/zerodha_api_setup_guide.md)

> **Implementation note:** Phase 1 plan specified PostgreSQL + Redis + APScheduler. The actual implementation uses in-process state and demo data fallback instead. This LLD documents what is implemented, not the original plan.

---

## 1. `src/core/config.py` — Settings

Single `Settings` class loaded from `.env` via `python-dotenv`.

| Field | Type | Default | Description |
|---|---|---|---|
| `KITE_API_KEY` | `str` | `""` | Zerodha Kite Connect API key |
| `KITE_API_SECRET` | `str` | `""` | Zerodha Kite Connect API secret |
| `KITE_REDIRECT_URL` | `str` | `"http://127.0.0.1:8000/api/v1/auth/callback"` | OAuth redirect URL |
| `ZERODHA_ENCTOKEN` | `str` | `""` | Resolved from `ZERODHA_ENCTOKEN`, `ENCTOKEN`, or `KITE_ENCTOKEN` env vars |
| `DEMO_MODE` | `bool` | `True` | Toggles demo data fallback |
| `APP_HOST` | `str` | `"127.0.0.1"` | FastAPI bind host |
| `APP_PORT` | `int` | `8000` | FastAPI bind port |
| `LLM_PROVIDER` | `str` | `"gemini"` | Phase 3 field — see [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |
| `GEMINI_API_KEY` | `str` | `""` | Phase 3 field — see [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |
| `OLLAMA_BASE_URL` | `str` | `"http://localhost:11434"` | Phase 3 field — see [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |
| `OLLAMA_MODEL` | `str` | `"mistral"` | Phase 3 field — see [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |

**Design note:** `ZERODHA_ENCTOKEN` resolves across three env var aliases for compatibility with different user setups.

---

## 2. `src/services/zerodha_client.py` — Zerodha Client Wrapper

### 2.1 Demo Data Constants

| Constant | Purpose |
|---|---|
| `DEMO_HOLDINGS` | 7 realistic NSE equity holdings used when no live token is available |
| `DEMO_MARGINS` | Sample equity margin structure matching Zerodha API response shape |

### 2.2 `ZerodhaService` — Class

Singleton instance `zerodha_service` exported at module level.

#### `__init__()`

Initialises `api_key`, `api_secret`, `redirect_url` from `settings`. Calls `sanitize_token()` on `ZERODHA_ENCTOKEN` if present.

---

#### `sanitize_token(raw_token: str) -> str`

Cleans raw enctoken strings that may contain extraneous formatting from browser copy-paste.

**Strips in order:**
1. Leading/trailing whitespace and quotes (`"`, `'`)
2. `enctoken=` cookie key prefix
3. `Authorization:` header prefix
4. `enctoken ` bearer prefix

**Returns:** Clean token string ready for use in HTTP headers.

---

#### `set_enctoken(enctoken: str)`

Public setter — calls `sanitize_token()` and stores result in `self.enctoken`. Called by API routers when `X-Enctoken` header is present on a request.

---

#### `_init_kite()`

Lazy initialiser for the `KiteConnect` SDK client. Only runs if `self.kite_client` is `None` and `self.api_key` is set. Catches `ImportError` gracefully if `kiteconnect` package is not installed.

---

#### `get_login_url() -> str`

Returns the Zerodha OAuth login URL.

| Condition | Returns |
|---|---|
| `DEMO_MODE=True` or no `api_key` | `http://127.0.0.1:8000/api/v1/auth/demo-login` |
| KiteConnect client available | `kite_client.login_url()` |
| Fallback | Manually constructed `https://kite.zerodha.com/connect/login?v=3&api_key=...` |

---

#### `generate_session(request_token: str) -> Dict[str, Any]`

Exchanges a Zerodha `request_token` for a session.

| Condition | Behaviour |
|---|---|
| `DEMO_MODE=True` or missing credentials | Returns hardcoded demo session dict, sets `access_token = "demo_access_token_12345"` |
| KiteConnect client available | Calls `kite_client.generate_session()`, stores `access_token`, sets it on the client |
| No client | Raises `RuntimeError` |

**Returns:** `{status, access_token, user_name, user_id}`

---

#### `_make_enctoken_request(path: str) -> Tuple[Optional[Dict], Optional[str]]`

Core HTTP request method using `enctoken` auth. Tries two base URLs in sequence.

**Endpoint fallback chain:**
```
https://api.kite.trade{path}       (retry up to 3×)
    ↓ failure
https://kite.zerodha.com/oms{path} (retry up to 3×)
    ↓ failure
Returns (None, last_error_message)
```

**Request headers set:**
- `Authorization: enctoken {token}`
- `Cookie: enctoken={token}`
- `X-Kite-Version: 3`
- `User-Agent: Mozilla/5.0 ...`

**Retry policy** (via `retry_call` — full spec in [LLD 05 §4](./05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry)):

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 1.0s |
| `multiplier` | 2.0 |
| `retryable_on` | `(urllib.error.URLError, TimeoutError, ConnectionError)` |

**Fail-fast:** `urllib.error.HTTPError` (4xx/5xx) is caught outside `retry_call` and logged as `WARNING` — not retried, as these indicate auth/token issues.

**Returns:** `(response_dict, None)` on success, `(None, error_string)` on failure.

---

#### `get_holdings_with_status() -> Tuple[List[Dict], bool, Optional[str]]`

Main holdings fetch with three-tier fallback. Returns `(holdings, is_live, error_message)`.

| Priority | Condition | Behaviour |
|---|---|---|
| 1 | `self.enctoken` set | Calls `_make_enctoken_request("/portfolio/holdings")`. Infers missing `sector` and `cap_category` fields. |
| 2 | `self.access_token` + `kite_client` | Calls `kite_client.holdings()`. Infers missing fields. |
| 3 | Fallback | Returns `DEMO_HOLDINGS` enriched with live LTP via `market_data_service.get_live_quote()`, `is_live=False`, `error_message=None` |

On enctoken failure: returns demo holdings (with live LTP if available), `is_live=False`, and a formatted error message instructing the user to re-copy their enctoken.

**Demo mode live quote enrichment:** Even in demo mode, `last_price`, `close_price`, `day_change`, and `day_change_percentage` are refreshed from yfinance (`.NS`) for each symbol. `pnl` is recomputed from the live `last_price`. Falls back to hardcoded values silently if yfinance is unavailable.

---

#### `get_holdings() -> List[Dict]`

Thin wrapper over `get_holdings_with_status()` — discards the status tuple, returns only the holdings list.

---

#### `get_positions() -> Dict`

Fetches intraday and net positions via `_make_enctoken_request("/portfolio/positions")` or `kite_client.positions()`. Returns `{"net": [], "day": []}` on failure.

---

#### `get_trades() -> List[Dict]`

Fetches historical trade book via `_make_enctoken_request("/trades")` or `kite_client.trades()`. Used by `analytics_engine` for XIRR cash flow reconstruction — see [LLD 02 §2](./02_phase2_analytics_engine.md#_xirr_from_tradestrades-current_value---float). Returns `[]` on failure.

---

#### `get_margins() -> Dict`

Fetches cash and collateral margins. Tries `/user/margins` first, then `/user/margins/equity` as a secondary fallback before returning `DEMO_MARGINS`.

---

#### `_infer_sector(symbol: str) -> str`

Static lookup table mapping 11 common NSE symbols to sector strings. Returns `"Diversified / Others"` for unknown symbols.

---

## 3. `src/api/auth.py` — Authentication Router

Prefix: `/api/v1/auth`

Log lines for all endpoints → [LLD 04 §3](./04_logging.md#authpy)

### `GET /login-url`

Returns the Zerodha OAuth login URL from `zerodha_service.get_login_url()`.

**Response:** `{status: "success", login_url: str}`

---

### `GET /demo-login`

Triggers a demo session without OAuth. Calls `zerodha_service.generate_session("demo_request_token")`.

**Response:** `{status: "success", message: str, session: dict}`

---

### `POST /callback`

Receives `request_token` from Zerodha OAuth redirect and exchanges it for a session.

**Request body:** `{request_token: str, status?: str}`

**On success:** `{status: "success", data: session_dict}`

**On failure:** `HTTP 400` with exception detail. Full stack trace logged via `exc_info=True`.

---

## 4. `src/api/holdings.py` — Holdings & Portfolio Router

Prefix: `/api/v1`

All endpoints accept an optional `X-Enctoken` header. If present, it is passed to `zerodha_service.set_enctoken()` before the data fetch. Falls back to `settings.ZERODHA_ENCTOKEN` if header is absent.

Log lines for all endpoints → [LLD 04 §3](./04_logging.md#holdingspy)

### `GET /holdings`

Returns enriched holdings with portfolio summary KPIs.

**Processing steps:**
1. Set enctoken if provided
2. `zerodha_service.get_holdings_with_status()` → raw holdings + live flag + error
3. `market_data_service.enrich_holdings_with_fundamentals()` → adds P/E, ROE, SMA trend (see [LLD 02 §1](./02_phase2_analytics_engine.md#enrich_holdings_with_fundamentalsholdings-listdict---listdict))
4. Compute `total_investment`, `current_value`, `total_pnl`, `total_pnl_percentage`

**Response shape:**
```json
{
  "status": "success",
  "is_live": bool,
  "error_message": str | null,
  "summary": {
    "total_holdings_count": int,
    "total_investment": float,
    "current_value": float,
    "total_pnl": float,
    "total_pnl_percentage": float
  },
  "holdings": [...]
}
```

---

### `GET /positions`

Returns `{"status": "success", "positions": dict}` from `zerodha_service.get_positions()`.

---

### `GET /margins`

Returns `{"status": "success", "margins": dict}` from `zerodha_service.get_margins()`.

---

## 5. `src/main.py` — FastAPI Application Entry Point

### Router registration

```python
app.include_router(auth_router)
app.include_router(holdings_router)
app.include_router(analytics_router)
app.include_router(advisory_router)
```

### `GET /health`

Returns `{status: "ok", demo_mode: bool}`. Used by the Streamlit UI on startup to verify backend connectivity.

### `request_tracing_middleware`

Full spec → [LLD 04 §2](./04_logging.md#2-srcmainpy--request-tracing-middleware)

### Lifecycle events

| Event | Action |
|---|---|
| `on_startup` | Calls `setup_logging()`, logs host/port/demo_mode |
| `on_shutdown` | Logs shutdown message |
