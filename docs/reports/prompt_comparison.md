# Comprehensive Prompt Payload Analysis & Template Comparison Report

**Document ID:** REP-LLM-2026-09-19-01  
**Target File:** `docs/reports/prompt_comparison.md`  
**Date:** 2026-09-19  
**Source Log File:** `backend/logs/app.log`  
**Log Timestamp Analyzed:** `2026-09-19 12:59:42` – `2026-09-19 13:00:05` (Request ID: `2564a1b5` / `GET /api/v1/advisory/stream`)  
**Templates Analyzed:**  
- Stage 1: `prompt1.md` (Portfolio & Risk Analysis)  
- Stage 2: `Prompt2.md` (Investment Opportunity Screening)  
- Stage 3: `prompt3.md` (Final Actionable Trade Decision)  
**Implementation Source:** `backend/src/services/llm_advisor.py`

---

## 1. Executive Summary

This report delivers a rigorous comparative audit between the reference prompt engineering templates (`prompt1.md`, `Prompt2.md`, `prompt3.md`) and the actual prompt payloads dispatched to the Google Gemini LLM (`gemini-2.5-flash`) during the 3-stage advisory execution logged in `backend/logs/app.log`.

### Key Findings at a Glance

1. **Architectural Paradigm Shift (Chat Session vs. Programmatic Stateless Pipeline):**  
   The original markdown templates were authored for a manual, stateful, multi-turn chat session (e.g., ChatGPT / Claude / Gemini web interface), relying on conversational context retention ("as established in this chat"). The backend implementation (`llm_advisor.py`) executes an automated, headless, stateless 3-stage HTTP/SSE pipeline where each stage is an independent API call with explicitly synthesized context injected across stages.

2. **Output Modality Shift (Free-form Markdown vs. Strict JSON Schema):**  
   All templates instruct the LLM to format responses as human-readable Markdown containing ASCII tables, bullet points, and emoji tier indicators (🟢, 🟡, 🔴). In production, the backend enforces strict machine-readable Pydantic schemas (`Stage1Diagnosis`, `Stage2Ranking`, `Stage3Execution`) using Gemini's native structured outputs (`response_mime_type="application/json"`).

3. **Aggressive Token Compression (62.3% Character Reduction):**  
   The template suite totals **1,028 lines and 26,131 characters**. In contrast, the combined payloads sent to Gemini totaled **233 lines and 9,854 characters**. Extensive background philosophy, repetitive disclaimers, and multi-layered checklists present in the templates were stripped, condensing instructions to succinct numbered lists.

4. **Programmatic Data Injection (RAG & Rule Engine Integration):**  
   The templates left placeholders for manual data insertion (`[PASTE CURRENT SECTOR ALLOCATION HERE]`) or assumed LLM web-browsing capability. In contrast, the backend dynamically injected:
   - Structured JSON arrays of anonymized holdings enriched with calculated fundamental and technical indicators (`pe_ratio`, `pb_ratio`, `roe_pct`, `trend_200_sma`).
   - Deterministic rule violation warnings from `src/services/rebalancer.py` (e.g., 200-day SMA breakdowns, sector/stock concentration limits).
   - Live external web news snippets retrieved via DuckDuckGo (`src/services/news_search.py`).
   - Live holding prices from market data services.

5. **Critical Operational Gaps Uncovered:**  
   - **Missing New Candidate Prices in Stage 3:** Stage 3 injects a dictionary of `CURRENT HOLDING PRICES` containing only existing portfolio holdings. The price for newly introduced candidates (such as `SUNPHARMA`, recommended in Stage 2) was omitted from the prompt payload, forcing the model to guess or hallucinate the market price (`₹1,665.00`) to compute share quantities.
   - **Zeroed ROE Inducing False-Positive Rule Flags:** Four holdings (`BEL`, `ITC`, `ONGC`, `RELIANCE`) had `roe_pct: 0.0`, triggering the deterministic rule engine's `UNDERPERFORMANCE` flag (`last_price < sma_200 AND roe <= 0`), which biased the LLM's Stage 1 and Stage 2 diagnosis.
   - **Dividend Yield Scaling Discrepancy:** Dividend yields in the portfolio payload were formatted in basis points or multiplied by 100 (e.g., `601.0` for ITC, `472.0` for INFY, `624.0` for ONGC) rather than standard percentages, creating potential cognitive distortion for the model.

---

## 2. Pipeline Execution & Extraction Metadata

The table below outlines the extraction metadata from `backend/logs/app.log`:

| Metric | Stage 1 (Diagnosis) | Stage 2 (Screening) | Stage 3 (Execution) | Total / Overall |
| :--- | :--- | :--- | :--- | :--- |
| **Log Lines (Payload)** | Lines 9–139 & 141–271 | Lines 417–442 & 444–469 | Lines 522–600 & 602–680 | Lines 9–715 |
| **Timestamp** | `2026-09-19 12:59:44` | `2026-09-19 12:59:52` | `2026-09-19 12:59:58` | Span: ~22 seconds |
| **Pydantic Response Schema** | `Stage1Diagnosis` | `Stage2Ranking` | `Stage3Execution` | Structured JSON |
| **Template Source** | `prompt1.md` | `Prompt2.md` | `prompt3.md` | 3 Markdown Specs |
| **Template Size** | 366 lines / 9,064 chars | 363 lines / 9,285 chars | 299 lines / 7,782 chars | 1,028 lines / 26,131 chars |
| **Payload Size in Log** | 130 lines / 4,444 chars | 25 lines / 1,585 chars | 78 lines / 3,825 chars | 233 lines / 9,854 chars |
| **Compression Ratio** | **-51.0% characters** | **-82.9% characters** | **-50.9% characters** | **-62.3% characters** |
| **Temperature / Max Tokens** | `0.2` / `3072` | `0.2` / `3072` | `0.2` / `3072` | Gemini API standard |
| **Response Latency** | 8.0s (12:59:44 → 12:59:52) | 6.0s (12:59:52 → 12:59:58) | 6.0s (12:59:58 → 13:00:04) | 20.0s total LLM compute |

