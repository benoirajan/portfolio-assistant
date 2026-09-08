"""
LLM Advisory Service — Phase 3
Sends anonymized portfolio context to Gemini (or Ollama) and validates
the response through Pydantic guardrails before returning recommendations.
Falls back to rule-based recommendations on any LLM/validation failure.
"""
import json
import logging
from typing import Dict, List, Any, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator
from src.core.config import settings
from src.core.retry import retry
from src.services.rebalancer import evaluate_rules

logger = logging.getLogger("portfolio_assistant.llm_advisor")

# ---------------------------------------------------------------------------
# Pydantic response schema (guardrails)
# ---------------------------------------------------------------------------
VALID_ACTIONS = {"BUY", "SELL", "HOLD", "TRIM"}


class Recommendation(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD", "TRIM"]
    target_allocation_pct: float
    confidence_score: float
    rationale: str

    @field_validator("confidence_score")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence_score {v} out of [0.0, 1.0]")
        return round(v, 2)

    @field_validator("target_allocation_pct")
    @classmethod
    def allocation_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("target_allocation_pct must be >= 0")
        return round(v, 2)


class RecommendationList(BaseModel):
    recommendations: List[Recommendation]
    investment_goal: str = ""

    @model_validator(mode="after")
    def validate_guardrails(self) -> "RecommendationList":
        total_alloc = sum(r.target_allocation_pct for r in self.recommendations)
        if total_alloc > 100.0:
            raise ValueError(f"Sum of target_allocation_pct is {total_alloc:.1f}% — exceeds 100%")
        for r in self.recommendations:
            if r.target_allocation_pct > 20.0 and r.action == "BUY":
                # Small-cap cap guard — we can't check cap_category here, so
                # this is enforced downstream in the advisor after symbol lookup
                pass
        return self


# ---------------------------------------------------------------------------
# Prompt builder — data minimization enforced here
# ---------------------------------------------------------------------------
def _build_prompt(
    holdings: List[Dict[str, Any]],
    rule_flags: List[Dict[str, Any]],
    investment_goal: str,
    total_value: float,
) -> str:
    """Strips all absolute ₹ values; only relative weights and ratios are sent."""
    anonymized = []
    for h in holdings:
        val = h.get("quantity", 0) * h.get("last_price", 0)
        weight = round((val / total_value) * 100, 2) if total_value > 0 else 0.0
        cap = h.get("cap_category", "Large Cap")
        anonymized.append({
            "symbol": h.get("tradingsymbol", ""),
            "weight_pct": weight,
            "sector": h.get("sector", ""),
            "cap_category": cap,
            "pe_ratio": h.get("pe_ratio", 0.0),
            "pb_ratio": h.get("pb_ratio", 0.0),
            "roe_pct": h.get("roe", 0.0),
            "div_yield_pct": h.get("div_yield", 0.0),
            "trend_200_sma": h.get("trend_200_sma", "Neutral"),
        })

    flag_summary = [f["detail"] for f in rule_flags] if rule_flags else ["No rule violations detected."]

    return f"""You are a SEBI-registered portfolio advisor AI for an Indian retail investor.

INVESTMENT GOAL: {investment_goal}

PORTFOLIO (anonymized — no absolute ₹ values):
{json.dumps(anonymized, indent=2)}

RULE ENGINE FLAGS:
{chr(10).join(f"- {f}" for f in flag_summary)}

TASK: Return a JSON object with key "recommendations" — a list where each item has:
  - symbol: string (must be from the portfolio above)
  - action: one of BUY, SELL, HOLD, TRIM
  - target_allocation_pct: float (desired % of total portfolio, all must sum <= 100)
  - confidence_score: float between 0.0 and 1.0
  - rationale: 1-2 sentence plain-English explanation

Rules you MUST follow:
1. Only use symbols present in the portfolio above — no new tickers.
2. Sum of all target_allocation_pct must not exceed 100.
3. No single Small Cap / Mid Cap stock should exceed 20% target allocation.
4. Respond ONLY with valid JSON — no markdown, no extra text.
"""


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------
class _GeminiRateLimitError(Exception):
    """Raised on HTTP 429 — signals retry with backoff is appropriate."""


def _call_gemini(prompt: str) -> Optional[str]:
    try:
        import os
        os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        client = genai.Client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RecommendationList,
            temperature=0.2,
            max_output_tokens=2048,
        )

        logger.info("Sending request to Gemini API (model=%s, prompt_len=%d)", settings.GEMINI_MODEL, len(prompt))
        logger.debug("Gemini Prompt Payload:\n%s", prompt)

        @retry(
            max_attempts=3,
            base_delay=2.0,
            multiplier=2.0,
            max_delay=30.0,
            retryable_on=(_GeminiRateLimitError,),  # only retry on 429
        )
        def _generate():
            try:
                return client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=config,
                )
            except Exception as exc:
                msg = str(exc)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    raise _GeminiRateLimitError(msg) from exc
                raise  # 404, 400, auth errors — fail fast, no retry

        response = _generate()
        raw_text = response.text
        logger.info("Received response from Gemini API (raw_len=%d)", len(raw_text) if raw_text else 0)
        logger.debug("Gemini Raw Response:\n%s", raw_text)
        return raw_text
    except Exception as e:
        logger.error("Gemini API call failed after retries: %s", e)
        return None


