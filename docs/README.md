# Documentation

**Project:** Portfolio Assistant (Zerodha Integrated)

---

## Structure

```
docs/
├── README.md                          ← this file
├── architecture/
│   ├── HLD.md                         ← System architecture, data flow, DB schema, security
│   ├── ARCHITECTURE_REVIEW.md         ← Design review: critical issues, gaps, recommendations
│   └── HYBRID_DEPLOYMENT_PLAN.md      ← Vercel + GCP Cloud Run + Supabase deployment architecture
├── lld/
│   ├── 00_INDEX.md                    ← LLD index + file-to-document coverage map
│   ├── 01_phase1_auth_and_holdings.md ← Config, Zerodha client, auth & holdings APIs
│   ├── 02_phase2_analytics_engine.md  ← Market data, analytics, tax harvesting APIs
│   ├── 03_phase3_ai_advisory.md       ← Rule engine, LLM advisor, advisory API
│   ├── 04_logging.md                  ← Logging setup, middleware, log lines
│   ├── 05_retry_and_fallback.md       ← Retry utility, per-service policies
│   └── 06_file_change_summary.md      ← Session change log (Phase 3)
├── plans/
│   ├── phase_1_authentication_and_holdings.md
│   ├── phase_2_fundamental_and_sector_analytics.md
│   ├── phase_3_ai_advisory_engine.md
│   ├── phase_4_order_staging_and_alerts.md
│   ├── phase_5_react_frontend.md
│   ├── phase_6_multi_tenant_and_universal_ingestion.md
│   └── phase_7_monetization_and_saas.md
├── guides/
│   ├── USER_GUIDE.md                  ← How to use the dashboard (end-user guide)
│   ├── TUTORIAL.md                    ← Developer setup tutorial (install → run)
│   └── zerodha_api_setup_guide.md     ← Free vs paid Zerodha API, enctoken setup
└── api-references/
    └── Gemini_api_doc.md              ← Google Gemini SDK integration reference
```

---

## Where to Start

| I want to... | Go to |
|---|---|
| Understand the overall system | [architecture/HLD.md](./architecture/HLD.md) |
| Read Hybrid Cloud Deployment plan | [architecture/HYBRID_DEPLOYMENT_PLAN.md](./architecture/HYBRID_DEPLOYMENT_PLAN.md) |
| See known design issues and recommendations | [architecture/ARCHITECTURE_REVIEW.md](./architecture/ARCHITECTURE_REVIEW.md) |
| Find the LLD for a specific source file | [lld/00_INDEX.md — Coverage Map](./lld/00_INDEX.md#file--lld-coverage-map) |
| Read Phase 1 implementation details | [lld/01_phase1_auth_and_holdings.md](./lld/01_phase1_auth_and_holdings.md) |
| Read Phase 2 implementation details | [lld/02_phase2_analytics_engine.md](./lld/02_phase2_analytics_engine.md) |
| Read Phase 3 implementation details | [lld/03_phase3_ai_advisory.md](./lld/03_phase3_ai_advisory.md) |
| Understand logging setup and log lines | [lld/04_logging.md](./lld/04_logging.md) |
| Understand retry policies | [lld/05_retry_and_fallback.md](./lld/05_retry_and_fallback.md) |
| Use the dashboard as a user | [guides/USER_GUIDE.md](./guides/USER_GUIDE.md) |
| Get started end-to-end (developer) | [guides/TUTORIAL.md](./guides/TUTORIAL.md) |
| Set up Zerodha API access | [guides/zerodha_api_setup_guide.md](./guides/zerodha_api_setup_guide.md) |
| Reference the Gemini SDK | [api-references/Gemini_api_doc.md](./api-references/Gemini_api_doc.md) |
| See Multi-Tenant & Ingestion plan | [plans/phase_6_multi_tenant_and_universal_ingestion.md](./plans/phase_6_multi_tenant_and_universal_ingestion.md) |
| See Monetization & SaaS plan | [plans/phase_7_monetization_and_saas.md](./plans/phase_7_monetization_and_saas.md) |

---

## Phase Status

| Phase | Plan | LLD | Code | Status |
|---|---|---|---|---|
| Phase 1 — Auth & Holdings | [plan](./plans/phase_1_authentication_and_holdings.md) | [lld](./lld/01_phase1_auth_and_holdings.md) | ✅ | Complete (partial — no DB/Redis/Scheduler) |
| Phase 2 — Analytics Engine | [plan](./plans/phase_2_fundamental_and_sector_analytics.md) | [lld](./lld/02_phase2_analytics_engine.md) | ✅ | Complete |
| Phase 3 — AI Advisory | [plan](./plans/phase_3_ai_advisory_engine.md) | [lld](./lld/03_phase3_ai_advisory.md) | ✅ | Complete |
| Phase 4 — Order Staging & Alerts | [plan](./plans/phase_4_order_staging_and_alerts.md) | — | ❌ | Not started |
| Phase 5 — React Frontend | [plan](./plans/phase_5_react_frontend.md) | [lld](./lld/07_phase5_react_frontend.md) | ✅ | In progress (`feature/react-frontend`) |
| Phase 6 — Multi-Tenant & Ingestion | [plan](./plans/phase_6_multi_tenant_and_universal_ingestion.md) | — | ❌ | Planned |
| Phase 7 — Monetization & SaaS | [plan](./plans/phase_7_monetization_and_saas.md) | — | ❌ | Planned |
