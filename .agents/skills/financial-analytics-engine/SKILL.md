---
name: financial-analytics-engine
description: Rules for deterministic financial math (XIRR, CAGR, Sharpe), market data caching, and Indian Income Tax harvesting.
---

# Financial Analytics Engine Skill

This skill governs the mathematical formulas, market data fetching order, and tax calculation logic implemented in the `portfolio_assistant` analytics service layer.

---

## 1. Deterministic Financial Metrics & Formulas

All portfolio metrics must strictly adhere to non-hallucinated, deterministic mathematical standards:

| Metric | Calculation Method / Formula | Data Source |
| :--- | :--- | :--- |
| **XIRR** | Newton-Raphson root finding on net cashflows $0 = \sum_{i=1}^N \frac{C_i}{(1 + r)^{(d_i - d_1)/365}}$ | `get_trades()` historical buy/sell log + current liquidation value |
| **CAGR** | $\left( \frac{\text{Current Value}}{\text{Initial Investment}} \right)^{\frac{1}{\text{Years}}} - 1$ | Portfolio total invested vs current value |
| **P/E & P/B** | Price-to-Earnings & Price-to-Book ratios | `market_data_service.get_fundamentals(symbol)` |
| **ROE** | Return on Equity % | `market_data_service.get_fundamentals(symbol)` |
| **200-day SMA** | 200-period Simple Moving Average of daily closing prices | `yfinance` / NSE historical close prices |

---

## 2. Market Data Providers & Caching Hierarchy

To maximize speed and minimize API costs/throttle errors, `MarketDataService` enforces a strict 3-tier fallback hierarchy:

1. **Tier 1 (Primary): `nsepython`**
   - Native NSE scraper with no API key requirement. Wrapped in retry decorator (3 attempts, exponential backoff).
2. **Tier 2 (Secondary): `yfinance`**
   - Fallback provider for historical candlestick series and fundamental data if `nsepython` fails.
3. **Tier 3 (Static DB Fallback): `STOCK_METADATA_DB`**
   - In-memory dictionary containing pre-configured fundamental metadata for common NSE symbols.

### Caching Standard
* **TTL:** `86400` seconds (24 hours).
* **Cache Storage:** `_FUNDAMENTALS_CACHE` in-memory dictionary `{symbol: (data, expiry_timestamp)}`.

---

## 3. Indian Tax Harvesting Logic (Section 112A Compliance)

Tax analysis models equity holdings according to current Indian Income Tax laws:

* **Short-Term Capital Gains (STCG):** Holding period $\le 365$ days. Taxed at **20%**.
* **Long-Term Capital Gains (LTCG):** Holding period $> 365$ days. Taxed at **12.5%** for aggregate gains exceeding **₹1.25 Lakh** per financial year.
* **Tax-Loss Harvesting Algorithm:**
  1. Identify holdings currently trading at an unrealized loss (`pnl < 0`).
  2. Separate into STCG losses vs LTCG losses based on purchase date.
  3. Suggest trimming/selling loss holdings prior to March 31 to offset taxable realized capital gains.

---

## 4. References & Documentation Links

* [Phase 2 Analytics Engine LLD](file:///home/benoi/Projects/portfolio_assistant/docs/lld/02_phase2_analytics_engine.md)
* [Phase 2 Implementation Plan](file:///home/benoi/Projects/portfolio_assistant/docs/plans/phase_2_fundamental_and_sector_analytics.md)
