# FolioGuard — LinkedIn Content Campaign Roadmap & Playbook

> **Target Schedule:** 2 posts per week across 5 weeks (10-post series)  
> **Author & Creator:** Benoi Rajan  
> **Core Objective:** Establish technical authority, showcase end-to-end full-stack SaaS engineering, and attract engineering recruiters, engineering managers, and fintech founders.

---

## 📅 Campaign Calendar At-a-Glance

| Week | Post | Scheduled Day | Focus Area | Core Tech & Topics | Key Media Asset |
|:---:|:---:|:---:|:---|:---|:---|
| **Week 1** | **Post 1** | Tuesday | **Launch & Hero Announcement** | Full-Stack, Next.js 14, GCP Cloud Run | [01_landing_page.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/01_landing_page.png) |
| **Week 1** | **Post 2** | Thursday | **Hybrid Cloud Architecture** | Zero-infra-cost butterfly cloud, Vercel + GCP + Supabase + Upstash | System Architecture Diagram |
| **Week 2** | **Post 3** | Tuesday | **3-Stage AI Advisory Pipeline** | Google Gemini API, Pydantic guardrails, SSE streaming, multi-pass reasoning | [06_advisory_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png) |
| **Week 2** | **Post 4** | Thursday | **Dashboard & Data Visualization** | Next.js 14, Tailwind, Recharts, dark/light theme, institutional UX | Carousel: [02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) & [03_sector_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png) |
| **Week 3** | **Post 5** | Tuesday | **Zerodha Integration & Security** | Fernet AES-256, free `enctoken` session vs OAuth, PBKDF2 hashing | [02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) |
| **Week 3** | **Post 6** | Thursday | **Quantitative Risk Engine** | XIRR (Newton-Raphson), Sharpe, Sortino, Beta vs NIFTY 50, 4-tier fallback | [04_performance_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/04_performance_tab.png) |
| **Week 4** | **Post 7** | Tuesday | **Tax-Loss Harvesting (Budget 2024)** | STCG 20%, LTCG 12.5%, ₹1.25L exemption, holding period engine | [05_tax_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/05_tax_tab.png) |
| **Week 4** | **Post 8** | Thursday | **DevOps & Production CI/CD** | GitHub Actions, Docker, GCP Artifact Registry, Cloud Run, approval gates | CI/CD Pipeline Diagram |
| **Week 5** | **Post 9** | Tuesday | **Multi-Tenant DB & Scaling** | PostgreSQL 16, SQLAlchemy 2.0, Alembic, Redis rate limiting, row locks | Database ER Diagram |
| **Week 5** | **Post 10** | Thursday | **Lessons Learned & What's Next** | Solo engineering retrospectives, roadmap (Phase 4 & 6), call for opportunities | Product Roadmap Matrix / Mosaic |

---

## 🛠️ LinkedIn Content Playbook: Detailed Post Blueprints

---

### 📌 Post 1 — Launch & Hero Announcement (Week 1, Day 1)
- **Primary Message:** I built and deployed **FolioGuard**, a production AI-powered portfolio assistant for Indian equity investors.
- **Hook Idea:**
  > *"Most retail investors in India check their Zerodha Demat accounts, look at daily green/red P&L, and have no idea what their actual XIRR, portfolio Beta, or sector risk is. I decided to fix that."*
- **Key Technical Highlights:**
  - 10+ decoupled microservices, 49 automated test suites, fully deployed to production.
  - Live Next.js 14 frontend on Vercel Edge + Dockerized FastAPI backend on Google Cloud Run.
  - Built-in multi-stage AI advisory, automated Indian tax-loss harvesting, and real-time Demat sync.
- **Visual:** Landing Page showcase [01_landing_page.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/01_landing_page.png).
- **Call-to-Action (CTA):** "Explore the live demo here: [https://portfolio-assistant-rouge.vercel.app](https://portfolio-assistant-rouge.vercel.app). Check the code or drop your thoughts below!"
- **Hashtags:** `#buildinpublic #fintech #fullstack #nextjs #fastapi #python #ai`

---

