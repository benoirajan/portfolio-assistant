# Flow Analysis & Architecture Mapping of 3-Stage Prompt Application Execution

This document maps out the end-to-end flow of the 3-Stage Prompt Pipeline in the `portfolio_assistant` application.

## 1. Frontend & API Trigger Points
- **Frontend (`backend/src/ui/app.py`)**: The frontend currently relies on the fast rule-based recommendations endpoint (`advisory/recommendations`).
- **API Endpoints (`backend/src/api/advisory.py`)**: Exposes the pipeline via `/pipeline` (synchronous) and `/stream` (SSE). The SSE stream uses an `asyncio` executor to prevent blocking and stream progress across the 3 stages.

## 2. The Core Orchestrator (`backend/src/services/llm_advisor.py`)
- **Context Gathering**: Before prompting the LLM, the system performs deterministic rule evaluation via `evaluate_rules` (in `rebalancer.py`) and live news injection via `search_company_news` (in `news_search.py`).
- **Stage 1 (Diagnosis)**: Analyzes the portfolio as a long-term analyst without making trade decisions. Validated strictly against `Stage1Diagnosis` Pydantic schema.
- **Stage 2 (Screening)**: Ranks opportunities. Contains critical guardrails validating recommended symbols against `market_data_service.is_valid_nse_symbol`.
- **Stage 3 (Execution)**: Determines exact share purchases. Enforces budget caps deterministically.

## 3. Resilience and Fallbacks
The system is highly resilient to API timeouts and rate limits:
- A rate limit exception *never bubbles up* to break the SSE stream. 
- The `_call_gemini_schema` method catches exceptions that exhaust the `@retry` wrapper, logging the error and returning `None`.
- The main orchestrator (`get_multi_stage_advisory`) invokes hardcoded dummy fallback functions (e.g., `_fallback_stage1`, `_fallback_stage2`) if the LLM fails.
- The SSE endpoint streams this fallback data instead of dropping the connection, ensuring UI stability.

## 4. Current Gaps / Next Steps
- **Missing Sector News**: Macro-level sector context (`search_sector_news`) is missing from the LLM prompt.
- **Action Support**: Stage 3 Execution supports `BUY`, `PARTIALLY_INVEST`, and `WAIT`, but does not explicitly handle `SELL` or `TRIM` workflows.
- **Caching**: The multi-stage pipeline is executed fresh on every hit; caching should be added.
