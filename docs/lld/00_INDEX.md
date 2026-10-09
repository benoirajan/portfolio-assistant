# Low-Level Design — Index

**Project:** Portfolio Assistant (Zerodha Integrated)

---

## Documents

| # | File | Phase | Contents |
|---|---|---|---|
| 1 | [01_phase1_auth_and_holdings.md](./01_phase1_auth_and_holdings.md) | Phase 1 | Config, Zerodha client wrapper, auth & holdings REST endpoints, FastAPI entrypoint |
| 2 | [02_phase2_analytics_engine.md](./02_phase2_analytics_engine.md) | Phase 2 | Market data service (4-tier fallback), quantitative analytics, tax harvesting, analytics REST endpoints |
| 3 | [03_phase3_ai_advisory.md](./03_phase3_ai_advisory.md) | Phase 3 | Rule engine, LLM advisor (Gemini/Ollama), Pydantic guardrails, advisory REST endpoint, trade basket endpoint, UI tab, Gemini bug fixes |
| 4 | [04_logging.md](./04_logging.md) | Cross-cutting | Central logging setup, request tracing middleware, per-router log lines, logger hierarchy |
| 5 | [05_retry_and_fallback.md](./05_retry_and_fallback.md) | Cross-cutting | Shared retry utility, per-service retry policies, fail-fast rules, jitter rationale |
| 6 | [06_file_change_summary.md](./06_file_change_summary.md) | Session log | All files added/modified in the Phase 3 session with links to relevant LLD sections |
| 7 | [07_phase5_react_frontend.md](./07_phase5_react_frontend.md) | Phase 5 | Next.js app structure, all components, hooks, API client, type definitions |
| 8 | [08_cache_layer.md](./08_cache_layer.md) | Cross-cutting | Redis cache client, key conventions, TTLs, graceful degradation, token security |
| 9 | [09_database_persistence.md](./09_database_persistence.md) | Phase 6 & P0 | Managed Supabase PostgreSQL, SQLAlchemy 2.0 ORM, Alembic migrations, test pipeline |
| 10 | [10_multi_tenant_auth.md](./10_multi_tenant_auth.md) | Phase 6 & P0 | Multi-tenant auth, Google IAM, PBKDF2 passwords, Fernet AES-256 broker encryption, SSE auth |
| 11 | [11_saas_monetization.md](./11_saas_monetization.md) | Phase 7 & P1 | SaaS monetization, tier gating, Razorpay integration, Redis AI quota rate limiting |

---

## File → LLD Coverage Map