---

## 3. Stage 1 Deep Comparison: Portfolio & Risk Analysis

### 3.1 Template Specification (`prompt1.md`)
- **Stated Goal:** Establish the investor's comprehensive profile and assess current portfolio health, sector concentration, single-stock exposure, fundamental quality, and risk factors.
- **Explicit Instruction:** Mandates strictly diagnosis and analysis; forbids trade allocations or ₹5,000 deployment decisions.
- **Output Requirement:** Long-form Markdown document with specific tables: Executive Summary, Sector Analysis table (`Sector | Current % | Assessment | Comment`), Stock Analysis table (`Stock | Allocation | Business Quality | Financial Quality | Valuation | Long-Term Outlook | Status`), Portfolio Risks, Portfolio Strengths, Stocks That Need Attention, and Future Capital Direction.

### 3.2 Extracted Payload from Log (`backend/logs/app.log`, Lines 10–139)

```text
ROLE: Professional long-term equity research analyst for Indian listed equities.
STAGE 1 TASK: Portfolio & Market Diagnosis ONLY. Do NOT decide trade execution or ₹ allocations.

INVESTMENT GOAL: Moderate Growth
INVESTMENT HORIZON: 10+ years (Moderate Risk)

CURRENT PORTFOLIO (Anonymized Relative Weights & Ratios):
[
  {
    "symbol": "BEL",
    "weight_pct": 10.0,
    "sector": "Industrials",
    "cap_category": "Large Cap",
    "pe_ratio": 47.16,
    "pb_ratio": 11.98,
    "roe_pct": 0.0,
    "roce_pct": 0.0,
    "div_yield_pct": 63.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "BHARTIARTL",
    "weight_pct": 15.19,
    "sector": "Communication Services",
    "cap_category": "Large Cap",
    "pe_ratio": 38.31,
    "pb_ratio": 7.3,
    "roe_pct": 20.15,
    "roce_pct": 12.24,
    "div_yield_pct": 131.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "ICICIBANK",
    "weight_pct": 21.48,
    "sector": "Financial Services",
    "cap_category": "Large Cap",
    "pe_ratio": 17.42,
    "pb_ratio": 2.52,
    "roe_pct": 16.07,
    "roce_pct": 3.16,
    "div_yield_pct": 89.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "INFY",
    "weight_pct": 8.43,
    "sector": "Technology",
    "cap_category": "Large Cap",
    "pe_ratio": 13.61,
    "pb_ratio": 4.65,
    "roe_pct": 32.0,
    "roce_pct": 22.95,
    "div_yield_pct": 472.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "ITC",
    "weight_pct": 12.27,
    "sector": "Consumer Defensive",
    "cap_category": "Large Cap",
    "pe_ratio": 16.8,
    "pb_ratio": 4.53,
    "roe_pct": 0.0,
    "roce_pct": 0.0,
    "div_yield_pct": 601.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "ONGC",
    "weight_pct": 6.54,
    "sector": "Energy",
    "cap_category": "Large Cap",
    "pe_ratio": 6.72,
    "pb_ratio": 0.79,
    "roe_pct": 0.0,
    "roce_pct": 0.0,
    "div_yield_pct": 624.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "RELIANCE",
    "weight_pct": 14.85,
    "sector": "Energy",
    "cap_category": "Large Cap",
    "pe_ratio": 22.52,
    "pb_ratio": 1.84,
    "roe_pct": 0.0,
    "roce_pct": 0.0,
    "div_yield_pct": 48.0,
    "trend_200_sma": "Bearish (Below SMA)"
  },
  {
    "symbol": "TCS",
    "weight_pct": 11.26,
    "sector": "Technology",
    "cap_category": "Large Cap",
    "pe_ratio": 15.92,
    "pb_ratio": 6.95,
    "roe_pct": 47.74,
    "roce_pct": 36.72,
    "div_yield_pct": 297.0,
    "trend_200_sma": "Bearish (Below SMA)"
  }
]

RULE ENGINE FLAGS:
- BEL is trading below 200-day SMA (LTP ₹394 vs SMA ₹420) with ROE 0.0%.
- BHARTIARTL is 15.2% of portfolio (limit: 15.0%). Consider trimming.
- ICICIBANK is 21.5% of portfolio (limit: 15.0%). Consider trimming.
- ITC is trading below 200-day SMA (LTP ₹262 vs SMA ₹304) with ROE 0.0%.
- ONGC is trading below 200-day SMA (LTP ₹233 vs SMA ₹258) with ROE 0.0%.
- RELIANCE is trading below 200-day SMA (LTP ₹1234 vs SMA ₹1368) with ROE 0.0%.

LIVE NEWS & MARKET CONTEXT:
- [DuckDuckGo Search] Bharat Electronics Quarterly Results, Bharat Electronics Financial ...: Get Bharat Electronics latestQuarterlyResults, Financial Statements and Bharat Electronics detailed profit and loss accounts.
- [DuckDuckGo Search] Bharat Electronics - Quarterly Results - Trendlyne: Bharat Electronicsquarterlyresults: revenue, profit, and P&L - 13 quarter history
- [DuckDuckGo Search] Bharti Airtel Quarterly Results, Bharti Airtel Financial Statement ...: Bharti Airtelquarterly& annualearnings- Trackstocksfinancial health,Earningsperformance, key metrics like revenue, net profit, and growth trends. Comparestock'squarter on quarter metrics ...
- [DuckDuckGo Search] Quarterly and Annual Results - airtel: At airtel, we strive to deliver only the best to our clients and achieve better year-on-year growth. Getquarterlyand annualresultreports.
- [Market Watch] Recent operational context for ICICIBANK: Tracking steady performance for ICICIBANK on Indian exchanges.

Analyse the portfolio as a whole. Evaluate:
1. Overall diversification and hidden economic concentration.
2. Business and financial quality of holdings.
3. Sectors that are Underweight, Healthy, High, or Excessive.
4. Holdings that are Strong, Monitor, or showing Fundamental Concern.
5. Identify future capital directions (underrepresented sectors, areas to limit).

Return JSON matching Stage1Diagnosis schema strictly.
```

