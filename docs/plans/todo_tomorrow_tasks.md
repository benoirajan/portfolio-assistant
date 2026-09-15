# Action Items / TODO for Next Session

---

## 📋 Task 1: Comprehensive DEBUG Level Prompt Payload Logging

* **Objective:** Ensure all multi-stage LLM prompt payloads are logged at `DEBUG` level in `backend/src/services/llm_advisor.py`.
* **Details:**
  * Log the complete rendered prompt string before invoking Gemini for Stage 1 (Diagnosis), Stage 2 (Conviction Screening), and Stage 3 (Bounded Execution).
  * Example:
    ```python
    logger.debug("Gemini Stage 1 Prompt Payload:\n%s", p1)
    logger.debug("Gemini Stage 2 Prompt Payload:\n%s", p2)
    logger.debug("Gemini Stage 3 Prompt Payload:\n%s", p3)
    ```
  * Verify that running with `LOG_LEVEL=DEBUG` captures full prompts in `logs/app.log`.

---

## 📋 Task 2: Audit `google-genai` SDK Structured Output & Function Calling Syntax

* **Objective:** Audit the `google-genai` Python SDK integration (`from google import genai`, `from google.genai import types`) in `llm_advisor.py` to ensure alignment with the latest SDK practices.
* **Details:**
  * Verify `GenerateContentConfig(response_mime_type="application/json", response_schema=PydanticModel)` usage against official Google AI Studio recommendations.
  * Check if native function calling (`tools=[func]`) or tool declarations should be leveraged for web-search / symbol lookups.
  * Ensure compatibility with upcoming `google-genai` SDK version updates.
