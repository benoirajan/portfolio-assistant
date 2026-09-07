# LLD 02 — Logging Infrastructure

**Files covered:**
`src/core/logging_config.py` · `src/main.py` · `src/api/holdings.py` · `src/api/analytics.py` · `src/api/auth.py` · `src/api/advisory.py` · `src/services/zerodha_client.py` · `src/services/market_data.py` · `src/services/analytics_engine.py` · `src/services/llm_advisor.py` · `.gitignore`

---

## 1. `src/core/logging_config.py` — Central Setup

**New file.** Single `setup_logging(level)` function called once at application startup in `main.py`. All other modules obtain their logger via `logging.getLogger("portfolio_assistant.<module>")`.

### Configuration

| Setting | Value |
|---|---|
| Log format | `%(asctime)s \| %(levelname)-8s \| %(name)s \| %(message)s` |
| Date format | `%Y-%m-%d %H:%M:%S` |
| Console handler | `StreamHandler` — always active |
| File handler | `RotatingFileHandler` — `logs/app.log` |
| Max file size | 5 MB per file |
| Backup count | 3 rotated files kept |
| Default level | `INFO` |

To enable debug output during development, change the call in `main.py`:
```python
setup_logging(level="DEBUG")
```

### Third-party loggers suppressed to WARNING

| Logger | Reason |
|---|---|
| `uvicorn.access` | Per-request access logs are redundant — covered by our own middleware |
| `httpx` | Internal HTTP client noise |
| `httpcore` | Low-level transport noise |
| `urllib3` | Connection pool noise |
| `yfinance` | Verbose download progress messages |

### Logger hierarchy

All application loggers use the `portfolio_assistant.*` namespace:

```
portfolio_assistant
├── portfolio_assistant.main
├── portfolio_assistant.retry
├── portfolio_assistant.api.holdings
├── portfolio_assistant.api.analytics
├── portfolio_assistant.api.auth
├── portfolio_assistant.api.advisory
├── portfolio_assistant.zerodha_client
├── portfolio_assistant.market_data
├── portfolio_assistant.analytics_engine
└── portfolio_assistant.llm_advisor
```

This enables controlling the entire application's log level with a single call:
```python
logging.getLogger("portfolio_assistant").setLevel(logging.DEBUG)
```

---

## 2. `src/main.py` — Request Tracing Middleware

### `request_tracing_middleware`

A new `@app.middleware("http")` wraps every incoming request with structured tracing.

**On request entry:**
```
→ GET /api/v1/holdings [req_id=a3f2c1b0]
```

**On response:**
```
← GET /api/v1/holdings [req_id=a3f2c1b0] status=200 84.2ms
```

**On unhandled exception:**
```
✗ GET /api/v1/holdings [req_id=a3f2c1b0] UNHANDLED ERROR after 12.1ms: ...
```

| Feature | Detail |
|---|---|
| `req_id` | First 8 characters of a UUID4 — unique per request |
| Elapsed time | Measured with `time.perf_counter()` — sub-millisecond precision |
| `X-Request-ID` header | Attached to every response for client-side correlation |
| Exception logging | `exc_info=True` — full stack trace captured in log file |

### Lifecycle events

| Event | Log message |
|---|---|
| `on_startup` | `Portfolio Assistant API starting — demo_mode=... host=... port=...` |
| `on_shutdown` | `Portfolio Assistant API shutting down` |

---

## 3. API Routers — Structured Log Lines

All 4 routers updated with `logging.getLogger("portfolio_assistant.api.<name>")`. Every endpoint logs meaningful business values — not just "request received".

### `holdings.py`

| Level | Trigger | Fields logged |
|---|---|---|
| `INFO` | Holdings fetched successfully | `count`, `is_live`, `pnl`, `pnl%` |
| `WARNING` | Zerodha returns an error message | `error_message` string |
| `ERROR` | Unhandled exception in endpoint | Full stack trace via `exc_info=True` |

Example:
```
INFO | portfolio_assistant.api.holdings | Holdings fetched — count=7 is_live=True pnl=42350.00 (18.50%)
```

### `analytics.py`

| Level | Trigger | Fields logged |
|---|---|---|
| `INFO` | Performance metrics calculated | `xirr%`, `beta`, `sharpe` |
| `INFO` | Tax analysis complete | `net_stcg`, `net_ltcg`, `candidate_count` |
| `INFO` | Fundamentals enriched | `holdings_count` |
| `ERROR` | Any endpoint exception | Full stack trace |

Example:
```
INFO | portfolio_assistant.api.analytics | Performance metrics — xirr=18.42% beta=1.05 sharpe=0.87
```

### `auth.py`

| Level | Trigger | Message |
|---|---|---|
| `INFO` | Login URL generated | `"Login URL generated"` |
| `INFO` | Demo login initiated | `"Demo login initiated"` |
| `INFO` | Demo login complete | `"Demo login successful"` |
| `INFO` | OAuth callback received | `"OAuth callback received — exchanging request_token"` |
| `INFO` | OAuth session established | `"OAuth session established successfully"` |
| `ERROR` | OAuth callback failed | Exception message + stack trace |

### `advisory.py`

| Level | Trigger | Fields logged |
|---|---|---|
| `INFO` | Request received | `investment_goal`, `stock_cap%`, `sector_cap%` |
| `DEBUG` | Holdings enriched | `holdings_count` |
| `INFO` | Advisory complete | `source`, `rule_flags_count`, `recommendations_count` |

Example:
```
INFO | portfolio_assistant.api.advisory | Advisory request — goal='Moderate Growth' stock_cap=15% sector_cap=25%
INFO | portfolio_assistant.api.advisory | Advisory complete — source=llm rule_flags=2 recommendations=7
```

---

## 4. Services — Logger Hierarchy Alignment

All service loggers renamed from flat strings to the `portfolio_assistant.*` hierarchy so they inherit the root handler configuration set up by `setup_logging()`.

| File | Logger before | Logger after |
|---|---|---|
| `zerodha_client.py` | `"zerodha_service"` | `"portfolio_assistant.zerodha_client"` |
| `market_data.py` | `"market_data"` | `"portfolio_assistant.market_data"` |
| `analytics_engine.py` | `"analytics_engine"` | `"portfolio_assistant.analytics_engine"` |
| `llm_advisor.py` | `"llm_advisor"` | `"portfolio_assistant.llm_advisor"` |

---

## 5. Log Levels Used Across the Application

| Level | Where used |
|---|---|
| `DEBUG` | Health check calls, enriched holdings count in advisory |
| `INFO` | Request tracing (→/←), startup/shutdown, all successful business operations with key metric values |
| `WARNING` | Holdings fetch warnings from Zerodha, LLM hallucinated symbols filtered, small-cap cap enforcement, nsepython/yfinance fetch failures, retry attempts |
| `ERROR` | Unhandled middleware exceptions, all `except` blocks with `exc_info=True`, Gemini/Ollama API failures after retries, LLM validation failures |

---

## 6. `.gitignore`

Added to prevent log files from being committed:
```
# Logs
logs/
*.log
```
