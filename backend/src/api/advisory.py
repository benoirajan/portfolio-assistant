import hashlib
import json
import logging
import math
from fastapi import APIRouter, Header, Query, HTTPException
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.services.llm_advisor import get_recommendations, Recommendation
from src.core.config import settings
from src.core import cache

logger = logging.getLogger("portfolio_assistant.api.advisory")
router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


def _advisory_cache_key(token: str, goal: str, stock_pct: float, sector_pct: float, holdings_hash: str) -> str:
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    params = f"{goal}:{stock_pct}:{sector_pct}:{holdings_hash}"
    params_hash = hashlib.sha256(params.encode()).hexdigest()[:16]
    return f"advisory:{token_hash}:{params_hash}"


@router.get("/recommendations")
def recommendations(
    investment_goal: str = Query("Moderate Growth", description="User's investment objective"),
    max_single_stock_pct: float = Query(15.0, ge=5.0, le=50.0),
    max_sector_pct: float = Query(25.0, ge=10.0, le=60.0),
    x_enctoken: Optional[str] = Header(None),
):
    logger.info("Advisory request — goal='%s' stock_cap=%.0f%% sector_cap=%.0f%%",
                investment_goal, max_single_stock_pct, max_sector_pct)
    effective_token = x_enctoken or settings.ZERODHA_ENCTOKEN or ""
    if x_enctoken:
        zerodha_service.set_enctoken(x_enctoken)

    raw_holdings, _, _ = zerodha_service.get_holdings_with_status()
    enriched = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)
    logger.debug("Enriched %d holdings for advisory", len(enriched))

    # Cache key includes a hash of holdings so stale recommendations auto-invalidate on portfolio change
    holdings_hash = hashlib.sha256(json.dumps(enriched, sort_keys=True, default=str).encode()).hexdigest()[:16]
    cache_key = _advisory_cache_key(effective_token, investment_goal, max_single_stock_pct, max_sector_pct, holdings_hash)

    cached = cache.get(cache_key)
    if cached:
        logger.info("Advisory served from cache — key=%s", cache_key)
        return cached

    result = get_recommendations(
        enriched,
        investment_goal=investment_goal,
        max_single_stock_pct=max_single_stock_pct,
        max_sector_pct=max_sector_pct,
    )
    logger.info("Advisory complete — source=%s rule_flags=%d recommendations=%d",
                result.get("source"), len(result.get("rule_flags", [])), len(result.get("recommendations", [])))

    response = {"status": "success", **result}
    # Only cache LLM responses — rule-engine results are cheap to recompute
    if result.get("source") == "llm":
        cache.set(cache_key, response, ttl=settings.ADVISORY_CACHE_TTL)
    return response


# ---------------------------------------------------------------------------
# Basket models
# ---------------------------------------------------------------------------
class BasketRequest(BaseModel):
    recommendations: List[Recommendation]
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


