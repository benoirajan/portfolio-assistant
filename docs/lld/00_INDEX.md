# Low-Level Design — Index

**Project:** Portfolio Assistant (Zerodha Integrated)
**Branch:** `feat/phase3-assistant`
**Scope:** Phase 3 AI Advisory Engine, Logging Infrastructure, Exponential Retry & Fallback

---

## Documents

| # | File | Contents |
|---|---|---|
| 1 | [01_phase3_ai_advisory.md](./01_phase3_ai_advisory.md) | Phase 3 AI Advisory Engine — config, rule engine, LLM advisor, REST endpoint, UI tab, Gemini API bug fixes |
| 2 | [02_logging.md](./02_logging.md) | Logging infrastructure — central setup, request tracing middleware, router log lines, logger hierarchy |
| 3 | [03_retry_and_fallback.md](./03_retry_and_fallback.md) | Exponential retry & fallback — shared utility, per-service retry policies |
| 4 | [04_file_change_summary.md](./04_file_change_summary.md) | Complete file change summary — all 19 files with new/modified status |

---

## Quick Reference — New Files Added This Session

| File | Purpose |
|---|---|
| `src/core/config.py` | +4 LLM settings fields |
| `src/core/logging_config.py` | Central logging bootstrap |
| `src/core/retry.py` | Shared exponential backoff utility |
| `src/services/rebalancer.py` | Deterministic portfolio rule engine |
| `src/services/llm_advisor.py` | Gemini/Ollama advisory + Pydantic guardrails |
| `src/api/advisory.py` | `GET /api/v1/advisory/recommendations` |
| `docs/Gemini_api_doc.md` | Official Gemini SDK reference |
| `docs/lld/` | This documentation set |