### 📌 Post 2 — Hybrid Cloud Architecture with Zero Maintenance (Week 1, Day 2)
- **Primary Message:** How to design a scalable, serverless fintech architecture that runs within generous free tiers without sacrificing reliability.
- **Hook Idea:**
  > *"How do you build a cloud-native fintech platform handling live broker data, AI inference, and relational persistence with virtually zero monthly cloud bills? Here is the Hybrid Butterfly Architecture I designed for FolioGuard."*
- **Key Technical Highlights:**
  - **Edge Tier:** Next.js 14 App Router on Vercel Edge Network.
  - **Compute Tier:** Python FastAPI on GCP Cloud Run (`asia-south1` Mumbai) for auto-scaling serverless compute.
  - **Data Tier:** Supabase Managed PostgreSQL with transaction pooling (`:6543`), Upstash Serverless Redis for caching and sliding-window rate limiting.
  - **AI & Integrations:** Google Gemini API (`google-genai`), Zerodha Kite Connect SDK.
- **Visual:** Clean export of the architecture diagram:
```
  [ Next.js 14 (Vercel) ] -- Bearer JWT --> [ FastAPI (GCP Cloud Run) ]
                                                   |
             +--------------------+----------------+--------------------+
             |                    |                                     |
  [ Supabase Postgres ]   [ Upstash Redis ]                 [ Google Gemini AI ]
```
- **Hashtags:** `#systemdesign #cloudnative #gcp #vercel #softwarearchitecture #microservices`

---

### 📌 Post 3 — The 3-Stage AI Advisory Pipeline with Pydantic Guardrails (Week 2, Day 1)
- **Primary Message:** Why a single LLM prompt fails for financial advice, and how a deterministic-first, 3-stage pipeline solves it.
- **Hook Idea:**
  > *"Prompting ChatGPT to 'analyze my stock portfolio' is a recipe for hallucinations and financial disaster. Here is how I designed a 3-stage deterministic + LLM advisory pipeline with strict Pydantic schemas."*
- **Key Technical Highlights:**
  - **Pre-flight Rule Engine:** Runs first to evaluate hard boundaries (over-concentration >15%, 200-day SMA breakdowns).
  - **Stage 1 (Diagnosis):** Long-term health & macro risk audit (no trade decisions).
  - **Stage 2 (Screening):** Filters affordable candidates and validates valid NSE symbols against live market data.
  - **Stage 3 (Execution):** Enforces budget caps, whole-share allocations, and deterministic sanity guards.
  - **SSE Streaming:** FastAPI streams real-time stage progress to the Next.js UI using Server-Sent Events (`/advisory/stream`).
- **Visual:** Advisory Tab screenshot [06_advisory_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png) highlighting multi-stage progress.
- **Hashtags:** `#ai #generativeai #gemini #pydantic #python #promptengineering #fintech`

---

### 📌 Post 4 — Institutional Frontend UX with Next.js 14 & Recharts (Week 2, Day 2)
- **Primary Message:** Engineering an interactive, institutional-grade analytics dashboard with Next.js 14, Tailwind CSS, and Recharts.
- **Hook Idea:**
  > *"Data is useless if users can't digest it. When building FolioGuard, I wanted the interface to feel like Bloomberg Terminal meets modern Linear UI."*
- **Key Technical Highlights:**
  - Real-time KPI summary bar (XIRR, Beta, Total Investment, Current P&L).
  - Donut & bar charts for sector allocation, market cap tiering (Large/Mid/Small cap), and single-stock concentration.
  - Dark/Light mode theme switching with Tailwind and SSR hydration guards.
  - Dynamic CSV/Excel portfolio uploader with column normalization and instant cache re-validation.
- **Visual:** 2-slide carousel or side-by-side composite: [02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) & [03_sector_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png).
- **Hashtags:** `#frontend #nextjs #react #tailwindcss #datavisualization #recharts #uiux`

---

