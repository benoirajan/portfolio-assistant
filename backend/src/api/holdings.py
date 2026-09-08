import hashlib
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import List, Dict, Any, Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.core.config import settings
from src.core import cache

logger = logging.getLogger("portfolio_assistant.api.holdings")
router = APIRouter(prefix="/api/v1", tags=["Portfolio"])


def _holdings_cache_key(token: str) -> str:
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    return f"holdings:{token_hash}"


@router.get("/holdings")
def get_holdings(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns long-term Demat holdings enriched with P&L, fundamentals, and metrics."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        cache_key = _holdings_cache_key(effective_token or "demo")
        cached = cache.get(cache_key)
        if cached:
            logger.info("Holdings served from cache — key=%s", cache_key)
            return cached

        raw_holdings, is_live, error_msg = zerodha_service.get_holdings_with_status()
        enriched_holdings = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)

        total_investment = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in enriched_holdings)
        current_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in enriched_holdings)
        total_pnl = current_value - total_investment
        total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0

        logger.info("Holdings fetched — count=%d is_live=%s pnl=%.2f (%.2f%%)",
                    len(enriched_holdings), is_live, total_pnl, total_pnl_pct)
        if error_msg:
            logger.warning("Holdings fetch warning: %s", error_msg)

        response = {
            "status": "success",
            "is_live": is_live,
            "error_message": error_msg,
            "summary": {
                "total_holdings_count": len(enriched_holdings),
                "total_investment": round(total_investment, 2),
                "current_value": round(current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percentage": round(total_pnl_pct, 2)
            },
            "holdings": enriched_holdings
        }
        cache.set(cache_key, response, ttl=settings.HOLDINGS_CACHE_TTL)
        return response
    except Exception as e:
        logger.error("Holdings fetch error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
def get_positions(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns day and net positions."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)
        positions = zerodha_service.get_positions()
        logger.info("Positions fetched — count=%d", len(positions) if isinstance(positions, list) else 1)
        return {"status": "success", "positions": positions}
    except Exception as e:
        logger.error("Positions fetch error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/margins")
def get_margins(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns cash balance and margin utilization."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)
        margins = zerodha_service.get_margins()
        logger.info("Margins fetched successfully")
        return {"status": "success", "margins": margins}
    except Exception as e:
        logger.error("Margins fetch error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/invalidate", tags=["Cache"])
def invalidate_cache(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Busts holdings and advisory cache for the current user. Call from the frontend Refresh button."""
    effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
    token_key = effective_token or "demo"
    deleted = cache.delete_pattern(f"holdings:{hashlib.sha256(token_key.encode()).hexdigest()[:16]}")
    deleted += cache.delete_pattern(f"advisory:{hashlib.sha256(token_key.encode()).hexdigest()[:16]}:*")
    logger.info("Cache invalidated — %d keys deleted", deleted)
    return {"status": "success", "keys_deleted": deleted}