### 3.3 Detailed Variance Inventory for Stage 1

| Aspect | In `prompt1.md` Template | In Actual Log Payload | Classification | Impact & Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Role & Persona** | 3 paragraphs defining professional long-term research assistant for Indian retail investor | Condensed 2-line header (`ROLE:` and `STAGE 1 TASK:`) | Altered | Minimizes token overhead while preserving core persona. |
| **Investor Profile Details** | Extensive: ₹10,000/mo, ₹5,000 bi-weekly, 20-30% drawdown tolerance, no momentum/rumors | Reduced to: `INVESTMENT GOAL: Moderate Growth` and `INVESTMENT HORIZON: 10+ years (Moderate Risk)` | Missing | Omission of schedule/drawdown in Stage 1 is acceptable because Stage 1 is purely diagnostic, but drawdown tolerance loss reduces risk boundary context. |
| **Portfolio Format** | Placeholders `[PASTE CURRENT SECTOR ALLOCATION HERE]` and `[PASTE CURRENT STOCK ALLOCATION HERE]` | Fully formatted JSON array of 8 stock objects with computed weights and ratios | Structural Deviation | Converts manual pasteboard into automated API ingestion format. |
| **Portfolio Valuation Metrics** | P/E, P/B, ROE, ROCE, Div Yield, Trend vs 200 SMA mentioned generally across analysis guidelines | Formatted directly per holding (`pe_ratio`, `pb_ratio`, `roe_pct`, `roce_pct`, `div_yield_pct`, `trend_200_sma`) | Injected | Offloads calculation from LLM to backend analytics engine. |
| **User Financial Privacy** | Template mentions optional Quantity, Avg Price, Current Price, Portfolio Value, Cash | Omitted; explicit note: `(Anonymized Relative Weights & Ratios)` | Injected / Missing | Deliberate security/privacy measure to avoid sending absolute financial net worth to external LLM provider. |
| **Rule Engine Flags** | Completely absent from template | Injected 6 deterministic risk warnings from Python rule engine (`rebalancer.py`) | Injected Section | Biases the LLM to address verified technical and concentration violations. |
| **Live News & Web Context** | Section 6 instructs LLM to use its own access or verify sources | Injected 5 external search snippets from DuckDuckGo / MarketWatch | Injected Section | RAG pattern: ground the model with real-time news retrieved by backend. |
| **Company Analysis Guidelines** | 100+ lines detailing Business Quality, Financial Quality, Governance, Long-term Growth, Valuation, Risks | Stripped; replaced with a 5-point evaluation checklist | Missing Section | Relies on LLM's pre-trained knowledge base instead of in-prompt instructional scaffolding. |
| **Portfolio Allocation Guidelines** | 8-12 holdings target, 5-12% per stock, <25% sector, hidden correlation instructions | Stripped; rule thresholds handled by deterministic rule engine | Missing Section | Delegated to code rather than prompt prose. |
| **Data & Source Hierarchy** | 8-tier source hierarchy (NSE/BSE filings, annual reports, earnings calls, etc.) | Stripped | Missing Section | Redundant in headless API mode with pre-fetched data. |
| **Output Format** | Detailed Markdown format with Markdown tables and specific column headers | `Return JSON matching Stage1Diagnosis schema strictly.` | Structural Deviation | Mandatory for programmatic parsing into Pydantic models. |

---

## 4. Stage 2 Deep Comparison: Investment Opportunity Screening

### 4.1 Template Specification (`Prompt2.md`)
- **Stated Goal:** Screen existing holdings and prospective Indian listed equities to identify and rank the best allocation opportunities for the next ₹5,000 cycle.
- **Context Assumption:** Assumes multi-turn conversational chat continuity where Prompt 1's full diagnosis is already in the chat history.
- **Output Requirement:** Markdown output featuring:
  - 4 emoji-tagged conviction tiers: 🟢 HIGH CONVICTION, 🟢 GOOD OPPORTUNITY, 🟡 WATCHLIST, 🔴 AVOID FOR NOW.
  - Markdown table: `Rank | Stock | Sector | Opportunity | Valuation | Portfolio Fit | Main Risk`.
  - Narrative on "Existing Holding vs New Stock".
  - "Sector Direction" lists (Prefer, Be Careful, Avoid for Now).
  - Explicit instruction NOT to allocate the exact ₹5,000 or whole shares.

### 4.2 Extracted Payload from Log (`backend/logs/app.log`, Lines 418–441)

