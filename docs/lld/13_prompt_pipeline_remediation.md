# LLD-13: 3-Stage AI Advisory Prompt Pipeline Remediation

**Issue:** [#19 — Audit & Remediation of 3-Stage AI Advisory Prompt Architecture](https://github.com/benoirajan/portfolio-assistant/issues/19)
**Status:** Implemented
**Date:** 2026-10-22

---

## Problem Summary

An audit of the 3-stage prompt pipeline (`prompt1.md`, `Prompt2.md`, `prompt3.md`) and its Python orchestration (`llm_advisor.py`) identified four critical categories of defects:

| # | Category | Root Cause |
|---|----------|-----------|
| 1 | Portfolio denominator missing | Stage 1 & 3 prompts omitted `total_portfolio_value` and `available_cash`, making post-trade concentration math impossible for the LLM |
| 2 | Unconstrained candidate universe | Stage 2 asked the LLM to screen "new Indian listed companies" from 2,000+ NSE stocks without any price filter, causing hallucination and recommending unaffordable stocks (MRF @ ₹1.3L for a ₹5k tranche) |
| 3 | Micro-basket anti-pattern | Stage 3 allowed splitting small tranches (≤₹10k) across multiple stocks, immediately loss-making after Indian DP charges (~₹15.93/debit) and STT |
| 4 | Prompt bloat & stateful references | All 3 prompts repeated identical 60-line checklists; contained 18+ "Do NOT" constraints; referenced "as established in this chat" — incompatible with stateless API architecture |

---

## Architecture Changes

### WS-1: Portfolio Denominator Injection

**File:** `backend/src/services/llm_advisor.py`

- `_build_stage1_prompt()`: Added `available_cash: float = 0.0` parameter. Injects `PORTFOLIO TOTAL VALUE`, `CASH AVAILABLE (uninvested)`, and `CONCENTRATION LIMITS` into the Stage 1 prompt header.
- `_build_stage3_prompt()`: Added `total_portfolio_value: float = 0.0` parameter. Injects `TOTAL PORTFOLIO VALUE`, `POST-TRADE CONCENTRATION LIMIT`, and the absolute limit (15% of total portfolio value in ₹).
- `run_stage1_diagnosis()`: Now returns `total_value` as a 5th element of its tuple, accepts `available_cash`.
- `run_stage3_execution()`: Accepts `total_portfolio_value` and threads it to the prompt builder.
- `get_multi_stage_advisory()`: Accepts `available_cash`; computes `total_portfolio_value` from Stage 1 and threads it to Stage 3. Adds `total_portfolio_value` to the response payload.

### WS-2: Pre-Filtered Candidate Universe

**Files:** `backend/src/services/market_data.py`, `backend/src/services/llm_advisor.py`

- `MarketDataService.get_affordable_nifty_universe(max_price: float)`: New method. Iterates `STOCK_METADATA_DB`, resolves the latest price (live quote → SMA-200 fallback), and returns only stocks where `price <= max_price`. Result is sorted by price descending.
- `_build_stage2_prompt()`: Added `candidate_universe: Optional[List[Dict]]` parameter. If provided, injects the filtered list as `PRE-FILTERED AFFORDABLE CANDIDATE UNIVERSE` with a hard constraint: "Rank ONLY candidates from the list above or from EXISTING HOLDINGS. Do NOT suggest any symbol outside this list."
- `run_stage2_screening()`: Accepts `total_budget`; calls `get_affordable_nifty_universe(max_price=total_budget)` and passes the result to the prompt builder.

### WS-3: Whole-Share Single-Asset Guard

**Files:** `backend/src/services/llm_advisor.py`

- `Stage3Execution` Pydantic model: Added `residual_cash_routing: str = ""` and `is_single_asset_tranche: bool = False`.
- `_build_stage3_prompt()`: When `total_budget <= 10_000`, injects a `SMALL TRANCHE RULE (MANDATORY)` block explaining the DP charge economics and requiring a single-stock allocation with residual cash routing.
- `run_stage3_execution()`: Post-LLM guard — if `total_budget <= 10_000` and the LLM still returned multiple purchases, automatically trims to the single highest-amount purchase, recomputes `cash_to_keep`, sets `is_single_asset_tranche = True`, and auto-populates `residual_cash_routing` if absent.
- WAIT action: Tightened — prompt now states WAIT is only valid if no candidate is purchasable within the budget AND residual cash routing is specified.

### WS-4: Prompt File Streamlining

| File | Before | After | Key Change |
|------|--------|-------|-----------|
| `prompt1.md` | 366 lines — included manual `[PASTE HERE]` blocks, 60-line checklist, stateful chat refs | ~85 lines | Scoped to Stage 1 only; programmatic context listed; 5 analysis rules; output schema documented |
| `Prompt2.md` | 363 lines — full checklist repeated, open "screen new Indian equities" instruction | ~90 lines | Accepts pre-filtered universe; hard constraint to not suggest symbols outside the list; 4-tier conviction table |
| `prompt3.md` | 299 lines — allowed multi-stock splits, "as established in this chat" | ~90 lines | Small tranche rule with DP-charge economics; WAIT tightened; residual cash routing required |

---

## Data Flow (Updated)

```
get_multi_stage_advisory(holdings, total_budget, available_cash)
  │
  ├── run_stage1_diagnosis(available_cash) ──► _build_stage1_prompt(total_value, available_cash)
  │     └── returns (stage1_data, rule_flags, source, llm_provider, total_portfolio_value)
  │
  ├── run_stage2_screening(total_budget)
  │     ├── get_affordable_nifty_universe(max_price=total_budget) ──► pre-filtered list
  │     └── _build_stage2_prompt(candidate_universe=pre_filtered)
  │
  └── run_stage3_execution(total_portfolio_value)
        ├── _build_stage3_prompt(total_portfolio_value, small_tranche_rule_if_≤10k)
        └── Post-LLM guard: trim to single purchase if total_budget ≤ 10,000
```

---

## Testing

All 64 existing tests pass after update. `test_prompt_rules` updated to assert `ANALYSIS RULES:`, `PORTFOLIO TOTAL VALUE:`, and `CONCENTRATION LIMITS:` in Stage 1 prompt output.

---

## Out of Scope (Future Issues)

- Tax-lot tracking (STCG/LTCG differentiation) — requires holdings DB schema changes.
- Idle cash auto-sweep to Liquid BeES — execution-side trading concern, not advisory pipeline.
- Nifty 100/200 full index refresh — current `STOCK_METADATA_DB` covers 14 large-cap stocks; a live NSE instrument list pull would expand coverage.
