---
name: e2e-live-testing
description: Comprehensive live end-to-end test runner for FolioGuard. Triggers automated browser and API verification across landing page, tenant auth, holdings, sector charts, risk performance, tax harvesting, and 3-stage AI advisory whenever the user mentions "run live e2e", "e2e test", "test live", "run full e2e", "live testing", "e2e", or asks to test the application end to end in live mode.
---

# Live End-to-End Testing Skill (`e2e-live-testing`)

This skill governs the automated, live, multi-tier End-to-End (E2E) testing workflow for FolioGuard. It drives real headless browser interaction (via Playwright / Chrome) and live API requests against the running stack without mocks.

---

## 🚀 Trigger Keywords

Activate this skill immediately whenever the user says or requests:
* `"run live e2e"` or `"live e2e"`
* `"test live"` or `"live test"`
* `"run full end to end"` or `"full e2e test"`
* `"e2e test"` or `"test e2e"`
* `"e2e"`

---

## 📋 Execution Protocol

### Step 1: Verify Dev Services Are Running
Before executing tests, check that both the backend API and frontend dev server are active:
* **Backend API**: `http://127.0.0.1:8000/health` (FastAPI with PostgreSQL + Redis)
  * If offline: Launch via `backend/run_dev.sh`
* **Frontend UI**: `http://localhost:3000` (Next.js App Router)
  * If offline: Launch via `npm run dev` in `frontend/`

### Step 2: Execute the Automated E2E Runner
Run the root test suite script:
```bash
./test_live_e2e.sh
```

### Step 3: What the E2E Suite Validates
The script executes 7 sequential live verification checkpoints:
1. **Landing Page & Budget 2024 Banner**: Verifies hero section, navigation links, and FY 2024-25 STCG/LTCG announcement notice.
2. **Authentication & Tenant Authorization**: Injects PRO JWT token for tenant `benoirajan@gmail.com` and verifies authenticated session.
3. **Holdings Table & Live Search**: Verifies all 9 portfolio holdings (`BEL`, `BHARTIARTL`, `ICICIBANK`, `INFY`, `ITC`, `ONGC`, `RELIANCE`, `SUNPHARMA`, `TCS`), real-time LTPs, P&L calculations, and dynamic search filtering.
4. **Sector Allocation & Concentration**: Verifies doughnut allocation chart, market cap weights, and single-stock concentration bars.
5. **Quantitative Performance**: Verifies deterministic mathematical formulas (XIRR, Sharpe Ratio, Sortino Ratio, Beta vs NIFTY 50, Herfindahl HHI index).
6. **Union Budget 2024 Tax Harvesting**: Verifies updated 20% STCG and 12.5% LTCG rates, ₹1.25 Lakh exemption headroom, and harvestable loss candidates.
7. **3-Stage AI Advisory Pipeline**: Clicks "Run 3-Stage AI Advisory", streams real-time SSE reasoning through Gemini (`gemini-3.1-flash-lite`), verifies Stage 1 (Audit), Stage 2 (Conviction), Stage 3 (Bounded whole-share buy order), and Zerodha basket staging.

### Step 4: Visual Artifacts & Reporting
* Verification screenshots are saved automatically in `.reports/e2e_screenshots/`:
  * `01_landing_page.png`
  * `02_holdings_tab.png`
  * `03_sector_tab.png`
  * `04_performance_tab.png`
  * `05_tax_tab.png`
  * `06_advisory_tab.png`
* Present the completed test matrix with green/red status indicators to the user.