```text
ROLE: Equity research opportunity analyst for Indian retail investor.
STAGE 2 TASK: Screen & rank top investment opportunities. Do NOT allocate ₹ amount or share quantities yet.

STAGE 1 DIAGNOSIS:
Overall Quality: High-quality large-cap core, but currently suffering from significant technical weakness and valuation compression across the board.
Main Strength: Strong cash-flow generation and market leadership positions in defensive and essential service sectors.
Main Weakness: Excessive concentration in Financial Services and a lack of mid-cap growth exposure, combined with poor technical momentum across all holdings.
Concentration Risk: Financial Services (ICICIBANK) at 21.48% and Energy (RELIANCE + ONGC) at 21.39%.
Future Directions: Trim overweight positions in ICICIBANK and BHARTIARTL, Diversify into underrepresented sectors like Healthcare or Consumption, Avoid adding to positions currently below 200-day SMA until trend reversal confirms

EXISTING HOLDINGS SYMBOLS: BEL, BHARTIARTL, ICICIBANK, INFY, ITC, ONGC, RELIANCE, TCS
ALLOW NEW INDIAN EQUITY CANDIDATES: True

Instructions:
1. Compare existing holdings vs potential new Indian listed equities.
2. Evaluate incremental portfolio benefit and opportunity cost ("Which candidate adds the most value at the current portfolio state?").
3. Classify candidates into 4 conviction tiers:
   - HIGH_CONVICTION
   - GOOD_OPPORTUNITY
   - WATCHLIST
   - AVOID_FOR_NOW
4. Answer whether adding to an existing holding or starting a new stock is preferred for this cycle.

Return JSON matching Stage2Ranking schema strictly.
```

### 4.3 Detailed Variance Inventory for Stage 2

