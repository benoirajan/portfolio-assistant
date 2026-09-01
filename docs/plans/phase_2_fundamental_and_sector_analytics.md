# Implementation Plan - Phase 2: Fundamental & Sector Analytics Engine

---

## 1. Overview & Objectives
Phase 2 enhances the Portfolio Assistant by adding deep quantitative financial analysis. It enriches raw stock symbols with fundamental metrics (P/E ratio, P/B ratio, Dividend Yield, Debt-to-Equity, ROE), calculates portfolio-level performance metrics (XIRR, Sharpe/Sortino ratios, Beta vs. Nifty 50), and analyzes tax harvesting opportunities (STCG vs. LTCG).

---

## 2. Technical Architecture & Component Design

```mermaid
graph TD
    HOLDINGS["Zerodha Holdings Ingestion"] --> ENRICHER["Stock Fundamentals Enricher (yfinance / NSE API)"]
    ENRICHER --> QUANT["Quantitative Analytics Engine"]
    
    QUANT --> SECTOR["Sector Exposure & Drift"]
    QUANT --> XIRR_ENG["XIRR & Performance Ratios"]
    QUANT --> TAX_ENG["Tax Harvesting Analyzer (STCG / LTCG)"]
    QUANT --> RISK["Portfolio Beta & Volatility"]
    
    SECTOR --> DASHBOARD["Streamlit Analytics Dashboard"]
    XIRR_ENG --> DASHBOARD
    TAX_ENG --> DASHBOARD
    RISK --> DASHBOARD
```

---

## 3. Key Components to Build

### 3.1 Market Data & Fundamentals Enricher (`src/services/market_data.py`)
- Integration with secondary data sources (e.g., `yfinance` or Indian market financial APIs).
- Caching stock fundamental metrics in Redis/SQLite to avoid redundant network calls.
- Historical price candle retrieval (1-year daily candles) for Beta and Sharpe ratio computations.

### 3.2 Quantitative Analytics Engine (`src/services/analytics_engine.py`)
- **Portfolio XIRR Calculation**: Computes Extended Internal Rate of Return taking into account historical cash inflows (buy transactions) and current market value.
- **Benchmark Comparative Beta**: Measures portfolio volatility against Nifty 50 and Nifty 500 indices.
- **Sharpe & Sortino Ratios**: Evaluates risk-adjusted returns against the Indian 10-Year Government Bond risk-free rate (~7%).

### 3.3 Tax Harvesting Analyzer (`src/services/tax_harvesting.py`)
- Categorizes holding gains into **STCG** (< 1 year holding, 20% tax rate) vs. **LTCG** (> 1 year holding, 12.5% tax rate after ₹1.25 Lakh exemption).
- Identifies loss-making stocks that can be sold to offset realized capital gains before financial year-end.

---

## 4. Proposed File Changes

#### [NEW] `src/services/market_data.py`
- Fundamental ratio fetcher & market candle downloader.

#### [NEW] `src/services/analytics_engine.py`
- Math routines for XIRR, Sharpe, Sortino, Beta, and drawdown metrics.

#### [NEW] `src/services/tax_harvesting.py`
- Tax optimization and capital gains classifier.

#### [MODIFY] `src/api/holdings.py`
- New endpoints: `/api/v1/analytics/performance` and `/api/v1/analytics/tax-harvesting`.

#### [MODIFY] `src/ui/app.py`
- Enhanced analytics UI with XIRR cards, Beta gauge chart, and Tax Loss Harvesting tab.

---

## 5. Verification & Testing Strategy
- Unit tests validating XIRR calculation accuracy against known financial benchmark datasets.
- Mock market data verification for off-market hour testing.
