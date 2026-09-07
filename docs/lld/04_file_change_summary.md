# LLD 04 — File Change Summary

**Session:** Phase 3 AI Advisory Engine + Logging + Retry & Fallback
**Branch:** `feat/phase3-assistant`
**Total files touched:** 19

---

## New Files

| File | Purpose |
|---|---|
| `src/core/logging_config.py` | Central logging bootstrap — console + rotating file handlers, third-party suppression, `portfolio_assistant.*` hierarchy |
| `src/core/retry.py` | Shared exponential backoff utility — `@retry` decorator and `retry_call()` with jitter and fail-fast logic |
| `src/services/rebalancer.py` | Deterministic portfolio rule engine — 3 rules (`OVER_CONCENTRATION`, `UNDERPERFORMANCE`, `SECTOR_OVERWEIGHT`), structured flag output |
| `src/services/llm_advisor.py` | Full LLM advisory pipeline — Gemini/Ollama integration, data minimization prompt builder, Pydantic guardrails, rule-based fallback |
| `src/api/advisory.py` | `GET /api/v1/advisory/recommendations` — investment goal + concentration cap params, enctoken header |
| `docs/Gemini_api_doc.md` | Official Gemini SDK integration reference (created by user; model table updated from `gemini-2.5-flash` to `gemini-3.6-flash`) |
| `docs/lld/00_INDEX.md` | Master index for this documentation set |
| `docs/lld/01_phase3_ai_advisory.md` | This document set — Phase 3 detail |
| `docs/lld/02_logging.md` | This document set — Logging detail |
| `docs/lld/03_retry_and_fallback.md` | This document set — Retry detail |
| `docs/lld/04_file_change_summary.md` | This file |

---

## Modified Files

| File | What changed |
|---|---|
| `src/core/config.py` | Added `LLM_PROVIDER`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` to `Settings` class |
| `src/services/market_data.py` | `@retry` applied to `_fetch_nsepython()` and `_fetch_yfinance()` inner closures; logger name aligned to `portfolio_assistant.market_data` |
| `src/services/analytics_engine.py` | Logger name aligned from `"analytics_engine"` to `"portfolio_assistant.analytics_engine"` |
| `src/services/zerodha_client.py` | `retry_call()` applied to enctoken HTTP requests; `HTTPError` caught outside retry (fail-fast); logger name aligned to `"portfolio_assistant.zerodha_client"` |
| `src/api/analytics.py` | Added `logging.getLogger("portfolio_assistant.api.analytics")`; INFO lines with `xirr%`, `beta`, `sharpe`, `stcg`, `ltcg`; `exc_info=True` on all errors |
| `src/api/auth.py` | Added `logging.getLogger("portfolio_assistant.api.auth")`; INFO lines for each OAuth flow step |
| `src/api/holdings.py` | Added `logging.getLogger("portfolio_assistant.api.holdings")`; INFO line with `count`, `is_live`, `pnl`, `pnl%`; WARNING on Zerodha error message; `exc_info=True` on errors |
| `src/main.py` | `setup_logging()` bootstrap at module load; `request_tracing_middleware` with `req_id`, elapsed ms, `X-Request-ID` header; `on_startup` / `on_shutdown` lifecycle events; advisory router registered |
| `src/ui/app.py` | `investment_goal` selectbox + `max_stock_cap` slider added to sidebar; advisory backend fetch added; `fetch_fallback_local()` extended for advisory endpoint; Tab 5 🤖 AI Advisory added; tab count `tab1–4` → `tab1–5` |
| `requirements.txt` | Added `google-genai>=1.0.0` |
| `.env.example` | Added `GEMINI_API_KEY`, `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` with comments |
| `.gitignore` | Added `logs/` and `*.log` entries |

---

## Deleted Files

| File | Reason |
|---|---|
| `docs/LOW_LEVEL_DESIGN.md` | Replaced by this split documentation set under `docs/lld/` |
