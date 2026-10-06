---
name: gemini-ai-advisory-pipeline
description: Workflow and guidelines for managing the 3-Stage Google Gemini AI Advisory Pipeline (Prompts 1-3), Rule Engine, and fallback models.
---

# Gemini AI Advisory Pipeline Skill

This skill governs the integration of Google Gemini (`google-genai` SDK) and the execution of the 3-Stage AI Advisory Pipeline for generating personalized stock recommendations.

---

## 1. Rule Engine Pre-Screening (`rebalancer.py`)

Before calling the LLM, holdings are evaluated by a deterministic rule engine to flag risk violations:

| Rule ID | Trigger Condition | Default Threshold | Severity |
| :--- | :--- | :--- | :--- |
| `OVER_CONCENTRATION` | Single stock weight > `max_single_stock_pct` | `15.0%` | `HIGH` |
| `UNDERPERFORMANCE` | `last_price < sma_200` **AND** `roe <= 0` | — | `MEDIUM` |
| `SECTOR_OVERWEIGHT` | Aggregate sector weight > `max_sector_pct` | `25.0%` | `MEDIUM` |

*Rule violations are injected into the LLM prompt context to force the model to address portfolio imbalances.*

---

## 2. 3-Stage Prompting Pipeline Mechanics

The AI Advisory Engine follows a structured 3-stage sequence:

### Stage 1: Portfolio & Risk Analysis ([prompt1.md](file:///home/benoi/Projects/portfolio_assistant/prompt1.md))
* **Objective:** Establish investor profile (10+ year horizon, moderate risk, 20–30% drawdown tolerance, ₹10,000 monthly investment capacity).
* **Output:** Deep portfolio health summary, sector exposure breakdown, and risk analysis.

### Stage 2: Investment Opportunity Screening ([Prompt2.md](file:///home/benoi/Projects/portfolio_assistant/Prompt2.md))
* **Objective:** Screen existing holdings and new NSE-listed companies to identify top allocation opportunities for a **₹5,000 investment tranche**.
* **Output:** Ranked list of investment options evaluating valuation, business quality, and concentration risk.

### Stage 3: Final Actionable Trade Decision ([prompt3.md](file:///home/benoi/Projects/portfolio_assistant/prompt3.md))
* **Objective:** Make the final, unambiguous recommendation for the ₹5,000 allocation.
* **Output:** Action plan specifying exact stock, quantity to buy/trim, entry rationale, and portfolio impact.

---

## 3. Gemini SDK (`google-genai`) Integration Standards

* **SDK Version:** Always use the official `google-genai` SDK.
* **API Key Management:** Push `GEMINI_API_KEY` into `os.environ` so `genai.Client()` auto-resolves authentication.
* **Structured Output Validation:** Parse LLM output into Pydantic models (`AdvisoryResponse`) to ensure schema safety before returning to the frontend.
* **Local Fallback:** If `LLM_PROVIDER="ollama"`, route prompt context to local Ollama instance (`http://localhost:11434`, model `mistral`).

---

## 4. References & Documentation Links

* [Phase 3 AI Advisory Engine LLD](file:///home/benoi/Projects/portfolio_assistant/docs/lld/03_phase3_ai_advisory.md)
* [Gemini SDK Integration Reference](file:///home/benoi/Projects/portfolio_assistant/docs/api-references/Gemini_api_doc.md)
* [Prompt 1 Spec](file:///home/benoi/Projects/portfolio_assistant/prompt1.md) · [Prompt 2 Spec](file:///home/benoi/Projects/portfolio_assistant/Prompt2.md) · [Prompt 3 Spec](file:///home/benoi/Projects/portfolio_assistant/prompt3.md)
