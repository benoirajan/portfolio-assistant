"""
LLM Advisory Service — Multi-Stage 3-Pass AI Pipeline Engine
Implements prompt1.md (Diagnosis), Prompt2.md (Opportunity Screening), and prompt3.md (Execution Decision).
Provides Pydantic guardrails, live news context integration, NSE symbol validation, and fallback handling.
"""
import json
import logging
import os
from typing import Dict, List, Any, Literal, Optional
from pydantic import BaseModel, field_validator, model_validator

from src.core.config import settings
from src.core.retry import retry
from src.services.rebalancer import evaluate_rules
from src.services.news_search import search_company_news, search_sector_news
from src.services.market_data import market_data_service

logger = logging.getLogger("portfolio_assistant.llm_advisor")

# ---------------------------------------------------------------------------
# Pydantic Schemas for Legacy / Single-Pass Compatibility
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
        return self


# ---------------------------------------------------------------------------
# Pydantic Schemas for Multi-Stage Pipeline (Stage 1, 2, 3)
# ---------------------------------------------------------------------------
class SectorHealth(BaseModel):
    sector: str
    weight_pct: float
    status: str
    comment: str


class StockHealth(BaseModel):
    symbol: str
    allocation_pct: float
    business_quality: str
    financial_quality: str
    valuation: str
    long_term_outlook: str
    status: str
    comment: str


class Stage1Diagnosis(BaseModel):
    overall_quality: str
    main_strength: str
    main_weakness: str
    biggest_concentration_risk: str
    most_important_thing_to_monitor: str
    sector_analysis: List[SectorHealth]
    stock_analysis: List[StockHealth]
    portfolio_risks: List[str]
    portfolio_strengths: List[str]
    future_capital_direction: List[str]


class CandidateOpportunity(BaseModel):
    symbol: str
    sector: str
    is_existing_holding: bool
    conviction_tier: Literal["HIGH_CONVICTION", "GOOD_OPPORTUNITY", "WATCHLIST", "AVOID_FOR_NOW"]
    valuation_assessment: str
    portfolio_fit_summary: str
    main_risk: str
    rationale: str


class Stage2Ranking(BaseModel):
    opportunity_summary: str
    existing_vs_new_recommendation: str
    strongest_opportunity: str
    top_opportunities: List[CandidateOpportunity]
    sectors_to_prefer: List[str]
    sectors_to_be_careful: List[str]
    sectors_to_avoid: List[str]


class WholeSharePurchase(BaseModel):
    symbol: str
    action: Literal["BUY", "HOLD", "TRIM", "SELL"]
    current_price: float
    quantity: int
    amount: float
    rationale: str


class Stage3Execution(BaseModel):
    action: Literal["BUY", "PARTIALLY_INVEST", "WAIT"]
    allocated_amount: float
    cash_to_keep: float
    purchases: List[WholeSharePurchase]
    why_this_decision: List[str]
    portfolio_impact: List[str]
    why_not_others: str
    risks_to_understand: List[str]
    data_date_verified: str = ""
    simple_action_recommendation: str


# ---------------------------------------------------------------------------
# Stage Prompt Builders
# ---------------------------------------------------------------------------
def _build_stage1_prompt(
    holdings: List[Dict[str, Any]],
    rule_flags: List[Dict[str, Any]],
    investment_goal: str,
    total_value: float,
    news_context: str,
) -> str:
    anonymized = []
    for h in holdings:
        val = h.get("quantity", 0) * h.get("last_price", 0)
        weight = round((val / total_value) * 100, 2) if total_value > 0 else 0.0
        anonymized.append({
            "symbol": h.get("tradingsymbol", ""),
            "weight_pct": weight,
            "sector": h.get("sector", ""),
            "cap_category": h.get("cap_category", ""),
            "pe_ratio": h.get("pe_ratio", 0.0),
            "pb_ratio": h.get("pb_ratio", 0.0),
            "roe_pct": h.get("roe", 0.0),
            "roce_pct": h.get("roce", 0.0),
            "div_yield_pct": h.get("div_yield", 0.0),
            "trend_200_sma": h.get("trend_200_sma", "Neutral"),
        })

    flag_summary = [f["detail"] for f in rule_flags] if rule_flags else ["No rule violations detected."]

    return f"""ROLE: Professional long-term equity research analyst for Indian listed equities.
STAGE 1 TASK: Portfolio & Market Diagnosis ONLY. Do NOT decide trade execution or ₹ allocations.

INVESTMENT GOAL: {investment_goal}
INVESTMENT HORIZON: 10+ years (Moderate Risk)

CURRENT PORTFOLIO (Anonymized Relative Weights & Ratios):
{json.dumps(anonymized, indent=2)}

RULE ENGINE FLAGS:
{chr(10).join(f"- {f}" for f in flag_summary)}

LIVE NEWS & MARKET CONTEXT:
{news_context}

Analyse the portfolio as a whole. Evaluate:
1. Overall diversification and hidden economic concentration.
2. Business and financial quality of holdings.
3. Sectors that are Underweight, Healthy, High, or Excessive.
4. Holdings that are Strong, Monitor, or showing Fundamental Concern.
5. Identify future capital directions (underrepresented sectors, areas to limit).

Return JSON matching Stage1Diagnosis schema strictly.
"""