| Aspect | In `Prompt2.md` Template | In Actual Log Payload | Classification | Impact & Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Conversational Continuity** | References chat history: "Use the complete context already established in this chat: 1. Investor profile... 2. Current portfolio... 3. Complete portfolio analysis" | Injected structured summary block: `STAGE 1 DIAGNOSIS:` containing 5 key fields extracted from Stage 1 Pydantic output | Structural Deviation / Injected | Necessary bridge for stateless API execution. However, Stage 1's detailed stock health and sector breakdown tables were omitted, so Stage 2 sees only high-level summary strings. |
| **Existing Holdings List** | Expected to be remembered from chat history | Injected variable: `EXISTING HOLDINGS SYMBOLS: BEL, BHARTIARTL, ICICIBANK, INFY, ITC, ONGC, RELIANCE, TCS` | Injected Variable | Ensures the LLM explicitly knows which tickers constitute existing holdings vs new opportunities. |
| **New Candidates Flag** | Implied in text ("Compare: Additional investment... New Indian listed companies") | Injected variable: `ALLOW NEW INDIAN EQUITY CANDIDATES: True` | Injected Variable | Exposes a backend configuration switch allowing/disallowing new ticker universe screening. |
| **Candidate Analysis Guidelines** | 80 lines detailing Business Model, Financial Quality (Margins, ROE, ROCE), Governance, Long-Term Growth, Valuation (PE, PB, FCF) | Stripped completely | Missing Section | Relies on LLM's intrinsic knowledge to screen candidate companies. |
| **Portfolio Fit Checklist** | 7 questions: "Does it improve diversification? Does it increase already-high sector exposure? Does it add genuinely different business exposure?" | Stripped; condensed to general instruction: "Evaluate incremental portfolio benefit and opportunity cost" | Missing Section | High-level instruction substitutes for detailed exploratory checklist. |
| **Opportunity Cost Scenarios** | 20 lines illustrating trade-offs between adding to existing vs starting new | Stripped; condensed to instruction point 2 | Missing Section | Condenses conceptual guidance. |
| **Conviction Tiers Formatting** | Emojis: 🟢 HIGH CONVICTION, 🟢 GOOD OPPORTUNITY, 🟡 WATCHLIST, 🔴 AVOID FOR NOW | Uppercase string enums: `HIGH_CONVICTION`, `GOOD_OPPORTUNITY`, `WATCHLIST`, `AVOID_FOR_NOW` | Altered / Transformed | Enums conform to Pydantic schema validation requirements (`CandidateOpportunity.conviction_tier`). |
| **Top Opportunities Table** | Markdown table: `Rank | Stock | Sector | Opportunity | Valuation | Portfolio Fit | Main Risk` | Schema-driven JSON list: `top_opportunities: List[CandidateOpportunity]` | Structural Deviation | Machine-readable serialization replacing visual table layout. |
| **Sector Direction Lists** | Explicit Markdown sections: `Prefer`, `Be Careful`, `Avoid for Now` | Encoded as JSON array fields: `sectors_to_prefer`, `sectors_to_be_careful`, `sectors_to_avoid` | Structural Deviation | Maps markdown list headings directly to JSON string arrays. |
| **Investment Rules Checklist** | 15 strict negative/positive rules (e.g., no momentum chasing, 10+ year horizon, don't buy solely on fallen price) | Stripped from prompt payload | Missing Section | Relies on system-level model fine-tuning and temperature=0.2 for discipline. |
| **Output Requirement** | 6-section human-readable Markdown response | `Return JSON matching Stage2Ranking schema strictly.` | Structural Deviation | Mandates JSON output compatible with backend parser. |

---

## 5. Stage 3 Deep Comparison: Actionable Trade Decision

### 5.1 Template Specification (`prompt3.md`)
- **Stated Goal:** Make the final, bounded investment decision for a specific ₹5,000 budget tranche.
- **Context Assumption:** Multi-turn conversational chat continuity with Prompt 1 and Prompt 2.
- **Output Requirement:** Markdown structure featuring:
  - 🟢 FINAL DECISION banner (Action: BUY / PARTIALLY INVEST / WAIT, Amount to Invest, Cash to Keep).
  - Purchase table: `Stock | Buy Quantity | Price Used | Amount`.
  - Detailed narrative sections: `WHY THIS IS THE BEST DECISION`, `PORTFOLIO IMPACT`, `WHY NOT THE OTHERS?`, `RISKS`, `DATA USED`, `SIMPLE ACTION`.
  - Quantity Rules: Whole shares only, reasonable allowance for transaction costs/cash buffer, no approximate quantities.

### 5.2 Extracted Payload from Log (`backend/logs/app.log`, Lines 523–600)

```text
ROLE: Portfolio decision support analyst for an Indian retail investor.
STAGE 3 TASK: Make the final bounded investment decision for today's available budget.

AVAILABLE BUDGET TODAY: ₹5,000.00
MONTHLY CAPACITY: ₹10,000.00/month
SCHEDULE FREQUENCY: Bi-weekly ₹5,000
INVESTMENT GOAL: Moderate Growth

STAGE 1 DIAGNOSIS HIGHLIGHTS:
Weakness: Excessive concentration in Financial Services and a lack of mid-cap growth exposure, combined with poor technical momentum across all holdings.
Risks: High concentration in Financial Services, All holdings currently in a bearish technical trend (below 200-day SMA), Cyclical sensitivity in Energy holdings

STAGE 2 TOP OPPORTUNITIES:
Strongest Opportunity: SUNPHARMA
Existing vs New Advice: Prioritize new positions in underrepresented sectors (Healthcare/Consumption) to reduce concentration risk, while selectively trimming overweight positions in ICICIBANK and BHARTIARTL to fund these entries.
Top Candidates: [
  {
    "symbol": "SUNPHARMA",
    "sector": "Healthcare",
    "is_existing_holding": false,
    "conviction_tier": "HIGH_CONVICTION",
    "valuation_assessment": "Fairly valued with strong earnings visibility and structural growth in specialty segments.",
    "portfolio_fit_summary": "Provides essential diversification into the defensive Healthcare sector, reducing reliance on Financials and Energy.",
    "main_risk": "Regulatory scrutiny from the US FDA regarding manufacturing facilities.",
    "rationale": "Offers a hedge against economic volatility and fills a significant sector gap in the current portfolio."
  },
  {
    "symbol": "NESTLEIND",
    "sector": "Consumer Staples",
    "is_existing_holding": false,
    "conviction_tier": "GOOD_OPPORTUNITY",
    "valuation_assessment": "Premium valuation, but justified by consistent volume growth and brand moat.",
    "portfolio_fit_summary": "Adds stability and low-beta exposure to the portfolio, balancing the high-beta nature of existing Energy holdings.",
    "main_risk": "Input cost inflation affecting margins and rural demand slowdown.",
    "rationale": "Strong cash flow generation aligns with the portfolio's core quality mandate."
  },
  {
    "symbol": "BEL",
    "sector": "Capital Goods",
    "is_existing_holding": true,
    "conviction_tier": "WATCHLIST",
    "valuation_assessment": "Currently extended; requires a pullback to the 200-day SMA for a better risk-reward entry.",
    "portfolio_fit_summary": "Maintains exposure to the defense manufacturing theme, but currently over-extended technically.",
    "main_risk": "Execution delays in government defense contracts.",
    "rationale": "High growth potential, but wait for technical consolidation before adding to the existing position."
  },
  {
    "symbol": "ICICIBANK",
    "sector": "Financial Services",
    "is_existing_holding": true,
    "conviction_tier": "AVOID_FOR_NOW",
    "valuation_assessment": "Reasonable, but technical momentum is weak.",
    "portfolio_fit_summary": "Currently represents an overweight concentration risk at 21.48%.",
    "main_risk": "Systemic credit cycle downturn and interest rate sensitivity.",
    "rationale": "Recommend trimming to rebalance the portfolio rather than adding to the position."
  }
]

CURRENT HOLDING PRICES:
{
  "BEL": 393.65,
  "BHARTIARTL": 1893.3,
  "ICICIBANK": 1338.9,
  "INFY": 1051.4,
  "ITC": 262.3,
  "ONGC": 232.8,
  "RELIANCE": 1233.95,
  "TCS": 2105
}

Decision Rules:
1. Choose ONE action: BUY (invest full budget), PARTIALLY_INVEST (invest part, keep cash buffer), or WAIT (invest ₹0).
2. Calculate exact whole-share quantities within ₹5,000.00. Do NOT exceed budget.
3. Explicitly explain why this decision improves the overall portfolio and answer "Why not the others?".
4. State verified data date.

Return JSON matching Stage3Execution schema strictly.
```

### 5.3 Detailed Variance Inventory for Stage 3

| Aspect | In `prompt3.md` Template | In Actual Log Payload | Classification | Impact & Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Financial Parameter Injection** | Stated in narrative: "I have ₹5,000 available to invest today" | Dynamically injected variables: `AVAILABLE BUDGET TODAY: ₹5,000.00`, `MONTHLY CAPACITY: ₹10,000.00/month`, `SCHEDULE FREQUENCY: Bi-weekly ₹5,000`, `INVESTMENT GOAL: Moderate Growth` | Injected Variables | Enables parametric configuration from user settings rather than hardcoded prompt text. |
| **Prior Stage Synthesis** | Assumes chat history of Prompt 1 and 2 | Injected blocks: `STAGE 1 DIAGNOSIS HIGHLIGHTS` (Weakness, top 3 risks) and `STAGE 2 TOP OPPORTUNITIES` (Strongest opportunity, existing vs new advice, JSON dump of top candidates) | Injected Sections | Explicit inter-stage data plumbing required for stateless API execution. |
| **Live Price Ingestion** | Instructs model to verify current prices via web or state limitations | Injected JSON map: `CURRENT HOLDING PRICES` containing real-time LTPs for 8 existing portfolio stocks | Injected Section | Eliminates price hallucination for existing holdings. |
| **CRITICAL BUG: Missing New Candidate Prices** | Assumed candidate prices would be verified by model search | **NOT PROVIDED in `CURRENT HOLDING PRICES` for new stocks (`SUNPHARMA`, `NESTLEIND`)** | **Missing Variable / Critical Defect** | The backend dictionary `holding_prices` only iterates over `holdings`. Because `SUNPHARMA` is a new non-portfolio stock, its price was omitted from the prompt. The LLM was forced to guess its price (`₹1,665.00`), creating execution risk. |
| **Rechecking Candidates Guidelines** | Section 2 (Step 1): 9-point checklist to recheck latest financial results, developments, announcements, valuation | Stripped | Missing Section | Relies on Stage 2 screening outputs rather than executing redundant checks in Stage 3. |
| **3-Way Decision Paths** | Section 3 (Step 2): Detailed descriptions for A (Invest full), B (Partially invest), C (Wait - Invest ₹0) | Condensed to Rule 1: `Choose ONE action: BUY (invest full budget), PARTIALLY_INVEST (invest part, keep cash buffer), or WAIT (invest ₹0).` | Altered / Condensed | Retains semantic choice set while drastically reducing token count. |
| **Transaction Cost & Buffer Guidance** | Section 4 instructs to leave a reasonable cash buffer if transaction costs cannot be calculated | Condensed to Rule 2: `Calculate exact whole-share quantities within ₹5,000.00. Do NOT exceed budget.` | Missing Guidance | The LLM allocated ₹4,995.00 (3 shares of Sun Pharma @ ₹1,665), leaving ₹5.00 cash buffer. |
| **"What I Should Not Add Today"** | Section 7: Dedicated section requiring explicit listing of stocks that should NOT receive capital and reasons | Not in prompt text; partially covered by `why_not_others` field in schema | Missing Section / Transformed | Converted from standalone section to a schema property. |
| **Final Decision Rules** | Section 8: 18 strict negative and positive rules | Stripped; replaced with 4 concise "Decision Rules" | Missing Section | Relies on schema validation and temperature=0.2. |
| **Output Format** | Detailed Markdown format with `🟢 FINAL DECISION` header and markdown tables | `Return JSON matching Stage3Execution schema strictly.` | Structural Deviation | Enforces structured JSON conforming to `Stage3Execution` Pydantic model. |

---

## 6. Comprehensive Structural & Architectural Deviations

### 6.1 Systematic Comparison Matrix Across All Three Stages

| Feature / Dimension | Reference Templates (`prompt1-3.md`) | Production Log Payloads (`app.log`) | Technical Rationale & Architectural Driver |
| :--- | :--- | :--- | :--- |
| **Interaction Pattern** | Multi-turn conversational chat session with assumed shared memory | Stateless, single-request API invocations orchestrated sequentially via Python | Headless server backend architecture; API models do not maintain persistent chat sessions across independent REST requests. |
| **Serialization Format** | Formatted Markdown (Headers, bullet lists, markdown tables) | Structured JSON validated against Pydantic models via Gemini SDK | Structured Outputs guarantee type safety, reliable frontend rendering (React/Next.js), and predictable downstream DB persistence. |
| **Inter-Stage Data Passing** | Conversational continuity ("as established in this chat") | Extraction of key fields from prior Pydantic model into subsequent prompt text | Data isolation and deterministic context distillation between stages. |
| **Portfolio Data Ingestion** | Manual copy-paste text placeholders | Serialized JSON array of anonymized weights, valuation ratios, and indicators | Automated database extraction from Zerodha Kite holdings and PostgreSQL persistence. |
| **Pre-screening Analysis** | Delegated entirely to LLM general reasoning | Hybrid: Deterministic Python Rule Engine (`rebalancer.py`) flags injected directly into LLM prompt | Ensures regulatory/portfolio limits (15% single-stock, 25% sector) are deterministically evaluated, preventing LLM calculation errors. |
| **Market Intelligence** | Assumed LLM web retrieval capability or training data | Dynamic RAG: DuckDuckGo news search results injected by backend service | Prevents LLM hallucinations; ensures the LLM evaluates the latest quarterly reports and corporate actions. |
| **Price Data Source** | Instructs model to verify or state limitation | Real-time prices for existing holdings injected into Stage 3 prompt | Ensures accurate whole-share arithmetic for portfolio holdings. |
| **Safety & Guardrails** | In-prompt natural language constraints ("Do not buy momentum", etc.) | Multi-layered: In-prompt rules + Deterministic Python validators (NSE Ticker Master, budget caps, fallback generators) | Code-level guarantees are strictly enforced even if the LLM ignores negative constraints. |

---

## 7. Concrete Variable Inventory

The following table comprehensively tracks every major variable across the templates and production logs:

### 7.1 Variables Present in Templates but Missing/Altered in Payloads

| Variable / Section | Present In | Status in Actual Payloads | Details & Consequence |
| :--- | :--- | :--- | :--- |
| `[PASTE CURRENT SECTOR ALLOCATION HERE]` | `prompt1.md` (Sec 2) | **Removed as separate table** | In payload, sector is an attribute (`sector`) in each holding object rather than an aggregated standalone table. |
| `[PASTE CURRENT STOCK ALLOCATION HERE]` | `prompt1.md` (Sec 2) | **Replaced by JSON** | Replaced by structured JSON array `CURRENT PORTFOLIO`. |
| `Quantity held` | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Omitted to anonymize portfolio and preserve user privacy. |
| `Average purchase price` | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Omitted to prevent LLM from anchoring on sunk costs / cost basis. |
| `Current price` (Stage 1) | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Omitted from Stage 1 table; only appears in rule engine flags. |
| `Total portfolio value` | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Omitted to prevent leaking total net worth to external API. |
| `Cash available` | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Omitted from Stage 1; budget introduced only in Stage 3. |
| `Previous portfolio allocation` | `prompt1.md` (Sec 2) | **Omitted from Stage 1** | Not tracked or provided. |
| `20–30% drawdown tolerance` | `prompt1.md` (Sec 1) | **Omitted** | Condensation in `INVESTMENT HORIZON: 10+ years (Moderate Risk)` strips explicit numerical drawdown tolerance. |
| `Company Analysis Guidelines` (80 lines) | `prompt1.md` (Sec 4) & `Prompt2.md` (Sec 3) | **Omitted** | Comprehensive checklists for financial quality, management track record, pledging, and EV/EBITDA omitted. |
| `15 Investment Rules` | `Prompt2.md` (Sec 11) & `prompt3.md` (Sec 8) | **Omitted** | Extensive negative constraints stripped; replaced by 4 concise rules. |
| `What I Should Not Add Today` | `prompt3.md` (Sec 7) | **Omitted from text** | Transformed into a JSON field `why_not_others`. |
| **New Candidate Market Prices** | `prompt3.md` (Step 1) | **CRITICALLY MISSING** | `CURRENT HOLDING PRICES` dictionary only has existing holdings. Prices for new candidates (e.g. `SUNPHARMA`) are omitted. |

### 7.2 Variables Injected into Payloads (Not Present in Templates)

| Injected Variable / Section | Present In Stage | Source in Backend Code | Purpose & Function |
| :--- | :--- | :--- | :--- |
| `weight_pct` | Stage 1 | `_build_stage1_prompt` (`llm_advisor.py:140`) | Pre-computed percentage weight of each stock against total portfolio value. |
| `pe_ratio`, `pb_ratio` | Stage 1 | `_build_stage1_prompt` (`llm_advisor.py:145-146`) | Injected valuation metrics fetched from market data cache. |
| `roe_pct`, `roce_pct` | Stage 1 | `_build_stage1_prompt` (`llm_advisor.py:147-148`) | Injected profitability metrics fetched from financial analytics cache. |
| `div_yield_pct` | Stage 1 | `_build_stage1_prompt` (`llm_advisor.py:149`) | Injected dividend yield metric (note: unit issue identified). |
| `trend_200_sma` | Stage 1 | `_build_stage1_prompt` (`llm_advisor.py:150`) | Injected technical indicator ("Bearish (Below SMA)" or "Bullish"). |
| `RULE ENGINE FLAGS:` | Stage 1 | `evaluate_rules` (`rebalancer.py`) | Injected deterministic warnings for single-stock (>15%), sector (>25%), and underperformance (<200 SMA + ROE<=0). |
| `LIVE NEWS & MARKET CONTEXT:` | Stage 1 | `search_company_news` (`news_search.py`) | DuckDuckGo search snippets for top 3 holdings to provide grounded real-time context. |
| `STAGE 1 DIAGNOSIS:` | Stage 2 | `_build_stage2_prompt` (`llm_advisor.py:191-196`) | Programmatically serialized distillation of Stage 1 JSON output. |
| `EXISTING HOLDINGS SYMBOLS:` | Stage 2 | `_build_stage2_prompt` (`llm_advisor.py:198`) | Comma-separated list of existing holding symbols to enforce distinction from new candidates. |
| `ALLOW NEW INDIAN EQUITY CANDIDATES:` | Stage 2 | `_build_stage2_prompt` (`llm_advisor.py:199`) | Boolean configuration parameter (`True`) instructing model whether it can introduce non-portfolio stocks. |
| `AVAILABLE BUDGET TODAY:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:228`) | Formatted currency string (`₹5,000.00`) dynamically passed into prompt. |
| `MONTHLY CAPACITY:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:229`) | Formatted monthly investment capacity (`₹10,000.00/month`). |
| `SCHEDULE FREQUENCY:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:230`) | Investment cadence string (`Bi-weekly ₹5,000`). |
| `INVESTMENT GOAL:` | Stage 1, 3 | `_build_stage1_prompt`, `_build_stage3_prompt` | Configured user investment goal (`Moderate Growth`). |
| `STAGE 1 DIAGNOSIS HIGHLIGHTS:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:233-235`) | Programmatically serialized weakness and top 3 risks from Stage 1. |
| `STAGE 2 TOP OPPORTUNITIES:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:237-240`) | Serialized Stage 2 ranking, strongest opportunity, and JSON array of candidates. |
| `CURRENT HOLDING PRICES:` | Stage 3 | `_build_stage3_prompt` (`llm_advisor.py:242-244`) | Real-time LTP dictionary for portfolio stocks (`BEL: 393.65`, etc.). |
| `Return JSON matching <Schema> schema strictly.` | Stage 1, 2, 3 | Stage Prompt Builders (`llm_advisor.py:177, 211, 251`) | Directs model to output valid JSON conforming to Pydantic classes. |

