# Low-Level Design — Index

**Project:** Portfolio Assistant (Zerodha Integrated)

---

## Documents

| # | File | Phase | Contents |
|---|---|---|---|
| 1 | [01_phase1_auth_and_holdings.md](./01_phase1_auth_and_holdings.md) | Phase 1 | Config, Zerodha client wrapper, auth & holdings REST endpoints, FastAPI entrypoint |
| 2 | [02_phase2_analytics_engine.md](./02_phase2_analytics_engine.md) | Phase 2 | Market data service (4-tier fallback), quantitative analytics, tax harvesting, analytics REST endpoints |
| 3 | [03_phase3_ai_advisory.md](./03_phase3_ai_advisory.md) | Phase 3 | Rule engine, LLM advisor (Gemini/Ollama), Pydantic guardrails, advisory REST endpoint, UI tab, Gemini bug fixes |
| 4 | [04_logging.md](./04_logging.md) | Cross-cutting | Central logging setup, request tracing middleware, per-router log lines, logger hierarchy |
| 5 | [05_retry_and_fallback.md](./05_retry_and_fallback.md) | Cross-cutting | Shared retry utility, per-service retry policies, fail-fast rules, jitter rationale |
| 6 | [06_file_change_summary.md](./06_file_change_summary.md) | Session log | All files added/modified in the Phase 3 session with links to relevant LLD sections |

---

## File → LLD Coverage Map

| Source File | LLD Document(s) |
|---|---|
| `src/core/config.py` | [LLD 01 §1](./01_phase1_auth_and_holdings.md#1-srccoreconfpy--settings), [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings) |
| `src/core/logging_config.py` | [LLD 04 §1](./04_logging.md#1-srccorelogs_configpy--central-setup) |
| `src/core/retry.py` | [LLD 05 §2](./05_retry_and_fallback.md#2-srccoretrypy--shared-retry-utility) |
| `src/services/zerodha_client.py` | [LLD 01 §2](./01_phase1_auth_and_holdings.md#2-srcserviceszerodha_clientpy--zerodha-client-wrapper), [LLD 05 §4](./05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry) |
| `src/services/market_data.py` | [LLD 02 §1](./02_phase2_analytics_engine.md#1-srcservicesmarket_datapy--market-data-service), [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry) |
| `src/services/analytics_engine.py` | [LLD 02 §2](./02_phase2_analytics_engine.md#2-srcservicesanalytics_enginepy--quantitative-analytics-engine) |
| `src/services/tax_harvesting.py` | [LLD 02 §3](./02_phase2_analytics_engine.md#3-srcservicestax_harvestingpy--tax-harvesting-analyzer) |
| `src/services/rebalancer.py` | [LLD 03 §2](./03_phase3_ai_advisory.md#2-srcservicesrebalancerpy--deterministic-rule-engine) |
| `src/services/llm_advisor.py` | [LLD 03 §3](./03_phase3_ai_advisory.md#3-srcservicesllm_advisorpy--llm-advisory-service), [LLD 05 §5](./05_retry_and_fallback.md#5-llm_advisorpy--gemini--ollama-retry) |
| `src/api/auth.py` | [LLD 01 §3](./01_phase1_auth_and_holdings.md#3-srcapiauthpy--authentication-router), [LLD 04 §3](./04_logging.md#authpy) |
| `src/api/holdings.py` | [LLD 01 §4](./01_phase1_auth_and_holdings.md#4-srcapiholdingspy--holdings--portfolio-router), [LLD 04 §3](./04_logging.md#holdingspy) |
| `src/api/analytics.py` | [LLD 02 §4](./02_phase2_analytics_engine.md#4-srcapianalyticspy--analytics-router), [LLD 04 §3](./04_logging.md#analyticspy) |
| `src/api/advisory.py` | [LLD 03 §4](./03_phase3_ai_advisory.md#4-srcapiadvisorypy--advisory-rest-endpoint), [LLD 04 §3](./04_logging.md#advisorypy) |
| `src/main.py` | [LLD 01 §5](./01_phase1_auth_and_holdings.md#5-srcmainpy--fastapi-application-entry-point), [LLD 04 §2](./04_logging.md#2-srcmainpy--request-tracing-middleware) |

---

## Open Issues

*No active cross-cutting logger issues.* All loggers aligned to `portfolio_assistant.*` namespace.
