# Implementation Plan: Multi-Stage AI Advisory Pipeline with Budget-Bounded Execution

**Target Components:**
- Backend Service: `backend/src/services/llm_advisor.py`
- Backend Web Search & Market Data: `backend/src/services/market_data.py`, `backend/src/services/news_search.py`
- Backend API Router: `backend/src/api/advisory.py`
- React Frontend: `frontend/components/tabs/AdvisoryTab.tsx`, `frontend/components/advisory/`
- React Frontend Types & Hooks: `frontend/lib/types.ts`, `frontend/hooks/usePortfolio.ts`

---

## 1. Goal & Architectural Design

Upgrade the single-pass AI advisory engine into a **3-stage interactive prompt pipeline** based on `prompt1.md`, `Prompt2.md`, and `prompt3.md`. 

Prioritizing **analysis quality over latency**, the feature uses an **interactive step-by-step wizard** in the React UI powered by **Server-Sent Events (SSE) / live streaming progress feedback**, providing the user with real-time feedback (e.g. *"🔍 Fetching live market news...", "📊 Auditing sector concentration..."*) while deep reasoning takes place.

### The 3-Stage Pipeline:
1. **Stage 1 — Portfolio & Market Health Audit (`prompt1.md`):** Diagnostic audit of holdings, sector concentration, hidden economic exposure, governance, and live macroeconomic/company news (via web search). *Strictly forbids trade execution or allocation recommendations.*
2. **Stage 2 — Opportunity Screening & Conviction Matrix (`Prompt2.md`):** Identifies and ranks candidates across 4 conviction tiers (🟢 High Conviction, 🟢 Good Opportunity, 🟡 Watchlist, 🔴 Avoid for Now). Compares existing holdings vs new Indian equity candidates (validated against official NSE/BSE master lists). Evaluates opportunity cost and incremental portfolio benefit.
3. **Stage 3 — Bounded Execution Plan (`prompt3.md`):** Takes explicit user inputs (**total budget ₹**, monthly investment capacity, schedule frequency) and makes the final execution decision (**INVEST FULL**, **PARTIAL INVEST**, or **₹0 WAIT**). Calculates whole-share purchase quantities, cash buffer retention, and explicitly details *"Why not the others?"*.

---

## 2. Technical Implementation Details

### A. Live Web Search & Fundamentals Layer
- **New Service (`backend/src/services/news_search.py`):** Integrates live market search grounding (Google Search / DuckDuckGo News API) to fetch recent earnings results, regulatory updates, and macro news for Stage 1 & Stage 3.
- **Data Enrichment (`backend/src/services/market_data.py`):** Expands holdings data with `roce_pct`, `fcf_yield_pct`, `debt_to_equity`, `peg_ratio`, `forward_pe`, `promoter_holding_pct`, and `promoter_pledge_pct`.
- **Ticker Master Validation:** Validates suggested new stock symbols in Stage 2 against the official Zerodha NSE/BSE master instrument list to guarantee zero hallucinated tickers.

---

### B. Backend Advisory Service & Streaming API
- **Stage Builders in `backend/src/services/llm_advisor.py`:**
  - `_build_stage1_prompt()`: Portfolio audit + web search news context.
  - `_build_stage2_prompt()`: Opportunity screening + fit matrix + ticker validation.
  - `_build_stage3_prompt()`: Execution decision + cash buffer math + whole-share allocation.
- **Server-Sent Events (SSE) Endpoint in `backend/src/api/advisory.py`:**
  - `GET /api/v1/advisory/stream`: Streams live progress events and intermediate stage results to the React frontend:
    ```json
    {"stage": 1, "status": "running", "message": "🔍 Fetching live NSE market announcements and sector news..."}
    {"stage": 1, "status": "complete", "data": {...}}
    {"stage": 2, "status": "running", "message": "🔎 Screening Indian equity universe against underrepresented sectors..."}
    {"stage": 2, "status": "complete", "data": {...}}
    {"stage": 3, "status": "running", "message": "🧮 Calculating whole-share allocation & cash buffer..."}
    {"stage": 3, "status": "complete", "data": {...}}
    ```

---

