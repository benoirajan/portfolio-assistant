import hashlib
import json
import logging
from fastapi import APIRouter, Header, Query
from typing import Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.services.llm_advisor import get_recommendations
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
