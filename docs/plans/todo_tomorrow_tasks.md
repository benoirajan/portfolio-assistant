# Action Items & TODO Tasks

---

## 📋 Upcoming TODO Tasks

### 1. 🔍 Flow Analysis of 3-Stage Prompt Application Execution
* **Objective:** Map out and document the full end-to-end flow of how the application runs the 3-stage prompt pipeline.
* **Details:**
  * Trace the flow from UI entrypoint (`backend/src/ui/app.py`) & FastAPI endpoints (`backend/src/api/advisory.py`).
  * Detail execution steps through `get_multi_stage_advisory()` in `backend/src/services/llm_advisor.py`:
    1. Rule Engine evaluation (`rebalancer.py`) & market context enrichment (`news_search.py`).
    2. Stage 1: Portfolio & Market Diagnosis prompt execution & Pydantic schema validation.
    3. Stage 2: Opportunity selection, conviction screening & ticker master validation (`market_data.py`).
    4. Stage 3: Bounded budget execution decision & whole-share calculation.
  * Document data transformations and fallback paths between stages.

---

### 2. 💾 User Portfolio Data & Symbol Persistence
* **Objective:** Set up persistence for user holdings, symbols, and portfolio details so previously fetched data remains available across session restarts.
* **Details:**
  * Implement local disk/database storage (e.g. SQLite, JSON store, or Redis cache persistence) for holdings fetched from Zerodha or manual input.
  * Store symbol metadata, cost bases, quantity, and enriched fundamental metrics.
  * Add automatic re-hydration on startup so users don't have to re-fetch or re-enter portfolio data every time.

---

### 3. 🧹 Remove Legacy Single-Pass Prompt & Replace with Rule-Based Analysis
* **Objective:** Remove legacy single-pass prompt execution and replace single-pass recommendation calls with pure deterministic rule-based analysis.
* **Details:**
  * Deprecate and remove `_build_prompt()`, `_call_gemini()`, and `_call_ollama()` from `backend/src/services/llm_advisor.py`.
  * Update `get_recommendations()` to directly use `_rule_based_recommendations()` powered by `evaluate_rules()`.
  * Ensure multi-stage advisory remains active for LLM-driven deep analysis, while quick single-pass recommendations rely purely on rule-based logic.
  * Clean up references across `backend/src/api/advisory.py` and `backend/src/ui/app.py`.

---

## ✅ Completed Tasks

### Task 1: Comprehensive DEBUG Level Prompt Payload Logging (Completed)
* **Objective:** Ensure all multi-stage LLM prompt payloads are logged at `DEBUG` level in `backend/src/services/llm_advisor.py`.
* **Verification:** Logged rendered prompt strings before invoking Gemini for Stage 1, Stage 2, Stage 3, and legacy mode. Verified via unit tests in `backend/tests/test_llm_advisor.py`.

### Task 2: Audit `google-genai` SDK Structured Output & Function Calling Syntax (Completed)
* **Objective:** Audit `google-genai` Python SDK integration (`from google import genai`, `from google.genai import types`) in `llm_advisor.py`.
* **Verification:** Upgraded `genai.Client(api_key=...)` initialization, verified structured output schemas, added tool declaration support, and verified response extraction fallback.