| Source File | LLD Document(s) |
|---|---|
| `src/core/security.py` | [LLD 10 §2](./10_multi_tenant_auth.md#2-key-architecture-components), [LLD 10 §4](./10_multi_tenant_auth.md#4-dual-transport-authentication-get_current_user) |
| `src/core/config.py` | [LLD 01 §1](./01_phase1_auth_and_holdings.md#1-srccoreconfpy--settings), [LLD 03 §1](./03_phase3_ai_advisory.md#1-srccoreconfpy--llm-settings), [LLD 09 §2](./09_database_persistence.md#2-database-engine--session-manager-srcdbsessionpy), [LLD 10 §3](./10_multi_tenant_auth.md#3-broker-credential-security--in-memory-resolution) |
| `src/db/base.py` | [LLD 09 §2](./09_database_persistence.md#2-database-engine--session-manager-srcdbsessionpy) |
| `src/db/session.py` | [LLD 09 §2](./09_database_persistence.md#2-database-engine--session-manager-srcdbsessionpy), [LLD 10 §2](./10_multi_tenant_auth.md#2-key-architecture-components) |
| `src/models/*` | [LLD 09 §3](./09_database_persistence.md#3-sqlalchemy-20-orm-models-srcmodels), [LLD 10 §3](./10_multi_tenant_auth.md#3-broker-credential-security--in-memory-resolution) |
| `src/services/portfolio_repository.py` | [LLD 09 §4](./09_database_persistence.md#4-repository-layer--fallback-mechanics-srcservicesportfolio_repositorypy), [LLD 10 §3](./10_multi_tenant_auth.md#3-broker-credential-security--in-memory-resolution) |
| `run_dev.sh` | [LLD 09 §5](./09_database_persistence.md#5-development-runner-pipeline-backendrun_devsh) |
| `tests/test_portfolio.py` | [LLD 09 §6](./09_database_persistence.md#6-comprehensive-test-suite-teststest_portfoliopy) |
| `tests/test_security.py` | [LLD 10 §2](./10_multi_tenant_auth.md#2-key-architecture-components) |
| `tests/test_auth.py` | [LLD 10 §5](./10_multi_tenant_auth.md#5-api-endpoints-reference) |
| `src/core/logging_config.py` | [LLD 04 §1](./04_logging.md#1-srccorelogs_configpy--central-setup) |
| `src/core/retry.py` | [LLD 05 §2](./05_retry_and_fallback.md#2-srccoretrypy--shared-retry-utility) |
| `src/core/cache.py` | [LLD 08 §1](./08_cache_layer.md#1-backendsrccorecachepy--cache-client) |
| `src/services/zerodha_client.py` | [LLD 01 §2](./01_phase1_auth_and_holdings.md#2-srcserviceszerodha_clientpy--zerodha-client-wrapper), [LLD 05 §4](./05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry) |
| `src/services/market_data.py` | [LLD 02 §1](./02_phase2_analytics_engine.md#1-srcservicesmarket_datapy--market-data-service), [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry) |
| `src/services/analytics_engine.py` | [LLD 02 §2](./02_phase2_analytics_engine.md#2-srcservicesanalytics_enginepy--quantitative-analytics-engine) |
| `src/services/tax_harvesting.py` | [LLD 02 §3](./02_phase2_analytics_engine.md#3-srcservicestax_harvestingpy--tax-harvesting-analyzer) |
| `src/services/rebalancer.py` | [LLD 03 §2](./03_phase3_ai_advisory.md#2-srcservicesrebalancerpy--deterministic-rule-engine) |
| `src/services/llm_advisor.py` | [LLD 03 §3](./03_phase3_ai_advisory.md#3-srcservicesllm_advisorpy--llm-advisory-service), [LLD 05 §5](./05_retry_and_fallback.md#5-llm_advisorpy--gemini--ollama-retry) |
| `src/api/auth.py` | [LLD 01 §3](./01_phase1_auth_and_holdings.md#3-srcapiauthpy--authentication-router), [LLD 04 §3](./04_logging.md#authpy) |
| `src/api/holdings.py` | [LLD 01 §4](./01_phase1_auth_and_holdings.md#4-srcapiholdingspy--holdings--portfolio-router), [LLD 04 §3](./04_logging.md#holdingspy) |
| `src/api/analytics.py` | [LLD 02 §4](./02_phase2_analytics_engine.md#4-srcapianalyticspy--analytics-router), [LLD 04 §3](./04_logging.md#analyticspy) |
| `src/api/advisory.py` | [LLD 03 §4](./03_phase3_ai_advisory.md#4-srcapiadvisorypy--advisory-rest-endpoint), [LLD 03 §9](./03_phase3_ai_advisory.md#9-trade-basket-feature), [LLD 04 §3](./04_logging.md#advisorypy) |
| `frontend/lib/types.ts` | [LLD 07 §1](./07_phase5_react_frontend.md#1-frontendlibtypests--typescript-type-definitions) — adds `BasketItem`, `BasketResponse` |
| `frontend/lib/api.ts` | [LLD 07 §2](./07_phase5_react_frontend.md#2-frontendlibapits--axios-client--api-functions) — adds `createBasket(recommendations, budget)` |
| `frontend/hooks/usePortfolio.ts` | [LLD 07 §3](./07_phase5_react_frontend.md#3-frontendhooksuseportfoliots--react-query-hooks) |
| `frontend/app/layout.tsx` | [LLD 07 §4](./07_phase5_react_frontend.md#4-frontendapplayouttsx--root-layout) |
| `frontend/components/theme/ThemeProvider.tsx` | [LLD 07 §4](./07_phase5_react_frontend.md#4-frontendapplayouttsx--root-layout) |
| `frontend/components/layout/Header.tsx` | [LLD 07 §5](./07_phase5_react_frontend.md#5-frontendcomponentslayoutheadertsx--themetoggletsx) |
| `frontend/components/layout/ThemeToggle.tsx` | [LLD 07 §5](./07_phase5_react_frontend.md#5-frontendcomponentslayoutheadertsx--themetoggletsx) |
| `frontend/components/layout/Sidebar.tsx` | [LLD 07 §6](./07_phase5_react_frontend.md#6-frontendcomponentslayoutsidebartsx) |
| `frontend/components/kpi/KpiBar.tsx` | [LLD 07 §7](./07_phase5_react_frontend.md#7-frontendcomponentskpikpibartsx) |
| `frontend/components/tabs/HoldingsTab.tsx` | [LLD 07 §8](./07_phase5_react_frontend.md#8-frontendcomponentstabsholdingstabtsx) |
| `frontend/components/tabs/SectorTab.tsx` | [LLD 07 §9](./07_phase5_react_frontend.md#9-frontendcomponentstabssectortabtsx) |
| `frontend/components/tabs/PerformanceTab.tsx` | [LLD 07 §10](./07_phase5_react_frontend.md#10-frontendcomponentstabsperformancetabtsx) |
| `frontend/components/tabs/TaxTab.tsx` | [LLD 07 §11](./07_phase5_react_frontend.md#11-frontendcomponentstabstaxtabtsx) |
| `frontend/components/tabs/AdvisoryTab.tsx` | [LLD 07 §12](./07_phase5_react_frontend.md#12-frontendcomponentstabsadvisorytabtsx) — adds basket budget input + basket table |
| `frontend/app/dashboard/page.tsx` | [LLD 07 §13](./07_phase5_react_frontend.md#13-frontendappdashboardpagetsx--dashboard-page) |
| `frontend/app/page.tsx` | [LLD 07 §14](./07_phase5_react_frontend.md#14-frontendapppagetsx--public-marketing-landing-page) |

---

## Open Issues

*No active cross-cutting logger issues.* All loggers aligned to `portfolio_assistant.*` namespace.
