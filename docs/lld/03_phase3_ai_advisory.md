# LLD 03 — Phase 3: AI Advisory Engine

**Files covered:**
`src/core/config.py` · `src/services/rebalancer.py` · `src/services/llm_advisor.py` · `src/api/advisory.py` · `src/main.py` · `src/ui/app.py` · `requirements.txt` · `.env.example`

**Cross-references:**
- Config base fields (Phase 1) → [LLD 01 §1](./01_phase1_auth_and_holdings.md#1-srccoreconfpy--settings)
- Holdings enrichment input (Phase 2) → [LLD 02 §1](./02_phase2_analytics_engine.md#enrich_holdings_with_fundamentalsholdings-listdict---listdict)
- Retry policies for Gemini & Ollama → [LLD 05 §5](./05_retry_and_fallback.md#5-llm_advisorpy--gemini--ollama-retry)
- Log lines emitted here → [LLD 04 §3](./04_logging.md#advisorypy)
- Gemini SDK integration reference → [api-references/Gemini_api_doc.md](../api-references/Gemini_api_doc.md)

---

## 1. `src/core/config.py` — LLM Settings

Added 4 new fields to the `Settings` class (base fields documented in [LLD 01 §1](./01_phase1_auth_and_holdings.md#1-srccoreconfpy--settings)):

| Field | Type | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `str` | `"gemini"` | Active LLM backend. Accepts `"gemini"` or `"ollama"` |
| `GEMINI_API_KEY` | `str` | `""` | Google AI Studio API key. Auto-resolved from env by SDK |
| `OLLAMA_BASE_URL` | `str` | `"http://localhost:11434"` | Base URL for self-hosted Ollama instance |
| `OLLAMA_MODEL` | `str` | `"mistral"` | Ollama model name (e.g. `mistral`, `llama3`) |

**Design note:** `GEMINI_API_KEY` is pushed into `os.environ` inside `_call_gemini()` via `os.environ.setdefault()` so the `google-genai` SDK can auto-resolve it — matching the documented pattern in [api-references/Gemini_api_doc.md](../api-references/Gemini_api_doc.md#api-key-configuration).

---

## 2. `src/services/rebalancer.py` — Deterministic Rule Engine

**New file.** Evaluates portfolio holdings against 3 hard rules before the LLM step. Returns a list of structured flag dicts.

### Function: `evaluate_rules(holdings, max_single_stock_pct, max_sector_pct)`

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `holdings` | `List[Dict]` | — | Enriched holdings list from `market_data_service` — see [LLD 02 §1](./02_phase2_analytics_engine.md#enrich_holdings_with_fundamentalsholdings-listdict---listdict) |
| `max_single_stock_pct` | `float` | `15.0` | Max allowed weight % for any single stock |
| `max_sector_pct` | `float` | `25.0` | Max allowed weight % for any single sector |

**Returns:** `List[Dict]` — each dict has `{symbol, rule, severity, detail}`

**Rules evaluated:**

| Rule ID | Trigger Condition | Severity | Symbol field |
|---|---|---|---|
| `OVER_CONCENTRATION` | Single stock weight > `max_single_stock_pct` | `HIGH` | Stock symbol |
| `UNDERPERFORMANCE` | LTP < 200-day SMA **and** ROE ≤ 0 | `MEDIUM` | Stock symbol |
| `SECTOR_OVERWEIGHT` | Sector total weight > `max_sector_pct` | `MEDIUM` | `None` |

**Implementation detail:** Sector values are aggregated in a single pass before the per-stock loop to avoid O(n²) recalculation.

---

## 3. `src/services/llm_advisor.py` — LLM Advisory Service

**New file.** Orchestrates the full advisory pipeline:

```
evaluate_rules()
    ↓
_build_prompt()
    ↓
_call_gemini() or _call_ollama()
    ↓ (on failure / validation error)
_rule_based_recommendations()   ← fallback
    ↓
return {recommendations, rule_flags, source, investment_goal, llm_provider}
```

### 3.1 Pydantic Response Schema (Guardrails)

**`Recommendation`** — single stock recommendation:

| Field | Type | Validation |
|---|---|---|
| `symbol` | `str` | Must exist in current holdings (enforced post-parse) |
| `action` | `Literal["BUY","SELL","HOLD","TRIM"]` | Enum enforced by Pydantic `Literal` |
| `target_allocation_pct` | `float` | Must be ≥ 0, rounded to 2dp |
| `confidence_score` | `float` | Must be in `[0.0, 1.0]`, rounded to 2dp |
| `rationale` | `str` | Free text, 1-2 sentences |

**`RecommendationList`** — full LLM response wrapper:

| Validation | Rule |
|---|---|
| Allocation sum | Sum of all `target_allocation_pct` must not exceed 100% |
| Small-cap cap | Any Small/Mid Cap stock with `target_allocation_pct > 20%` is clamped to 20% post-parse |
| Symbol existence | Symbols not in current holdings are filtered out (hallucination guard) |

### 3.2 `_build_prompt()` — Data Minimization

Absolute ₹ values are **never** included in the LLM payload. Only the following fields are sent per stock:

- `weight_pct` — relative portfolio weight %
- `sector`, `cap_category`
- `pe_ratio`, `pb_ratio`, `roe_pct`, `div_yield_pct`
- `trend_200_sma` — sourced from `enrich_holdings_with_fundamentals()` in [LLD 02 §1](./02_phase2_analytics_engine.md#enrich_holdings_with_fundamentalsholdings-listdict---listdict)

Rule engine flag details are appended as a plain-text summary list at the end of the prompt.

### 3.3 `_call_gemini()`

| Setting | Value |
|---|---|
| Client init | `genai.Client()` — SDK auto-resolves key from `os.environ` |
| Model | `gemini-3.6-flash` |
| Output mode | `response_mime_type="application/json"` + `response_schema=RecommendationList` |
| Temperature | `0.2` — low for deterministic financial output |
| Max tokens | `2048` |
| Retry | 3 attempts, **429 only** — full spec in [LLD 05 §5.1](./05_retry_and_fallback.md#51-gemini--429-only-retry) |

### 3.4 `_call_ollama()`

| Setting | Value |
|---|---|
| Endpoint | `{OLLAMA_BASE_URL}/api/generate` |
| Stream | `False` |
| Timeout | 60 seconds |
| Retry | 3 attempts on any exception — full spec in [LLD 05 §5.2](./05_retry_and_fallback.md#52-ollama--general-retry) |

### 3.5 `_rule_based_recommendations()` — Deterministic Fallback

Pure fallback — no external calls. Maps rule flags to actions:

| Rule flag | Action | Target allocation | Confidence |
|---|---|---|---|
| `OVER_CONCENTRATION` | `TRIM` | Capped at 15% | `0.75` |
| `UNDERPERFORMANCE` | `SELL` | Current weight | `0.75` |
| No flags | `HOLD` | Current weight | `0.60` |

`source` field in the response is `"llm"` or `"rule_engine"` — surfaced in the UI as a badge.

---

## 4. `src/api/advisory.py` — Advisory REST Endpoint

**New file.**

### `GET /api/v1/advisory/recommendations`

**Query parameters:**

| Param | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `investment_goal` | `str` | `"Moderate Growth"` | — | Passed verbatim into LLM prompt |
| `max_single_stock_pct` | `float` | `15.0` | `5.0 – 50.0` | Single stock concentration cap |
| `max_sector_pct` | `float` | `25.0` | `10.0 – 60.0` | Sector concentration cap |

**Request header:**

| Header | Description |
|---|---|
| `X-Enctoken` | Optional — Zerodha enctoken for live holdings |

**Response shape:**
```json
{
  "status": "success",
  "recommendations": [...],
  "rule_flags": [...],
  "source": "llm | rule_engine",
  "investment_goal": "Moderate Growth",
  "llm_provider": "gemini-3.6-flash | null"
}
```

Log lines → [LLD 04 §3](./04_logging.md#advisorypy)

---

## 5. `src/main.py` — Router Registration

Added:
```python
from src.api.advisory import router as advisory_router
app.include_router(advisory_router)
```

Full `main.py` spec → [LLD 01 §5](./01_phase1_auth_and_holdings.md#5-srcmainpy--fastapi-application-entry-point)

---

## 6. `src/ui/app.py` — AI Advisory Tab

### Sidebar additions

- `investment_goal` selectbox: `["Moderate Growth", "Aggressive Growth", "Capital Preservation", "Income / Dividend", "Balanced"]`
- `max_stock_cap` slider: 5–40%, default 15%

### New backend fetch

```python
advisory_res, _ = fetch_from_backend(
    f"advisory/recommendations?investment_goal={investment_goal}"
    f"&max_single_stock_pct={max_stock_cap}&max_sector_pct={max_sector_cap}",
    enctoken_input=enctoken_val,
)
```

### Offline fallback

`fetch_fallback_local()` extended — parses query string params and calls `get_recommendations()` directly when FastAPI server is offline.

### Tab 5 — 🤖 AI Advisory

| UI Component | Purpose |
|---|---|
| Source badge (`st.success` / `st.info`) | Shows LLM provider name or rule engine fallback indicator |
| `st.warning` banners | Rule engine alerts with 🔴 HIGH / 🟡 MEDIUM severity icons |
| `st.expander` per stock | Expandable recommendation card with `st.progress` confidence bar |
| `st.dataframe` | Summary table with `ProgressColumn` for confidence scores |

**Tab count change:** `tab1, tab2, tab3, tab4` → `tab1, tab2, tab3, tab4, tab5`

---

## 7. `requirements.txt`

Added:
```
google-genai>=1.0.0
```

---

## 8. `.env.example`

Added:
```ini
# Phase 3 — AI Advisory Engine
# Get your free Gemini API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini        # "gemini" | "ollama"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## 9. Trade Basket Feature

**New capability added to Phase 3.** After receiving LLM recommendations, the user can enter a max budget and generate a deterministic trade basket — no second LLM call.

### 9.1 Design Principles

- Absolute ₹ values never leave the backend — the LLM only ever sees `weight_pct`
- Basket math is pure arithmetic on the backend using real holdings data
- User's `max_budget` caps total BUY spend; SELL/TRIM quantities are computed from the delta between current and target allocation independently
- All four actions are supported: `BUY`, `SELL`, `TRIM`, `HOLD` (HOLD items are excluded from the basket)

### 9.2 `POST /api/v1/advisory/basket`

**New endpoint in `src/api/advisory.py`.**

**Request body:**

```json
{
  "recommendations": [
    {
      "symbol": "INFY",
      "action": "BUY",
      "target_allocation_pct": 12.0,
      "confidence_score": 0.7,
      "rationale": "High ROE..."
    }
  ],
  "max_budget": 50000.0
}
```

| Field | Type | Description |
|---|---|---|
| `recommendations` | `List[Recommendation]` | Full recommendations list from `/recommendations` response |
| `max_budget` | `float` | Max ₹ the user is willing to spend on BUY orders. Does not cap SELL/TRIM |

**Response shape:**

```json
{
  "status": "success",
  "basket": [
    {
      "symbol": "INFY",
      "action": "BUY",
      "quantity": 4,
      "estimated_value": 14200.0,
      "reason": "High ROE..."
    }
  ],
  "total_buy_value": 14200.0,
  "total_sell_value": 5600.0,
  "budget_utilised_pct": 28.4
}
```

| Field | Type | Description |
|---|---|---|
| `basket` | `List[BasketItem]` | One item per non-HOLD recommendation with quantity > 0 |
| `total_buy_value` | `float` | Sum of `estimated_value` for all BUY items |
| `total_sell_value` | `float` | Sum of `estimated_value` for all SELL/TRIM items |
| `budget_utilised_pct` | `float` | `total_buy_value / max_budget * 100` |

### 9.3 Basket Calculation Logic

All math runs in `src/api/advisory.py` using live holdings fetched inside the endpoint.

**Step 1 — Compute total portfolio value:**
```
total_value = sum(quantity × last_price for each holding)
```

**Step 2 — Per recommendation:**

| Action | Formula |
|---|---|
| `BUY` | `target_₹ = total_value × target_pct / 100`<br>`current_₹ = quantity × last_price`<br>`delta_₹ = target_₹ − current_₹`<br>`shares = floor(delta_₹ / last_price)` |
| `SELL` | `target_₹ = total_value × target_pct / 100`<br>`delta_₹ = current_₹ − target_₹`<br>`shares = floor(delta_₹ / last_price)` |
| `TRIM` | Same formula as SELL |
| `HOLD` | Excluded from basket |

**Step 3 — Apply budget cap to BUY items:**
- Sort BUY items by `confidence_score` descending
- Accumulate spend; once `running_total + estimated_value > max_budget`, recalculate `quantity = floor(remaining_budget / last_price)`
- Items that result in `quantity = 0` are excluded from the basket

**Step 4 — Exclude zero-quantity items** (e.g. already at target, or price > remaining budget).

### 9.4 Pydantic Request/Response Models

Added to `src/api/advisory.py`:

```python
class BasketRequest(BaseModel):
    recommendations: List[Recommendation]   # reuses existing Pydantic model
    max_budget: float = Field(gt=0)

class BasketItem(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL", "TRIM"]
    quantity: int
    estimated_value: float
    reason: str

class BasketResponse(BaseModel):
    status: str
    basket: List[BasketItem]
    total_buy_value: float
    total_sell_value: float
    budget_utilised_pct: float
```

---

## 10. Gemini API Bug Fixes

Three bugs found by comparing the implementation against [api-references/Gemini_api_doc.md](../api-references/Gemini_api_doc.md):

### Bug 1 — Wrong model name

| | Value |
|---|---|
| Before | `model="gemini-2.0-flash"` |
| After (doc) | `model="gemini-2.5-flash"` |
| After (live 404) | `model="gemini-3.6-flash"` — API returned 404 stating `gemini-2.5-flash` is no longer available to new users |

### Bug 2 — Wrong client initialisation

| | Code |
|---|---|
| Before | `genai.Client(api_key=settings.GEMINI_API_KEY)` |
| After | `os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)` then `genai.Client()` |

The official doc shows the SDK auto-resolves `GEMINI_API_KEY` from the environment. Passing `api_key=` directly is not the documented pattern.

### Bug 3 — Manual JSON parsing instead of native structured output

| | Approach |
|---|---|
| Before | Manually stripped markdown fences from response text, then called `json.loads()` |
| After | `types.GenerateContentConfig(response_mime_type="application/json", response_schema=RecommendationList)` — Gemini returns clean structured JSON natively, `model_validate_json(llm_raw)` called directly |

Using `response_schema` eliminates the fragile string manipulation entirely and guarantees the response conforms to the `RecommendationList` shape before it even reaches the application. See [Structured JSON Output example](../api-references/Gemini_api_doc.md#6-structured-json-output-pydantic).

---

## 11. Exporting Baskets to Zerodha (`/orders/baskets`)

The generated trade basket can be pushed directly into Zerodha Baskets without automated trade execution.

### 11.1 Endpoints Added to `src/api/advisory.py`

- `GET /api/v1/advisory/zerodha-baskets`: Fetches existing Zerodha baskets for dropdown selection.
- `POST /api/v1/advisory/export-zerodha-basket`: Accepts basket name, optional basket ID, and items (`[{symbol, action, quantity}]`). Formats orders for NSE CNC MARKET trades and posts to Zerodha OMS `/orders/baskets`.

### 11.2 Safety & Workflow

1. **Non-Executing**: Uses Zerodha OMS Basket endpoints (`/orders/baskets`), never order placement endpoints (`/orders/regular`).
2. **Manual Review**: Returns a direct link to `https://kite.zerodha.com/orders/baskets` where users review items and trigger manual execution when ready.
3. **Demo Mode**: Gracefully simulates basket creation and returns mock basket IDs when running without live Zerodha sessions.
