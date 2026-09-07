# LLD 02 — Phase 2: Fundamental & Sector Analytics Engine

**Files covered:**
`src/services/market_data.py` · `src/services/analytics_engine.py` · `src/services/tax_harvesting.py` · `src/api/analytics.py`

**Cross-references:**
- Retry policies applied to market data providers → [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry)
- Log lines emitted by analytics endpoints → [LLD 04 §3](./04_logging.md#analyticspy)
- `get_trades()` data source (used for XIRR) → [LLD 01 §2](./01_phase1_auth_and_holdings.md#get_trades---listdict)
- Holdings enrichment consumed by Phase 3 advisory → [LLD 03 §3.2](./03_phase3_ai_advisory.md#32-_build_prompt--data-minimization)

---

## 1. `src/services/market_data.py` — Market Data Service

### 1.1 Module-level constants

| Constant | Value | Purpose |
|---|---|---|
| `_FUNDAMENTALS_CACHE` | `Dict[str, tuple]` | In-memory TTL cache: `{symbol: (data, expiry_timestamp)}` |
| `_CACHE_TTL_SECONDS` | `86400` | 24-hour cache TTL |
| `STOCK_METADATA_DB` | `Dict[str, Dict]` | Static fallback fundamentals for 12 common NSE stocks |
| `SECTOR_MAP` | `Dict[str, str]` | Symbol → sector string lookup for 13 common symbols |

`STOCK_METADATA_DB` fields per symbol: `sector`, `cap_category`, `pe_ratio`, `pb_ratio`, `roe`, `sma_200`, `div_yield`.

### 1.2 `MarketDataService` — Class

Singleton instance `market_data_service` exported at module level. Lazy-loads `yfinance` and `nsepython` on first use to avoid import-time failures if packages are absent.

---

#### `_get_yfinance() -> Optional[module]`

Lazy import of `yfinance`. Logs a `WARNING` and returns `None` if not installed.

---

#### `_get_nsepython() -> Optional[module]`

Lazy import of `nsepython`. Logs a `WARNING` and returns `None` if not installed.

---

#### `_fetch_nsepython(symbol: str) -> Optional[Dict]`

**Primary data provider** — NSE-native, no API key required.

Uses `nse.nse_eq(symbol)` wrapped in a `@retry` decorator (full retry spec → [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry)).

**Retry policy:**

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 1.0s |
| `multiplier` | 2.0 |
| `retryable_on` | `(Exception,)` |

**Data extracted from NSE response:**

| Field | Source path |
|---|---|
| `pe_ratio` | `priceInfo.pdSymbolPe` |
| `sector` | `industryInfo.sector` → fallback `_infer_sector()` |
| `cap_category` | `_sebi_cap_category(metadata.pdSectorInd)` |
| `sma_200` | `priceInfo.priceBand.lowerPrice` (best available proxy) |
| `pb_ratio`, `roe`, `div_yield` | Not available in basic NSE quote — set to `0.0` |

**Returns `None`** if `pe_ratio == 0` (incomplete data) or on any exception after retries — triggers fallthrough to `_fetch_yfinance()`.

---

#### `_fetch_yfinance(symbol: str) -> Optional[Dict]`

**Secondary data provider** — Yahoo Finance with `.NS` suffix.

Uses `yf.Ticker(f"{symbol}.NS").info` wrapped in a `@retry` decorator (full retry spec → [LLD 05 §3](./05_retry_and_fallback.md#3-market_datapy--nsepython--yfinance-retry)).

**Retry policy:**

| Setting | Value |
|---|---|
| `max_attempts` | 3 |
| `base_delay` | 2.0s (longer — Yahoo rate-limits more aggressively) |
| `multiplier` | 2.0 |
| `retryable_on` | `(Exception,)` |

**Data extracted from yfinance `info` dict:**

| Field | yfinance key |
|---|---|
| `pe_ratio` | `trailingPE` |
| `pb_ratio` | `priceToBook` |
| `roe` | `returnOnEquity` × 100 |
| `div_yield` | `dividendYield` × 100 |
| `sma_200` | `twoHundredDayAverage` |
| `cap_category` | `_infer_cap_category(marketCap)` |
| `sector` | `sector` → fallback `_infer_sector()` |

**Returns `None`** if `trailingPE` is absent or on exception after retries.

---

#### `get_stock_fundamental_data(symbol: str) -> Dict`

**Public API** — orchestrates the 4-tier fallback chain.

```
1. TTL cache hit (< 24h old)
    ↓ miss
2. _fetch_nsepython()
    ↓ None
3. _fetch_yfinance()
    ↓ None
4. STOCK_METADATA_DB lookup
    ↓ not found
5. Generic defaults (pe=22.5, pb=3.2, roe=15.0, div_yield=1.0, sma_200=0.0)
```

Normalises symbol by uppercasing and stripping `.NS` / `.BO` suffixes before lookup.

Stores result in `_FUNDAMENTALS_CACHE` with `expiry = time.time() + 86400`.

**Returns:** Dict with keys: `symbol`, `sector`, `cap_category`, `pe_ratio`, `pb_ratio`, `roe`, `div_yield`, `sma_200`.

---

#### `enrich_holdings_with_fundamentals(holdings: List[Dict]) -> List[Dict]`

Iterates over holdings list, calls `get_stock_fundamental_data()` per symbol, and merges fundamental fields into a copy of each holding dict.

**Fields added/overwritten per holding:**

| Field | Source |
|---|---|
| `sector` | Fundamental data (preserves existing if fund data absent) |
| `cap_category` | Fundamental data |
| `pe_ratio` | Fundamental data |
| `pb_ratio` | Fundamental data |
| `roe` | Fundamental data |
| `div_yield` | Fundamental data |
| `sma_200` | Fundamental data |
| `trend_200_sma` | Computed: `"Bullish (Above SMA)"` / `"Bearish (Below SMA)"` / `"Neutral"` |

`trend_200_sma` is `"Neutral"` when `sma_200 == 0` (data unavailable). This field is consumed by the Phase 3 rule engine — see [LLD 03 §2](./03_phase3_ai_advisory.md#2-srcservicesrebalancerpy--deterministic-rule-engine).

---

#### `_infer_sector(symbol: str) -> str`

Static `SECTOR_MAP` lookup. Returns `"Diversified / Others"` for unknown symbols.

---

#### `_sebi_cap_category(sector_ind: str) -> str`

Maps NSE sector index name string to SEBI-defined cap category.

| Keyword match | Returns |
|---|---|
| `NIFTY 50`, `NIFTY100`, `LARGE` | `"Large Cap"` |
| `MIDCAP`, `NIFTY 150`, `MID` | `"Mid Cap"` |
| `SMALLCAP`, `SMALL` | `"Small Cap"` |
| No match | `"Large Cap"` (default for unclassified NSE stocks) |

---

#### `_infer_cap_category(market_cap: float) -> str`

Fallback cap classification by raw market cap value (INR).

| Threshold | Returns |
|---|---|
| ≥ ₹20,000 Cr (`200_000_000_000`) | `"Large Cap"` |
| ≥ ₹5,000 Cr (`50_000_000_000`) | `"Mid Cap"` |
| Below | `"Small Cap"` |

---

## 2. `src/services/analytics_engine.py` — Quantitative Analytics Engine

Module constant: `RISK_FREE_RATE = 0.071` (Indian 10-Year G-Sec yield ~7.1%).

Singleton instance `analytics_engine` exported at module level.

### `QuantitativeAnalyticsEngine` — Class

---

#### `calculate_portfolio_metrics(holdings, trades=None) -> Dict`

**Main entry point.** Computes all portfolio-level quantitative metrics in a single pass.

**Returns `_empty_metrics()`** if `holdings` is empty.

**Computation steps:**

1. `total_invested`, `total_current`, `total_pnl`, `overall_return` — simple sum over holdings
2. XIRR — calls `_xirr_from_trades(trades, total_current)` if `trades` provided, else `_estimate_xirr()`
3. Single pass over holdings to compute weighted averages:
   - `weighted_pe` — value-weighted P/E ratio
   - `weighted_roe` — value-weighted ROE
   - `portfolio_beta` — value-weighted beta via `_infer_beta()`
   - `hhi` — Herfindahl-Hirschman Index: `Σ(weight% ²)`
4. `est_vol = max(0.12 × portfolio_beta, 0.08)` — estimated annualised volatility
5. `sharpe = (ann_return − RISK_FREE_RATE) / est_vol`
6. `sortino = (ann_return − RISK_FREE_RATE) / (est_vol × 0.7)`

**Returns:**

| Key | Description |
|---|---|
| `xirr_percentage` | Extended IRR % |
| `overall_return_percentage` | Simple total return % |
| `portfolio_beta` | Value-weighted beta vs market |
| `sharpe_ratio` | Risk-adjusted return (Sharpe) |
| `sortino_ratio` | Downside risk-adjusted return |
| `herfindahl_index` | Concentration index (higher = more concentrated) |
| `weighted_pe` | Value-weighted P/E |
| `weighted_roe` | Value-weighted ROE |
| `risk_profile_tag` | Human-readable risk label |

---

#### `_xirr_from_trades(trades, current_value) -> float`

Builds a cash flow series from trade history and solves for XIRR using Newton-Raphson.

Trade data sourced from `zerodha_service.get_trades()` — see [LLD 01 §2](./01_phase1_auth_and_holdings.md#get_trades---listdict).

**Cash flow construction:**
- `BUY` transactions → negative cash flow (`-qty × price`)
- `SELL` transactions → positive cash flow (`+qty × price`)
- Current portfolio value → positive terminal cash flow at today's date

**Date parsing:** Tries `fill_timestamp` first, falls back to `order_timestamp`. Skips trades with unparseable dates.

**Returns `0.0`** if no valid cash flows can be built.

Delegates to `_newton_xirr(amounts, days)` after sorting by date.

---

#### `_newton_xirr(amounts, days, guess=0.1, max_iter=100, tol=1e-6) -> float`

Newton-Raphson solver for XIRR.

**Formula:**
```
NPV  = Σ( amount_i / (1 + rate)^(days_i / 365) )
dNPV = Σ( -days_i/365 × amount_i / (1 + rate)^(days_i/365 + 1) )
rate_new = rate - NPV / dNPV
```

Iterates until `|rate_new − rate| < tol` or `max_iter` reached.

**Returns:** `rate × 100` (as percentage), rounded to 2dp. Returns `0.0` if solver does not converge.

---

#### `_estimate_xirr(invested, current, holding_years=1.2) -> float`

Fallback CAGR estimate when no trade history is available.

**Formula:** `((current / invested)^(1 / holding_years) − 1) × 100`

Returns `0.0` if either value is ≤ 0 or on any arithmetic exception.

---

#### `_infer_beta(symbol: str, sector: str) -> float`

Static beta lookup for 10 known NSE symbols. Falls back to sector-based estimates:

| Sector keyword | Beta |
|---|---|
| Technology | 0.90 |
| Financial | 1.10 |
| Pharma / Healthcare | 0.70 |
| Automotive / Metals | 1.25 |
| Default | 1.00 |

---

#### `_risk_tag(beta: float, hhi: float) -> str`

| Condition | Tag |
|---|---|
| `beta > 1.20` or `hhi > 2500` | `"High risk / Aggressive growth"` |
| `beta < 0.85` and `hhi < 1500` | `"Low volatility / Defensive"` |
| Otherwise | `"Moderate risk / Balanced growth"` |

---

#### `_empty_metrics() -> Dict`

Returns a zeroed-out metrics dict with `portfolio_beta=1.0` and `risk_profile_tag="Moderate risk / Balanced growth"`.

---

## 3. `src/services/tax_harvesting.py` — Tax Harvesting Analyzer

### Module-level constants

| Constant | Value | Description |
|---|---|---|
| `STCG_TAX_RATE` | `0.20` | 20% Short Term Capital Gains tax rate |
| `LTCG_TAX_RATE` | `0.125` | 12.5% Long Term Capital Gains tax rate |
| `LTCG_EXEMPTION_LIMIT` | `125000.0` | ₹1.25 Lakh annual LTCG exemption |

> **Known issue:** Logger name is `"tax_harvesting"` — should be `"portfolio_assistant.tax_harvesting"` to align with the logger hierarchy defined in [LLD 04 §1](./04_logging.md#1-srccorelogs_configpy--central-setup).

Singleton instance `tax_harvesting_analyzer` exported at module level.

### `TaxHarvestingAnalyzer` — Class

---

#### `analyze_tax_harvesting(holdings: List[Dict]) -> Dict`

Iterates over all holdings, classifies each as STCG or LTCG via `_is_long_term()`, and accumulates gains/losses.

**Per holding:**
- `pnl` taken from holding dict if present, else computed as `(last_price − average_price) × quantity`
- Loss-making holdings are added to `harvestable_loss_candidates` with a plain-English `recommendation` string

**Tax calculations:**

| Metric | Formula |
|---|---|
| `net_stcg` | `max(0, stcg_gains − stcg_losses)` |
| `net_ltcg` | `max(0, ltcg_gains − ltcg_losses)` |
| `stcg_tax_payable` | `net_stcg × 0.20` |
| `taxable_ltcg` | `max(0, net_ltcg − 125000)` |
| `ltcg_tax_payable` | `taxable_ltcg × 0.125` |
| `total_estimated_tax` | `stcg_tax_payable + ltcg_tax_payable` |
| `potential_tax_savings` | `(stcg_losses × 0.20) + (ltcg_losses × 0.125)` |

**Returns:**

| Key | Description |
|---|---|
| `stcg_gains` / `stcg_losses` | Gross short-term gains and losses |
| `net_stcg` | Net taxable STCG |
| `stcg_tax_payable` | Estimated STCG tax |
| `ltcg_gains` / `ltcg_losses` | Gross long-term gains and losses |
| `net_ltcg` | Net taxable LTCG |
| `ltcg_exemption_used` | Amount of ₹1.25L exemption consumed |
| `ltcg_tax_payable` | Estimated LTCG tax after exemption |
| `total_estimated_tax` | Combined tax liability |
| `potential_tax_savings` | Tax savings achievable by harvesting all current losses |
| `harvestable_loss_candidates` | List of `{symbol, holding_type, unrealized_loss, quantity, last_price, recommendation}` |

---

#### `_is_long_term(auth_date_str: str) -> bool`

Determines if a holding qualifies as long-term (> 365 days).

| Condition | Returns |
|---|---|
| `auth_date_str` is empty | `True` (assumes core portfolio is LTCG) |
| Date parses and age ≥ 365 days | `True` |
| Date parses and age < 365 days | `False` |
| Date parse fails | `True` (safe default) |

**Date format expected:** `YYYY-MM-DD` (splits on space to handle datetime strings).

---

## 4. `src/api/analytics.py` — Analytics Router

Prefix: `/api/v1/analytics`

All endpoints accept an optional `X-Enctoken` header. Resolved against `settings.ZERODHA_ENCTOKEN` as fallback.

Log lines for all endpoints → [LLD 04 §3](./04_logging.md#analyticspy)

### `GET /fundamentals`

Returns holdings enriched with fundamental ratios.

**Steps:** `get_holdings()` → `enrich_holdings_with_fundamentals()`

**Response:** `{status: "success", holdings: [enriched_holding, ...]}`

---

### `GET /performance`

Returns full quantitative portfolio metrics.

**Steps:** `get_holdings()` → `enrich_holdings_with_fundamentals()` → `get_trades()` → `calculate_portfolio_metrics(enriched, trades)`

**Response:** `{status: "success", metrics: {xirr_percentage, portfolio_beta, sharpe_ratio, sortino_ratio, herfindahl_index, weighted_pe, weighted_roe, risk_profile_tag}}`

---

### `GET /tax-harvesting`

Returns STCG/LTCG tax liability and loss harvesting candidates.

**Steps:** `get_holdings()` → `analyze_tax_harvesting(holdings)`

**Response:** `{status: "success", tax_analysis: {...}}`

---

All three endpoints return `HTTP 500` with exception detail on unhandled errors, with full stack trace logged via `exc_info=True`.
