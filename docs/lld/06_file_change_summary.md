# LLD 06 — File Change Summary

**Session:** Phase 3 AI Advisory Engine + Logging + Retry & Fallback
**Branch:** `feat/phase3-assistant`
**Total files touched:** 19

---

## New Files

| File | Purpose | LLD |
|---|---|---|
| `src/core/logging_config.py` | Central logging bootstrap — console + rotating file handlers, third-party suppression, `portfolio_assistant.*` hierarchy | [LLD 04](./04_logging.md) |
| `src/core/retry.py` | Shared exponential backoff utility — `@retry` decorator and `retry_call()` with jitter and fail-fast logic | [LLD 05](./05_retry_and_fallback.md) |
| `src/services/rebalancer.py` | Deterministic portfolio rule engine — 3 rules (`OVER_CONCENTRATION`, `UNDERPERFORMANCE`, `SECTOR_OVERWEIGHT`), structured flag output | [LLD 03 §2](./03_phase3_ai_advisory.md#2-srcservicesrebalancerpy--deterministic-rule-engine) |
| `src/services/llm_advisor.py` | Full LLM advisory pipeline — Gemini/Ollama integration, data minimization prompt builder, Pydantic guardrails, rule-based fallback | [LLD 03 §3](./03_phase3_ai_advisory.md#3-srcservicesllm_advisorpy--llm-advisory-service) |
| `src/api/advisory.py` | `GET /api/v1/advisory/recommendations` — investment goal + concentration cap params, enctoken header | [LLD 03 §4](./03_phase3_ai_advisory.md#4-srcapiadvisorypy--advisory-rest-endpoint) |
| `docs/api-references/Gemini_api_doc.md` | Official Gemini SDK integration reference | [api-references/Gemini_api_doc.md](../api-references/Gemini_api_doc.md) |

---

## Modified Files

| File | What changed | LLD |
|---|---|---|
| `src/core/config.py` | Added `LLM_PROVIDER`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` to `Settings` class | [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |
| `src/services/market_data.py` | `@retry` applied to `_fetch_nsepython()` and `_fetch_yfinance()` inner closures; logger name aligned to `portfolio_assistant.market_data` | [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry) |
| `src/services/analytics_engine.py` | Logger name aligned from `"analytics_engine"` to `"portfolio_assistant.analytics_engine"` | [LLD 04 §4](./04_logging.md#4-services--logger-hierarchy-alignment) |
| `src/services/zerodha_client.py` | `retry_call()` applied to enctoken HTTP requests; `HTTPError` caught outside retry (fail-fast); logger name aligned to `"portfolio_assistant.zerodha_client"` | [LLD 05 §4](./05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry) |
| `src/api/analytics.py` | Added `logging.getLogger("portfolio_assistant.api.analytics")`; INFO lines with `xirr%`, `beta`, `sharpe`, `stcg`, `ltcg`; `exc_info=True` on all errors | [LLD 04 §3](./04_logging.md#analyticspy) |
| `src/api/auth.py` | Added `logging.getLogger("portfolio_assistant.api.auth")`; INFO lines for each OAuth flow step | [LLD 04 §3](./04_logging.md#authpy) |
| `src/api/holdings.py` | Added `logging.getLogger("portfolio_assistant.api.holdings")`; INFO line with `count`, `is_live`, `pnl`, `pnl%`; WARNING on Zerodha error message; `exc_info=True` on errors | [LLD 04 §3](./04_logging.md#holdingspy) |
| `src/main.py` | `setup_logging()` bootstrap at module load; `request_tracing_middleware` with `req_id`, elapsed ms, `X-Request-ID` header; `on_startup` / `on_shutdown` lifecycle events; advisory router registered | [LLD 04 §2](./04_logging.md#2-srcmainpy--request-tracing-middleware) |
| `src/ui/app.py` | `investment_goal` selectbox + `max_stock_cap` slider added to sidebar; advisory backend fetch added; `fetch_fallback_local()` extended for advisory endpoint; Tab 5 🤖 AI Advisory added; tab count `tab1–4` → `tab1–5` | [LLD 03 §6](./03_phase3_ai_advisory.md#6-srcuiapppy--ai-advisory-tab) |
| `requirements.txt` | Added `google-genai>=1.0.0` | [LLD 03 §7](./03_phase3_ai_advisory.md#7-requirementstxt) |
| `.env.example` | Added `GEMINI_API_KEY`, `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` with comments | [LLD 03 §8](./03_phase3_ai_advisory.md#8-envexample) |
| `.gitignore` | Added `logs/` and `*.log` entries | [LLD 04 §6](./04_logging.md#6-gitignore) |

---

## Deleted Files

| File | Reason |
|---|---|
| `docs/LOW_LEVEL_DESIGN.md` | Replaced by this split documentation set under `docs/lld/` |