### C. React Frontend Interactive Wizard (`frontend/components/tabs/AdvisoryTab.tsx`)
- **Step 1: User Inputs Form**
  - Investment Budget for today (e.g. ₹5,000)
  - Monthly Investment Capacity (e.g. ₹10,000/month)
  - Investment Schedule (`Bi-weekly ₹5,000`, `Monthly Lump-sum ₹10,000`, `Custom`)
  - Risk & Growth Objective (`Moderate Growth`, `Aggressive Growth`, `Capital Preservation`, `Balanced`)
  - `Allow New Stock Screening` toggle
- **Step 2: Interactive Stepper & Live Streaming Progress**
  - **Live Progress Animation Bar:** Displays active sub-task status comments with smooth loading spinners/pulse effects.
  - **Stage 1 Card:** Baseline Diagnosis, Sector Health Badge, Overlapping Risk Summary.
  - **Stage 2 Conviction Grid:** 4-tier color-coded cards (🟢 High Conviction, 🟢 Good Opportunity, 🟡 Watchlist, 🔴 Avoid) comparing existing vs. new stock ideas.
  - **Stage 3 Execution Panel:** `INVEST FULL` / `PARTIAL INVEST` / `WAIT` status badge, cash buffer metric, whole-share buy table, "Why not the others?" rationale, and **Push to Zerodha Basket** button.

---

## 3. Proposed File Modifications

#### [MODIFY] [market_data.py](file:///home/benoi/Projects/portfolio_assistant/backend/src/services/market_data.py)
* Add fundamental ratio enrichment (`roce_pct`, `fcf_yield`, `debt_to_equity`, `peg_ratio`, `promoter_pledge_pct`).
* Add Zerodha master ticker list validator.

#### [NEW] [news_search.py](file:///home/benoi/Projects/portfolio_assistant/backend/src/services/news_search.py)
* Live web search & news fetcher for stock symbols and Indian equity macro trends.

#### [MODIFY] [llm_advisor.py](file:///home/benoi/Projects/portfolio_assistant/backend/src/services/llm_advisor.py)
* Refactor into `_build_stage1_prompt()`, `_build_stage2_prompt()`, and `_build_stage3_prompt()`.
* Add Pydantic guardrail models for Stage 1, Stage 2, and Stage 3.

#### [MODIFY] [advisory.py](file:///home/benoi/Projects/portfolio_assistant/backend/src/api/advisory.py)
* Update `/recommendations` to accept `total_budget`, `monthly_capacity`, `investment_schedule`, and `allow_new_stocks`.
* Add SSE streaming endpoint `GET /api/v1/advisory/stream` for live UI progress updates.

#### [MODIFY] [AdvisoryTab.tsx](file:///home/benoi/Projects/portfolio_assistant/frontend/components/tabs/AdvisoryTab.tsx)
#### [MODIFY] [types.ts](file:///home/benoi/Projects/portfolio_assistant/frontend/lib/types.ts)
#### [MODIFY] [usePortfolio.ts](file:///home/benoi/Projects/portfolio_assistant/frontend/hooks/usePortfolio.ts)
* Build interactive stepper wizard with live SSE progress animations, stage breakdown cards, and Zerodha basket export.

---

## 4. Verification Plan

### Automated Tests
1. **Pytest (`backend/tests/test_llm_advisor.py`):**
   * Test 3-stage LLM response builders and Pydantic validation.
   * Verify ticker validation excludes fake/hallucinated symbols.
   * Verify Stage 3 budget cap compliance (`total_spend <= total_budget`).

2. **API SSE Stream Test (`backend/tests/test_advisory_api.py`):**
   * Verify `/api/v1/advisory/stream` streams valid event frames for Stages 1, 2, and 3.

### Manual Verification
1. **React Frontend (`http://localhost:3000/dashboard`):**
   * Open Advisory tab, enter ₹5,000 budget, ₹10,000 monthly capacity, bi-weekly schedule.
   * Click **Run 3-Stage AI Advisory** and observe live progress comments/animations.
   * Step through Stage 1 Diagnosis → Stage 2 Conviction Grid → Stage 3 Execution Plan.
   * Verify Zerodha Basket Export creates orders successfully.