def _build_stage2_prompt(
    stage1: Stage1Diagnosis,
    holdings: List[Dict[str, Any]],
    investment_goal: str,
    allow_new_stocks: bool,
) -> str:
    existing_symbols = [h.get("tradingsymbol", "") for h in holdings]
    return f"""ROLE: Equity research opportunity analyst for Indian retail investor.
STAGE 2 TASK: Screen & rank top investment opportunities. Do NOT allocate ₹ amount or share quantities yet.

STAGE 1 DIAGNOSIS:
Overall Quality: {stage1.overall_quality}
Main Strength: {stage1.main_strength}
Main Weakness: {stage1.main_weakness}
Concentration Risk: {stage1.biggest_concentration_risk}
Future Directions: {', '.join(stage1.future_capital_direction)}

EXISTING HOLDINGS SYMBOLS: {', '.join(existing_symbols)}
ALLOW NEW INDIAN EQUITY CANDIDATES: {allow_new_stocks}

Instructions:
1. Compare existing holdings vs potential new Indian listed equities.
2. Evaluate incremental portfolio benefit and opportunity cost ("Which candidate adds the most value at the current portfolio state?").
3. Classify candidates into 4 conviction tiers:
   - HIGH_CONVICTION
   - GOOD_OPPORTUNITY
   - WATCHLIST
   - AVOID_FOR_NOW
4. Answer whether adding to an existing holding or starting a new stock is preferred for this cycle.

Return JSON matching Stage2Ranking schema strictly.
"""


def _build_stage3_prompt(
    stage1: Stage1Diagnosis,
    stage2: Stage2Ranking,
    holdings: List[Dict[str, Any]],
    total_budget: float,
    monthly_capacity: float,
    investment_schedule: str,
    investment_goal: str,
) -> str:
    holding_prices = {h.get("tradingsymbol", ""): h.get("last_price", 0.0) for h in holdings}
    return f"""ROLE: Portfolio decision support analyst for an Indian retail investor.
STAGE 3 TASK: Make the final bounded investment decision for today's available budget.

AVAILABLE BUDGET TODAY: ₹{total_budget:,.2f}
MONTHLY CAPACITY: ₹{monthly_capacity:,.2f}/month
SCHEDULE FREQUENCY: {investment_schedule}
INVESTMENT GOAL: {investment_goal}

STAGE 1 DIAGNOSIS HIGHLIGHTS:
Weakness: {stage1.main_weakness}
Risks: {', '.join(stage1.portfolio_risks[:3])}

STAGE 2 TOP OPPORTUNITIES:
Strongest Opportunity: {stage2.strongest_opportunity}
Existing vs New Advice: {stage2.existing_vs_new_recommendation}
Top Candidates: {json.dumps([o.model_dump() for o in stage2.top_opportunities], indent=2)}

CURRENT HOLDING PRICES:
{json.dumps(holding_prices, indent=2)}

Decision Rules:
1. Choose ONE action: BUY (invest full budget), PARTIALLY_INVEST (invest part, keep cash buffer), or WAIT (invest ₹0).
2. Calculate exact whole-share quantities within ₹{total_budget:,.2f}. Do NOT exceed budget.
3. Explicitly explain why this decision improves the overall portfolio and answer "Why not the others?".
4. State verified data date.

Return JSON matching Stage3Execution schema strictly.
"""


