# LLD 05 — Exponential Retry & Fallback

**Files covered:**
`src/core/retry.py` · `src/services/market_data.py` · `src/services/zerodha_client.py` · `src/services/llm_advisor.py`

**Cross-references:**
- `retry_call()` used in Zerodha client → [LLD 01 §2](./01_phase1_auth_and_holdings.md#_make_enctoken_requestpath-str---tupleoptionaldict-optionalstr)
- `@retry` used in market data providers → [LLD 02 §1](./02_phase2_analytics_engine.md#_fetch_nsepythonsymbol-str---optionaldict)
- `@retry` used in Gemini/Ollama callers → [LLD 03 §3.3](./03_phase3_ai_advisory.md#33-_call_gemini)
- Log lines emitted by retry → [LLD 04 §5](./04_logging.md#5-log-levels-used-across-the-application)

---

## 1. Design Principles

**Where retry applies:** Only on external I/O calls that can fail transiently — network timeouts, rate limits, temporary service unavailability.

**Where retry does NOT apply:**
- Deterministic rule engine (`rebalancer.py`) — pure computation, retrying won't change the result
- Pydantic validation — schema violations are not transient
- HTTP 4xx errors from Zerodha — auth failures and bad tokens are not transient

**Fail-fast principle:** Non-retryable errors are re-raised immediately without sleeping. This avoids wasting seconds on errors that will never recover (e.g. a 404 model-not-found from Gemini).

---

## 2. `src/core/retry.py` — Shared Retry Utility

Two public interfaces used across the application.

### 2.1 `@retry(...)` Decorator

```python
@retry(
    max_attempts=3,
    base_delay=1.0,
    multiplier=2.0,
    max_delay=30.0,
    jitter=True,
    retryable_on=(ConnectionError, TimeoutError),
)
def my_function(): ...
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_attempts` | `int` | `3` | Total number of attempts including the first |
| `base_delay` | `float` | `1.0` | Initial sleep duration in seconds |
| `multiplier` | `float` | `2.0` | Factor applied to delay after each failure |
| `max_delay` | `float` | `30.0` | Upper cap on sleep duration in seconds |
| `jitter` | `bool` | `True` | Adds `random(0, 0.5)s` to each sleep |
| `retryable_on` | `Tuple[Type[Exception], ...]` | `(Exception,)` | Only these exception types trigger a retry |

### 2.2 `retry_call(fn, args, kwargs, ...)` Inline Function

Used when decorating is not practical — e.g. closures defined inside instance methods.

```python
result = retry_call(
    _do_request,
    max_attempts=3,
    base_delay=1.0,
    retryable_on=(urllib.error.URLError, TimeoutError),
)
```

### 2.3 Backoff Formula

```
sleep = min(base_delay × multiplier^(attempt−1) + jitter(0, 0.5s), max_delay)
```

**Example schedule** (base=1s, multiplier=2, jitter≈0.25s avg):

| Attempt | Failure | Sleep before next attempt |
|---|---|---|
| 1 | ✗ | ~1.25s |
| 2 | ✗ | ~2.25s |
| 3 | ✗ | raise |

### 2.4 Jitter Rationale

Without jitter, all concurrent symbol fetches (e.g. 7 holdings being enriched simultaneously) would retry at exactly the same time, creating a thundering herd that hammers the NSE/Yahoo endpoints in sync. Adding `random.uniform(0, 0.5)` spreads the retries across a 500ms window.

### 2.5 Logging Behaviour

| Situation | Log level | Message includes |
|---|---|---|
| Retryable failure, will retry | `WARNING` | Function name, attempt x/n, exception, sleep duration |
| Final failure or non-retryable | `ERROR` | Function name, attempt x/n, exception |

---

## 3. `market_data.py` — nsepython & yfinance Retry

Both provider fetchers define an inner `@retry`-decorated closure around the network call. The existing 4-tier fallback chain is preserved — retry is layered **inside** each tier, not across tiers.

Full provider chain spec → [LLD 02 §1](./02_phase2_analytics_engine.md#get_stock_fundamental_datasymbol-str---dict)

### Fallback chain (unchanged)

```
nsepython (3 retries)
    ↓ None
yfinance (3 retries)
    ↓ None
Static metadata DB
    ↓ not found
Generic defaults
```

### Retry policies

| Provider | `max_attempts` | `base_delay` | `retryable_on` | On exhaustion |
|---|---|---|---|---|
| `nsepython` | 3 | 1.0s | `Exception` (any) | Returns `None` → falls through to yfinance |
| `yfinance` | 3 | 2.0s | `Exception` (any) | Returns `None` → falls through to static DB |

`yfinance` uses a longer base delay (2s) because Yahoo Finance rate-limits more aggressively than NSE.

---

## 4. `zerodha_client.py` — Enctoken Request Retry

`_make_enctoken_request()` uses `retry_call()` per endpoint URL. Full method spec → [LLD 01 §2](./01_phase1_auth_and_holdings.md#_make_enctoken_requestpath-str---tupleoptionaldict-optionalstr).

### Retry policy

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 1.0s |
| `retryable_on` | `(urllib.error.URLError, TimeoutError, ConnectionError)` |

### Fail-fast on HTTP errors

`urllib.error.HTTPError` (4xx/5xx) is caught **outside** `retry_call` and logged as `WARNING` — not retried. Rationale: HTTP errors from Zerodha indicate auth failure or an invalid/expired token. Retrying 3 times would waste ~7 seconds before the inevitable fallback to demo data.

### Endpoint fallback (unchanged)

```
https://api.kite.trade{path}   (retry up to 3×)
    ↓ failure
https://kite.zerodha.com/oms{path}   (retry up to 3×)
    ↓ failure
Demo data / empty response
```

---

## 5. `llm_advisor.py` — Gemini & Ollama Retry

### 5.1 Gemini — 429-Only Retry

The Gemini SDK raises a generic `Exception` for all API errors. To distinguish rate limit errors (retryable) from model/auth errors (non-retryable), a sentinel exception is defined:

```python
class _GeminiRateLimitError(Exception):
    """Raised on HTTP 429 — signals retry with backoff is appropriate."""
```

Inside `_generate()`, the exception is inspected and re-raised as the sentinel if it's a rate limit:

```python
except Exception as exc:
    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
        raise _GeminiRateLimitError(msg) from exc
    raise  # 404, 400, auth errors — fail fast, no retry
```

The outer `@retry` is configured with `retryable_on=(_GeminiRateLimitError,)` — only the sentinel triggers backoff.

**Retry policy:**

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 2.0s |
| `multiplier` | 2.0 |
| `max_delay` | 30.0s |
| `retryable_on` | `(_GeminiRateLimitError,)` |

**Scenario table:**

| HTTP status / Error | Behaviour |
|---|---|
| `429 / RESOURCE_EXHAUSTED` | Retry up to 3× with 2s → 4s → 8s backoff |
| `404` (model not found) | Fail fast — no retry — fall back to rule engine |
| `400` (bad request) | Fail fast — no retry — fall back to rule engine |
| Auth / key error | Fail fast — no retry — fall back to rule engine |

This matches the explicit recommendation in [api-references/Gemini_api_doc.md](../api-references/Gemini_api_doc.md#troubleshooting--best-practices): *"enforce exponential backoff and jitter on retries"* for 429 errors.

### 5.2 Ollama — General Retry

Ollama is a local service that may be temporarily starting up or under load. All exceptions are retryable.

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 2.0s |
| `retryable_on` | `(Exception,)` — any exception |

### 5.3 LLM Fallback Chain

```
_call_gemini() or _call_ollama()
    ↓ None (all retries exhausted or non-retryable error)
_rule_based_recommendations()   ← deterministic, no external calls
    ↓
response with source="rule_engine"
```

The UI displays a fallback indicator banner when `source == "rule_engine"` so the user knows the LLM was unavailable. Fallback logic spec → [LLD 03 §3.5](./03_phase3_ai_advisory.md#35-_rule_based_recommendations--deterministic-fallback).