### 📌 Post 5 — Zerodha Demat Integration & End-to-End Encryption (Week 3, Day 1)
- **Primary Message:** Solving broker integration securely without forcing users to pay ₹2,000/month for developer API subscriptions.
- **Hook Idea:**
  > *"How do you connect live Zerodha holdings into an app without paying ₹2,000/month or risking user credentials? The engineering behind FolioGuard's broker ingestion layer."*
- **Key Technical Highlights:**
  - Dual auth modes: Official Kite OAuth 2.0 flow + lightweight free browser session (`enctoken`) ingestion.
  - **Fernet AES-256 Encryption at Rest:** Every broker token is encrypted with a dedicated key before hitting PostgreSQL (`user_sessions` table).
  - **Zero credential retention:** The server never stores user Demat passwords or plain-text secrets.
  - Automated security hardening: Constant-time comparison (`hmac.compare_digest`), scoped user quotas, and PBKDF2 salt hashing.
- **Visual:** Holdings Tab screenshot [02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png).
- **Hashtags:** `#security #cybersecurity #cryptography #zerodha #api #fintech #dataprivacy`

---

### 📌 Post 6 — Deterministic Quantitative Risk Engine (Week 3, Day 2)
- **Primary Message:** Financial math cannot be hallucinated. Building an exact quantitative analytics engine in Python.
- **Hook Idea:**
  > *"A 15% green portfolio can still be high-risk if its Beta is 1.8 and its Sharpe ratio is negative. Here is how I built FolioGuard's deterministic quantitative engine."*
- **Key Technical Highlights:**
  - **XIRR calculation:** Implemented via Newton-Raphson approximation on non-periodic cash flows.
  - **Risk Ratios:** Computes Sharpe Ratio (excess return over 10Y Indian G-Sec 7.10% risk-free rate) and Sortino Ratio (downside risk only).
  - **Portfolio Beta:** Calculated covariance against the NIFTY 50 benchmark index.
  - **4-Tier Market Data Resiliency:** KiteConnect → yfinance → NSE RSS / Public Scrapers → Local Cache fallback.
- **Visual:** Performance Tab screenshot [04_performance_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/04_performance_tab.png) showing the Beta Gauge and Valuation Matrix.
- **Hashtags:** `#quantitativefinance #python #numpy #math #investing #riskmanagement #nifty50`

---

### 📌 Post 7 — Indian Tax-Loss Harvesting Engine (Union Budget 2024 Rules) (Week 4, Day 1)
- **Primary Message:** Automating complex Indian taxation rules (STCG 20%, LTCG 12.5%) into an actionable tax-harvesting dashboard.
- **Hook Idea:**
  > *"Under the latest Union Budget 2024 amendments, equity taxation in India underwent significant shifts: STCG rose to 20% and LTCG to 12.5%. I automated tax-loss harvesting so investors don't leave money on the table before March 31st."*
- **Key Technical Highlights:**
  - Automatic classification of lots into STCG (< 365 days) and LTCG (> 365 days).
  - Dynamic progress tracking against the ₹1.25 Lakh annual LTCG tax-free exemption ceiling.
  - Automated detection of harvestable loss candidates to offset realized gains.
- **Visual:** Tax Tab screenshot [05_tax_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/05_tax_tab.png).
- **Hashtags:** `#taxes #incometax #taxharvesting #indiantax #unionbudget #wealthtech`

---

### 📌 Post 8 — Zero-Downtime CI/CD Pipeline & Deployments (Week 4, Day 2)
- **Primary Message:** Solo development doesn't mean skipping enterprise DevOps standards.
- **Hook Idea:**
  > *"Building alone shouldn't mean deploying blindly. Here is the automated GitHub Actions CI/CD pipeline I set up with quality gates, automated testing, and manual approval before touching production."*
- **Key Technical Highlights:**
  - **Quality Gates on Pull Requests:** 49 unit tests executed on Python + `npm run build` on Next.js.
  - **Manual Approval Gate:** Production environment requires sign-off before triggering Docker build.
  - **Artifacts & Compute:** Built image pushed to GCP Artifact Registry; zero-downtime rolling update pushed to Cloud Run.
  - Automated `/health` endpoint verification and instant one-click rollback mechanism.