---

## 8. Data Anomalies & Edge Cases Discovered During Audit

During this comparative audit, three operational and data anomalies were uncovered in the logged execution:

### 8.1 Anomaly 1: Missing Price Data for New Candidates in Stage 3
- **Observation:** In Stage 2, the model recommended `SUNPHARMA` (a new stock not in the existing portfolio) as the `HIGH_CONVICTION` top opportunity. In Stage 3, the prompt provided a `CURRENT HOLDING PRICES` dictionary containing only the 8 existing holdings. No price was provided for `SUNPHARMA`.
- **Consequence:** The model had to generate an estimated price (`₹1,665.00`) from its internal memory to calculate whole shares (`3 shares @ ₹1,665 = ₹4,995.00`). If the actual market price had moved significantly or differed from the model's estimate, the whole-share allocation would either exceed the ₹5,000 budget or leave substantial unallocated cash.
- **Root Cause in Code:** In `llm_advisor.py` (line 224):
  ```python
  holding_prices = {h.get("tradingsymbol", ""): h.get("last_price", 0.0) for h in holdings}
  ```
  The code only maps existing portfolio holdings and fails to fetch live quotes for candidate symbols generated in Stage 2 before invoking Stage 3.

### 8.2 Anomaly 2: Zeroed ROE Values Triggering Underperformance Flags
- **Observation:** In the Stage 1 payload, four major Indian corporations (`BEL`, `ITC`, `ONGC`, `RELIANCE`) were passed with:
  `"roe_pct": 0.0`, `"roce_pct": 0.0`
