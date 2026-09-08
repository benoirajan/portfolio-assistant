# LLD 04 — Logging Infrastructure

**Files covered:**
`src/core/logging_config.py` · `src/main.py` · `src/api/holdings.py` · `src/api/analytics.py` · `src/api/auth.py` · `src/api/advisory.py` · `src/services/zerodha_client.py` · `src/services/market_data.py` · `src/services/analytics_engine.py` · `src/services/llm_advisor.py` · `.gitignore`

**Cross-references:**
- `setup_logging()` called from → [LLD 01 §5](./01_phase1_auth_and_holdings.md#5-srcmainpy--fastapi-application-entry-point)
- Known logger name issue in `tax_harvesting.py` → [LLD 02 §3](./02_phase2_analytics_engine.md#3-srcservicestax_harvestingpy--tax-harvesting-analyzer)
- Retry warning/error log lines → [LLD 05 §2.5](./05_retry_and_fallback.md#25-logging-behaviour)

---

## 1. `src/core/logging_config.py` — Central Setup

Single `setup_logging(level)` function called once at application startup in `main.py`. All other modules obtain their logger via `logging.getLogger("portfolio_assistant.<module>")`.

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

A `@app.middleware("http")` wraps every incoming request with structured tracing.

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

All 4 routers use `logging.getLogger("portfolio_assistant.api.<name>")`. Every endpoint logs meaningful business values — not just "request received".

### `holdings.py`

Router spec → [LLD 01 §4](./01_phase1_auth_and_holdings.md#4-srcapiholdingspy--holdings--portfolio-router)

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

Router spec → [LLD 02 §4](./02_phase2_analytics_engine.md#4-srcapianalyticspy--analytics-router)

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

Router spec → [LLD 01 §3](./01_phase1_auth_and_holdings.md#3-srcapiauthpy--authentication-router)

| Level | Trigger | Message |
|---|---|---|
| `INFO` | Login URL generated | `"Login URL generated"` |
| `INFO` | Demo login initiated | `"Demo login initiated"` |
| `INFO` | Demo login complete | `"Demo login successful"` |
| `INFO` | OAuth callback received | `"OAuth callback received — exchanging request_token"` |
| `INFO` | OAuth session established | `"OAuth session established successfully"` |
| `ERROR` | OAuth callback failed | Exception message + stack trace |

### `advisory.py`

Router spec → [LLD 03 §4](./03_phase3_ai_advisory.md#4-srcapiadvisorypy--advisory-rest-endpoint)

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

### `llm_advisor.py` (AI Traceability Logging)

| Level | Trigger | Fields / Content logged |
|---|---|---|
| `INFO` | LLM request initiated | `model`, `prompt_len` |
| `DEBUG` | LLM prompt built | Full prompt payload sent to AI backend |
| `INFO` | LLM response received | `raw_len` |
| `DEBUG` | LLM raw output | Complete raw response string received from AI backend |
| `INFO` | Response parsed | `raw_len`, `recommendations_count` |
| `WARNING` | Guardrails triggered | Hallucinated symbol count or small/mid-cap allocation cap adjustments |
| `ERROR` | Validation / API failure | Exception message and fallback notification |

Example:
```
INFO  | portfolio_assistant.llm_advisor | Sending request to Gemini API (model=gemini-3.6-flash, prompt_len=1420)
DEBUG | portfolio_assistant.llm_advisor | Gemini Prompt Payload:
...
INFO  | portfolio_assistant.llm_advisor | Received response from Gemini API (raw_len=850)
DEBUG | portfolio_assistant.llm_advisor | Gemini Raw Response:
...
INFO  | portfolio_assistant.llm_advisor | LLM recommendations validated successfully — count=5
```

---

## 4. Services — Logger Hierarchy Alignment

All service loggers renamed to the `portfolio_assistant.*` hierarchy so they inherit the root handler configuration set up by `setup_logging()`.

| File | Logger before | Logger after | Status |
|---|---|---|---|
| `zerodha_client.py` | `"zerodha_service"` | `"portfolio_assistant.zerodha_client"` | ✅ Aligned |
| `market_data.py` | `"market_data"` | `"portfolio_assistant.market_data"` | ✅ Aligned |
| `analytics_engine.py` | `"analytics_engine"` | `"portfolio_assistant.analytics_engine"` | ✅ Aligned |
| `llm_advisor.py` | `"llm_advisor"` | `"portfolio_assistant.llm_advisor"` | ✅ Aligned |
| `tax_harvesting.py` | `"tax_harvesting"` | `"portfolio_assistant.tax_harvesting"` | ✅ Aligned |

---

## 5. Log Levels Used Across the Application

| Level | Where used |
|---|---|
| `DEBUG` | Health check calls, enriched holdings count in advisory, full AI prompt payload sent to Gemini/Ollama, raw string response returned from Gemini/Ollama |
| `INFO` | Request tracing (→/←), startup/shutdown, all successful business operations with key metric values, AI generation initiation & response length, validation success |
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