@router.post("/basket", response_model=BasketResponse)
def create_basket(
    body: BasketRequest,
    x_enctoken: Optional[str] = Header(None),
):
    logger.info("Basket request — recommendations=%d max_budget=%.2f", len(body.recommendations), body.max_budget)
    if x_enctoken:
        zerodha_service.set_enctoken(x_enctoken)

    raw_holdings, _, _ = zerodha_service.get_holdings_with_status()
    price_map = {
        h["tradingsymbol"]: {
            "last_price": h.get("last_price", 0.0),
            "current_value": h.get("quantity", 0) * h.get("last_price", 0.0),
        }
        for h in raw_holdings
    }
    total_value = sum(v["current_value"] for v in price_map.values())

    # Separate BUY items (budget-capped) from SELL/TRIM items
    buy_recs = sorted(
        [r for r in body.recommendations if r.action == "BUY"],
        key=lambda r: r.confidence_score,
        reverse=True,
    )
    sell_recs = [r for r in body.recommendations if r.action in ("SELL", "TRIM")]

    basket: List[BasketItem] = []

    # --- BUY items with budget cap ---
    remaining_budget = body.max_budget
    for rec in buy_recs:
        info = price_map.get(rec.symbol)
        if not info or info["last_price"] <= 0 or remaining_budget <= 0:
            continue
        target_value = total_value * rec.target_allocation_pct / 100
        delta = target_value - info["current_value"]
        if delta <= 0:
            continue
        spend = min(delta, remaining_budget)
        qty = math.floor(spend / info["last_price"])
        if qty <= 0:
            continue
        est = round(qty * info["last_price"], 2)
        remaining_budget -= est
        basket.append(BasketItem(
            symbol=rec.symbol,
            action="BUY",
            quantity=qty,
            estimated_value=est,
            reason=rec.rationale,
        ))

    # --- SELL / TRIM items (no budget cap) ---
    for rec in sell_recs:
        info = price_map.get(rec.symbol)
        if not info or info["last_price"] <= 0:
            continue
        target_value = total_value * rec.target_allocation_pct / 100
        delta = info["current_value"] - target_value
        if delta <= 0:
            continue
        qty = math.floor(delta / info["last_price"])
        if qty <= 0:
            continue
        basket.append(BasketItem(
            symbol=rec.symbol,
            action=rec.action,  # type: ignore[arg-type]
            quantity=qty,
            estimated_value=round(qty * info["last_price"], 2),
            reason=rec.rationale,
        ))

    total_buy = round(sum(i.estimated_value for i in basket if i.action == "BUY"), 2)
    total_sell = round(sum(i.estimated_value for i in basket if i.action in ("SELL", "TRIM")), 2)
    utilised_pct = round(total_buy / body.max_budget * 100, 1) if body.max_budget > 0 else 0.0

    logger.info("Basket created — items=%d buy=%.2f sell=%.2f budget_used=%.1f%%",
                len(basket), total_buy, total_sell, utilised_pct)
    return BasketResponse(
        status="success",
        basket=basket,
        total_buy_value=total_buy,
        total_sell_value=total_sell,
        budget_utilised_pct=utilised_pct,
    )


# ---------------------------------------------------------------------------
# Zerodha Basket Export models & endpoints
# ---------------------------------------------------------------------------
class ExportZerodhaBasketItem(BaseModel):
    symbol: str
    action: str
    quantity: int


class ExportZerodhaBasketRequest(BaseModel):
    basket_name: str
    basket_id: Optional[str] = None
    items: List[ExportZerodhaBasketItem]


class ExportZerodhaBasketResponse(BaseModel):
    status: str
    basket_id: str
    basket_name: str
    item_count: int
    kite_url: str
    message: str


@router.get("/zerodha-baskets")
def list_zerodha_baskets(x_enctoken: Optional[str] = Header(None)):
    if x_enctoken:
        zerodha_service.set_enctoken(x_enctoken)
    baskets, err = zerodha_service.get_baskets()
    return {"status": "success", "baskets": baskets, "error": err}


@router.post("/export-zerodha-basket", response_model=ExportZerodhaBasketResponse)
def export_zerodha_basket(
    body: ExportZerodhaBasketRequest,
    x_enctoken: Optional[str] = Header(None),
):
    if x_enctoken:
        zerodha_service.set_enctoken(x_enctoken)

    items_dict = [item.model_dump() for item in body.items]
    res, err = zerodha_service.export_to_zerodha_basket(
        basket_name=body.basket_name,
        items=items_dict,
        basket_id=body.basket_id,
    )
    if not res:
        raise HTTPException(status_code=400, detail=err or "Failed to export basket to Zerodha")

    return ExportZerodhaBasketResponse(
        status="success",
        basket_id=res["basket_id"],
        basket_name=res["basket_name"],
        item_count=res["item_count"],
        kite_url=res["kite_url"],
        message=f"Basket '{res['basket_name']}' successfully updated in Zerodha with {res['item_count']} items.",
    )