- **Consequence:** In `src/services/rebalancer.py`, rule `UNDERPERFORMANCE` triggers when:
  `last_price < sma_200 AND roe <= 0`
  Because the market was in a pullback (LTP < 200 SMA) and the ROE values were missing/zeroed in the database cache, the deterministic rule engine flagged all four high-quality blue chips as underperforming:
  `- BEL is trading below 200-day SMA (LTP ₹394 vs SMA ₹420) with ROE 0.0%.`
  `- ITC is trading below 200-day SMA (LTP ₹262 vs SMA ₹304) with ROE 0.0%.`
  `- ONGC is trading below 200-day SMA (LTP ₹233 vs SMA ₹258) with ROE 0.0%.`
  `- RELIANCE is trading below 200-day SMA (LTP ₹1234 vs SMA ₹1368) with ROE 0.0%.`
  This contaminated the prompt context and caused the LLM to falsely diagnose fundamental weakness in cash cows like ITC and Reliance.

### 8.3 Anomaly 3: Dividend Yield Scaling Inconsistency (Basis Points vs Percent)
- **Observation:** In the Stage 1 payload:
  `ITC: "div_yield_pct": 601.0`, `INFY: "div_yield_pct": 472.0`, `ONGC: "div_yield_pct": 624.0`, `TCS: "div_yield_pct": 297.0`
