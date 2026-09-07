import logging
from fastapi import APIRouter, Header, Query
from typing import Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.services.llm_advisor import get_recommendations

logger = logging.getLogger("portfolio_assistant.api.advisory")
router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


@router.get("/recommendations")
def recommendations(
    investment_goal: str = Query("Moderate Growth", description="User's investment objective"),
    max_single_stock_pct: float = Query(15.0, ge=5.0, le=50.0),
    max_sector_pct: float = Query(25.0, ge=10.0, le=60.0),
    x_enctoken: Optional[str] = Header(None),
):
    logger.info("Advisory request — goal='%s' stock_cap=%.0f%% sector_cap=%.0f%%",
                investment_goal, max_single_stock_pct, max_sector_pct)
    if x_enctoken:
        zerodha_service.set_enctoken(x_enctoken)

    raw_holdings, _, _ = zerodha_service.get_holdings_with_status()
    enriched = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)
    logger.debug("Enriched %d holdings for advisory", len(enriched))

    result = get_recommendations(
        enriched,
        investment_goal=investment_goal,
        max_single_stock_pct=max_single_stock_pct,
        max_sector_pct=max_sector_pct,
    )
    logger.info("Advisory complete — source=%s rule_flags=%d recommendations=%d",
                result.get("source"), len(result.get("rule_flags", [])), len(result.get("recommendations", [])))
    return {"status": "success", **result}