- **Visual:** Flow diagram of GitHub Actions CI/CD Pipeline:
```
  PR / Commit ──> [ 49 Unit Tests + Next.js Build ]
                                 │
                         (Passes Gates)
                                 ▼
                     [ Manual Approval Gate ]
                                 │
                            (Approved)
                                 ▼
         [ Docker Build ] ──> [ Artifact Registry ] ──> [ Cloud Run Deploy ] ──> [ Health Check ✓ ]
```
- **Hashtags:** `#devops #cicd #githubactions #docker #googlecloud #cloudrun #automation`

---

### 📌 Post 9 — Multi-Tenant PostgreSQL Schema & Concurrency Handling (Week 5, Day 1)
- **Primary Message:** Architecting a relational data layer that isolates multi-tenant user portfolios and handles concurrent AI quota deductions safely.
- **Hook Idea:**
  > *"When scaling a multi-tenant SaaS, dirty reads and race conditions around quotas or sessions will break your app. Here is how I designed FolioGuard's database layer with PostgreSQL, SQLAlchemy 2.0, and Alembic."*
- **Key Technical Highlights:**
  - Normalized schema: `users`, `portfolios`, `user_holdings`, `user_sessions`, `staged_orders`, `subscriptions`.
  - Transaction pooling using Supabase Pooler (`port 6543`) to prevent connection starvation in serverless environments.
  - Atomic AI quota tracking using PostgreSQL row-level locks (`SELECT ... FOR UPDATE`) to prevent concurrent quota bypassing.
  - Centralized database migrations version-controlled via Alembic revisions.
- **Visual:** Entity-Relationship (ER) diagram of the schema.
- **Hashtags:** `#postgresql #database #sqlalchemy #alembic #sql #backendengineering #systemdesign`

---

### 📌 Post 10 — Retrospective, Lessons Learned & What's Next (Week 5, Day 2)
- **Primary Message:** Reflection on building an institutional SaaS from 0 to 1, open-source highlights, and what's on the horizon.
- **Hook Idea:**
  > *"After 7 distinct phases, 10,000+ lines of clean code, and weeks of iterative development, FolioGuard is live. Here are the 3 biggest technical lessons I learned building a complete fintech SaaS solo."*
- **Key Technical Highlights:**
  - Lesson 1: Deterministic rules must always supervise LLMs in financial contexts.
  - Lesson 2: Designing for zero infrastructure cost forces superior architecture decisions.
  - Lesson 3: E2E and unit test suites are the only way to ship fast with confidence as a solo builder.
  - **Roadmap Preview:** Human-in-the-loop Order Staging Queue (Phase 4), CAS Statement Universal Ingestion (Phase 6), and Razorpay SaaS monetization (Phase 7).
  - Open call for connections, discussions, and technical opportunities.
- **Visual:** Comprehensive collage or roadmap matrix showing completed vs upcoming milestones.
- **Hashtags:** `#buildinpublic #techcareers #fullstack #fintech #softwareengineering #opentowork`

---

## 💡 Practical Execution Tips for LinkedIn Algorithm Success

1. **Link in First Comment vs Post Body:** LinkedIn tends to limit reach on posts containing external links in the main caption. You can write: *"Link to the live app & repo in the first comment 👇"* or include it at the very bottom of the post.
2. **Exporting Mermaid Diagrams to Images:**
   - Copy the Mermaid snippets from `docs/architecture/HLD.md` or this document.
   - Paste them into [mermaid.live](https://mermaid.live) or [eraser.io](https://eraser.io) or [excalidraw.com](https://excalidraw.com).
   - Export as high-resolution PNG (2x or 3x scale) with a clean dark or light background.
3. **Screenshots Format:** Crop browser chrome slightly or keep full-width window view. The pre-captured screenshots in `.reports/e2e_screenshots/` are already 1080p full-page renders.
4. **Ideal Posting Times (IST):**
   - Tuesday & Thursday mornings: **8:30 AM – 10:30 AM IST** or evenings **6:30 PM – 8:30 PM IST**.
5. **Engage with Early Commenters:** Reply to comments within the first 60 minutes to boost feed distribution.