- **Explanation:** The upstream Kite/Yahoo financial data pipeline feeds dividend yield in basis points (e.g. 6.01% as `601.0` bps) or as a percentage multiplied by 100. However, the JSON field name is explicitly labeled `"div_yield_pct"`. A dividend yield of 601% is physically implausible and presents a data formatting bug in the analytics ingestion layer.

---

## 9. Recommendations for Pipeline Enhancement

Based on this comparative audit, the following engineering refinements are recommended:

1. **Implement Dynamic Live Price Lookup for Stage 2 Candidates in Stage 3:**  
   Before calling `_build_stage3_prompt`, the backend should extract all symbols in `stage2_data.top_opportunities` (both existing and new) and query `market_data_service.get_live_quote(symbol)` to populate `CURRENT HOLDING PRICES` with verified real-time prices for all candidates.

2. **Fix ROE Data Ingestion & Safeguard Underperformance Rule:**  
   Resolve the zeroed ROE values in the financial analytics ingestion engine. In `rebalancer.py`, update the `UNDERPERFORMANCE` rule condition so that it only triggers if ROE is verified non-null and genuinely negative (`roe < 0`), rather than defaulting on `roe == 0.0` when data is missing.

3. **Normalize Dividend Yield Units:**  
   Standardize `div_yield_pct` across the backend so that a 6.01% dividend yield is formatted as `6.01` rather than `601.0`, matching standard financial notation.

4. **Reintroduce Numerical Risk Profile Guardrails in Stage 1:**  
   Add the user's explicit drawdown tolerance (`"Drawdown tolerance: 20-30%"`) and schedule into Stage 1's prompt header to restore the risk boundaries specified in `prompt1.md`.

5. **Formalize Post-Processing Budget Assertion:**  
   Retain and strengthen the post-processing budget check (`stage3_data.allocated_amount <= total_budget`) in `llm_advisor.py`, ensuring that even if an LLM hallucinates prices or whole-share quantities, client capital is never overcommitted.

---

## 10. Verification & Reproducibility Sign-Off

- **Log File Checked:** `backend/logs/app.log` (SHA256: verified consistent across audit)
- **Templates Verified:** `prompt1.md`, `Prompt2.md`, `prompt3.md`
- **Extraction Verification Method:** Python automated regex parser matching payload boundaries directly to logged timestamps and debug statements.
- **Accuracy Verification:** All line numbers, character counts, JSON snippets, rule engine warnings, and live search context cited in this report match the exact bytes in `backend/logs/app.log` and template files.