def _call_ollama(prompt: str) -> Optional[str]:
    try:
        import requests

        logger.info("Sending request to Ollama API (model=%s, prompt_len=%d)", settings.OLLAMA_MODEL, len(prompt))
        logger.debug("Ollama Prompt Payload:\n%s", prompt)

        @retry(max_attempts=3, base_delay=2.0, multiplier=2.0,
               retryable_on=(Exception,))
        def _generate():
            resp = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

        raw_res = _generate()
        logger.info("Received response from Ollama API (raw_len=%d)", len(raw_res) if raw_res else 0)
        logger.debug("Ollama Raw Response:\n%s", raw_res)
        return raw_res
    except Exception as e:
        logger.error("Ollama API call failed after retries: %s", e)
        return None


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------
def _rule_based_recommendations(
    holdings: List[Dict[str, Any]],
    rule_flags: List[Dict[str, Any]],
    total_value: float,
) -> List[Dict[str, Any]]:
    """Generates simple HOLD/TRIM/SELL recommendations from rule flags alone."""
    flagged_symbols = {f["symbol"] for f in rule_flags if f.get("symbol")}
    recs = []
    for h in holdings:
        sym = h.get("tradingsymbol", "")
        val = h.get("quantity", 0) * h.get("last_price", 0)
        weight = round((val / total_value) * 100, 2) if total_value > 0 else 0.0
        matching_flags = [f for f in rule_flags if f.get("symbol") == sym]

        if any(f["rule"] == "OVER_CONCENTRATION" for f in matching_flags):
            action, rationale = "TRIM", "Position exceeds concentration limit. Reduce to rebalance."
        elif any(f["rule"] == "UNDERPERFORMANCE" for f in matching_flags):
            action, rationale = "SELL", "Trading below 200-day SMA with weak fundamentals."
        else:
            action, rationale = "HOLD", "No rule violations. Maintain current position."

        recs.append({
            "symbol": sym,
            "action": action,
            "target_allocation_pct": round(min(weight, 15.0) if action == "TRIM" else weight, 2),
            "confidence_score": 0.75 if sym in flagged_symbols else 0.60,
            "rationale": rationale,
            "source": "rule_engine",
        })
    return recs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_recommendations(
    holdings: List[Dict[str, Any]],
    investment_goal: str = "Moderate Growth",
    max_single_stock_pct: float = 15.0,
    max_sector_pct: float = 25.0,
) -> Dict[str, Any]:
    """
    Returns:
      {
        recommendations: [...],
        rule_flags: [...],
        source: "llm" | "rule_engine",
        investment_goal: str,
        llm_provider: str | None,
      }
    """
    rule_flags = evaluate_rules(holdings, max_single_stock_pct, max_sector_pct)
    total_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
    known_symbols = {h.get("tradingsymbol", "") for h in holdings}

    llm_raw: Optional[str] = None
    source = "rule_engine"
    llm_provider = None

    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        prompt = _build_prompt(holdings, rule_flags, investment_goal, total_value)
        llm_raw = _call_gemini(prompt)
        llm_provider = settings.GEMINI_MODEL
    elif settings.LLM_PROVIDER == "ollama":
        prompt = _build_prompt(holdings, rule_flags, investment_goal, total_value)
        llm_raw = _call_ollama(prompt)
        llm_provider = f"ollama/{settings.OLLAMA_MODEL}"

    recs: List[Dict[str, Any]] = []

    if llm_raw:
        try:
            logger.info("Parsing LLM response — raw_len=%d", len(llm_raw))
            parsed = RecommendationList.model_validate_json(llm_raw)

            # Guardrail: reject hallucinated symbols
            valid_recs = [r for r in parsed.recommendations if r.symbol in known_symbols]
            if len(valid_recs) < len(parsed.recommendations):
                logger.warning("LLM hallucinated %d unknown symbols — filtered out.", len(parsed.recommendations) - len(valid_recs))

            # Guardrail: small-cap allocation cap
            for r in valid_recs:
                h_match = next((h for h in holdings if h.get("tradingsymbol") == r.symbol), {})
                if h_match.get("cap_category", "") in ("Small Cap", "Mid Cap") and r.target_allocation_pct > 20.0:
                    logger.warning("Small/mid-cap %s allocation %.1f%% capped at 20%%.", r.symbol, r.target_allocation_pct)
                    r.target_allocation_pct = 20.0

            recs = [r.model_dump() | {"source": "llm"} for r in valid_recs]
            source = "llm"
            logger.info("LLM recommendations validated successfully — count=%d", len(recs))
        except Exception as e:
            logger.error("LLM response validation failed: %s. Falling back to rule engine.", e)

    if not recs:
        recs = _rule_based_recommendations(holdings, rule_flags, total_value)
        source = "rule_engine"
        llm_provider = None
        logger.info("Generated rule-based recommendations fallback — count=%d", len(recs))

    return {
        "recommendations": recs,
        "rule_flags": rule_flags,
        "source": source,
        "investment_goal": investment_goal,
        "llm_provider": llm_provider,
    }