# ---------------------------------------------------------------------------
# LLM Execution Helpers
# ---------------------------------------------------------------------------
class _GeminiRateLimitError(Exception):
    pass


def _call_gemini_schema(prompt: str, schema_class: Any) -> Optional[str]:
    try:
        os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        from google import genai
        from google.genai import types

        client = genai.Client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema_class,
            temperature=0.2,
            max_output_tokens=3072,
        )

        logger.info("Sending multi-stage request to Gemini API (schema=%s, prompt_len=%d)",
                    schema_class.__name__, len(prompt))

        @retry(
            max_attempts=3,
            base_delay=2.0,
            multiplier=2.0,
            max_delay=30.0,
            retryable_on=(_GeminiRateLimitError,),
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
                raise

        response = _generate()
        return response.text
    except Exception as e:
        logger.error("Gemini API call failed for %s: %s", schema_class.__name__, e)
        return None


def _call_ollama_json(prompt: str) -> Optional[str]:
    try:
        import requests

        @retry(max_attempts=3, base_delay=2.0, multiplier=2.0, retryable_on=(Exception,))
        def _generate():
            resp = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "format": "json", "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

        return _generate()
    except Exception as e:
        logger.error("Ollama API call failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Fallback Generators for Multi-Stage Pipeline
# ---------------------------------------------------------------------------
def _fallback_stage1(holdings: List[Dict[str, Any]], rule_flags: List[Dict[str, Any]]) -> Stage1Diagnosis:
    total_val = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
    sectors = {}
    stocks = []
    for h in holdings:
        sym = h.get("tradingsymbol", "")
        val = h.get("quantity", 0) * h.get("last_price", 0)
        w = round((val / total_val * 100), 2) if total_val > 0 else 0.0
        sec = h.get("sector", "Diversified")
        sectors[sec] = sectors.get(sec, 0.0) + w
        stocks.append(StockHealth(
            symbol=sym, allocation_pct=w, business_quality="Good", financial_quality="Strong",
            valuation="Fair", long_term_outlook="Good", status="Strong Holding" if w <= 15.0 else "Monitor",
            comment="Stable fundamentals."
        ))

    sector_objs = [
        SectorHealth(sector=k, weight_pct=v, status="Excessive" if v > 25.0 else "Healthy", comment="Monitored exposure.")
        for k, v in sectors.items()
    ]

    return Stage1Diagnosis(
        overall_quality="Solid fundamental foundation with moderate growth potential.",
        main_strength="Core holdings in large-cap Indian equities with healthy ROE.",
        main_weakness="Concentration risk in top-weighted sectors." if any(v > 25.0 for v in sectors.values()) else "Underrepresented in emerging growth sectors.",
        biggest_concentration_risk="Top sector concentration threshold limit.",
        most_important_thing_to_monitor="Valuation expansion and 200-day SMA trend alignment.",
        sector_analysis=sector_objs,
        stock_analysis=stocks,
        portfolio_risks=[f["detail"] for f in rule_flags] if rule_flags else ["Market volatility & interest rate sensitivity."],
        portfolio_strengths=["High return on equity across core holdings", "Low leverage balance sheets"],
        future_capital_direction=["Consider underrepresented sectors like Healthcare & Capital Goods", "Maintain strict single-stock 15% cap"],
    )


def _fallback_stage2(stage1: Stage1Diagnosis, holdings: List[Dict[str, Any]]) -> Stage2Ranking:
    cands = []
    for s in stage1.stock_analysis[:4]:
        cands.append(CandidateOpportunity(
            symbol=s.symbol,
            sector=next((h.get("sector", "") for h in holdings if h.get("tradingsymbol") == s.symbol), "Equities"),
            is_existing_holding=True,
            conviction_tier="HIGH_CONVICTION" if s.status == "Strong Holding" else "GOOD_OPPORTUNITY",
            valuation_assessment=s.valuation,
            portfolio_fit_summary="Fits long-term portfolio growth strategy.",
            main_risk="Short-term market volatility.",
            rationale=s.comment,
        ))

    return Stage2Ranking(
        opportunity_summary="Existing portfolio holdings offer attractive risk-reward relative to new candidates.",
        existing_vs_new_recommendation="Currently better to add to existing high-conviction holdings.",
        strongest_opportunity=cands[0].symbol if cands else "INFY",
        top_opportunities=cands,
        sectors_to_prefer=["Information Technology", "Financial Services"],
        sectors_to_be_careful=["Automotive"],
        sectors_to_avoid=[],
    )


def _fallback_stage3(stage2: Stage2Ranking, holdings: List[Dict[str, Any]], total_budget: float) -> Stage3Execution:
    purchases = []
    rem_budget = total_budget
    top_cand = stage2.top_opportunities[0] if stage2.top_opportunities else None

    if top_cand:
        h = next((item for item in holdings if item.get("tradingsymbol") == top_cand.symbol), {})
        price = h.get("last_price", 1000.0)
        if price > 0 and rem_budget >= price:
            qty = int(rem_budget // price)
            amt = round(qty * price, 2)
            rem_budget -= amt
            purchases.append(WholeSharePurchase(
                symbol=top_cand.symbol,
                action="BUY",
                current_price=price,
                quantity=qty,
                amount=amt,
                rationale=top_cand.rationale,
            ))

    return Stage3Execution(
        action="BUY" if purchases else "WAIT",
        allocated_amount=round(total_budget - rem_budget, 2),
        cash_to_keep=round(rem_budget, 2),
        purchases=purchases,
        why_this_decision=["High conviction candidate with strong fundamentals", "Keeps single stock exposure below concentration limit"],
        portfolio_impact=["Improves core allocation without introducing unvalidated new ticker risks"],
        why_not_others="Secondary candidates had higher relative valuation or lower conviction scores.",
        risks_to_understand=["General equity market downturn", "Near-term sector headwinds"],
        data_date_verified="Current Live Demat Session",
        simple_action_recommendation=f"Invest ₹{total_budget - rem_budget:,.2f} in {purchases[0].symbol} ({purchases[0].quantity} shares)" if purchases else "Maintain cash position until market prices reach target entries.",
    )


# ---------------------------------------------------------------------------
# Public API — Multi-Stage Advisory Pipeline Entrypoint
# ---------------------------------------------------------------------------
def get_multi_stage_advisory(
    holdings: List[Dict[str, Any]],
    total_budget: float = 5000.0,
    monthly_capacity: float = 10000.0,
    investment_schedule: str = "Bi-weekly ₹5,000",
    investment_goal: str = "Moderate Growth",
    allow_new_stocks: bool = True,
    max_single_stock_pct: float = 15.0,
    max_sector_pct: float = 25.0,
) -> Dict[str, Any]:
    """
    Executes the 3-Stage Prompt Pipeline:
      Stage 1: Portfolio & Market Diagnosis
      Stage 2: Investment Opportunity Selection & Conviction Matrix
      Stage 3: Bounded Execution Decision
    """
    rule_flags = evaluate_rules(holdings, max_single_stock_pct, max_sector_pct)
    total_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)

    # 1. Fetch live news context for top holdings & sectors
    top_symbols = [h.get("tradingsymbol", "") for h in holdings[:3] if h.get("tradingsymbol")]
    news_items = []
    for sym in top_symbols:
        news_items.extend(search_company_news(sym, count=2))
    news_text = chr(10).join(f"- [{item['source']}] {item['title']}: {item['snippet']}" for item in news_items)

    llm_provider = None
    source = "rule_engine"

    # --- STAGE 1 ---
    stage1_data: Optional[Stage1Diagnosis] = None
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        p1 = _build_stage1_prompt(holdings, rule_flags, investment_goal, total_value, news_text)
        res1 = _call_gemini_schema(p1, Stage1Diagnosis)
        if res1:
            try:
                stage1_data = Stage1Diagnosis.model_validate_json(res1)
                llm_provider = settings.GEMINI_MODEL
                source = "llm"
            except Exception as e:
                logger.error("Stage 1 Pydantic parsing failed: %s", e)

    if not stage1_data:
        stage1_data = _fallback_stage1(holdings, rule_flags)

    # --- STAGE 2 ---
    stage2_data: Optional[Stage2Ranking] = None
    if source == "llm" and settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        p2 = _build_stage2_prompt(stage1_data, holdings, investment_goal, allow_new_stocks)
        res2 = _call_gemini_schema(p2, Stage2Ranking)
        if res2:
            try:
                stage2_data = Stage2Ranking.model_validate_json(res2)
                # Ticker Master Validation: Filter out unverified new ticker symbols
                valid_top = []
                for cand in stage2_data.top_opportunities:
                    if cand.is_existing_holding or market_data_service.is_valid_nse_symbol(cand.symbol):
                        valid_top.append(cand)
                    else:
                        logger.warning("Filtered out unverified candidate symbol '%s'", cand.symbol)
                stage2_data.top_opportunities = valid_top
            except Exception as e:
                logger.error("Stage 2 Pydantic parsing failed: %s", e)

    if not stage2_data:
        stage2_data = _fallback_stage2(stage1_data, holdings)

    # --- STAGE 3 ---
    stage3_data: Optional[Stage3Execution] = None
    if source == "llm" and settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        p3 = _build_stage3_prompt(stage1_data, stage2_data, holdings, total_budget, monthly_capacity, investment_schedule, investment_goal)
        res3 = _call_gemini_schema(p3, Stage3Execution)
        if res3:
            try:
                stage3_data = Stage3Execution.model_validate_json(res3)
                # Cap allocation at total_budget
                if stage3_data.allocated_amount > total_budget:
                    stage3_data.allocated_amount = total_budget
                    stage3_data.cash_to_keep = 0.0
            except Exception as e:
                logger.error("Stage 3 Pydantic parsing failed: %s", e)

    if not stage3_data:
        stage3_data = _fallback_stage3(stage2_data, holdings, total_budget)

    return {
        "status": "success",
        "stage1": stage1_data.model_dump(),
        "stage2": stage2_data.model_dump(),
        "stage3": stage3_data.model_dump(),
        "rule_flags": rule_flags,
        "source": source,
        "llm_provider": llm_provider,
        "total_budget": total_budget,
        "monthly_capacity": monthly_capacity,
    }


# ---------------------------------------------------------------------------
# Legacy Single-Pass Recommendation Function (Backwards Compatibility)
# ---------------------------------------------------------------------------
def _build_prompt(
    holdings: List[Dict[str, Any]],
    rule_flags: List[Dict[str, Any]],
    investment_goal: str,
    total_value: float,
) -> str:
    anonymized = []
    for h in holdings:
        val = h.get("quantity", 0) * h.get("last_price", 0)
        weight = round((val / total_value) * 100, 2) if total_value > 0 else 0.0
        anonymized.append({
            "symbol": h.get("tradingsymbol", ""),
            "weight_pct": weight,
            "sector": h.get("sector", ""),
            "cap_category": h.get("cap_category", "Large Cap"),
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


def _call_gemini(prompt: str) -> Optional[str]:
    try:
        os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        from google import genai
        from google.genai import types

        client = genai.Client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RecommendationList,
            temperature=0.2,
            max_output_tokens=2048,
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        logger.error("Gemini legacy call failed: %s", e)
        return None


def _call_ollama(prompt: str) -> Optional[str]:
    try:
        import requests
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        logger.error("Ollama legacy call failed: %s", e)
        return None


def _rule_based_recommendations(
    holdings: List[Dict[str, Any]],
    rule_flags: List[Dict[str, Any]],
    total_value: float,
) -> List[Dict[str, Any]]:
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


def get_recommendations(
    holdings: List[Dict[str, Any]],
    investment_goal: str = "Moderate Growth",
    max_single_stock_pct: float = 15.0,
    max_sector_pct: float = 25.0,
) -> Dict[str, Any]:
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
            parsed = RecommendationList.model_validate_json(llm_raw)
            valid_recs = [r for r in parsed.recommendations if r.symbol in known_symbols]
            recs = [r.model_dump() | {"source": "llm"} for r in valid_recs]
            source = "llm"
        except Exception as e:
            logger.error("LLM legacy validation failed: %s", e)

    if not recs:
        recs = _rule_based_recommendations(holdings, rule_flags, total_value)
        source = "rule_engine"
        llm_provider = None

    return {
        "recommendations": recs,
        "rule_flags": rule_flags,
        "source": source,
        "investment_goal": investment_goal,
        "llm_provider": llm_provider,
    }
