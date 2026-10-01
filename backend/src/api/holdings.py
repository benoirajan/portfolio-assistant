import hashlib
import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import List, Dict, Any, Optional

from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.core.config import settings
from src.core import cache
from src.core.security import get_current_user, get_user_enctoken
from src.models.user import User
from src.services.portfolio_repository import save_portfolio, load_portfolio

logger = logging.getLogger("portfolio_assistant.api.holdings")
router = APIRouter(prefix="/api/v1", tags=["Portfolio"])


def _holdings_cache_key(user_id: str, token_key: str) -> str:
    token_hash = hashlib.sha256(token_key.encode()).hexdigest()[:16]
    return f"holdings:{user_id}:{token_hash}"


@router.get("/holdings")
def get_holdings(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns long-term Demat holdings enriched with P&L, fundamentals, and metrics for authenticated user."""
    try:
        # Resolve effective token: Header > Stored DB Encrypted Token > Settings
        effective_token = x_enctoken
        if not effective_token:
            effective_token = get_user_enctoken(current_user.id)
        if not effective_token and settings.ZERODHA_ENCTOKEN:
            effective_token = settings.ZERODHA_ENCTOKEN

        token_identifier = effective_token or f"user_{current_user.id}"
        cache_key = _holdings_cache_key(current_user.id, token_identifier)
        cached = cache.get(cache_key)
        if cached:
            logger.info("Holdings served from cache — key=%s (user_id=%s)", cache_key, current_user.id)
            return cached

        if effective_token:
            zerodha_service.set_enctoken(effective_token)
            raw_holdings, is_live, error_msg = zerodha_service.get_holdings_with_status()
        else:
            raw_holdings, is_live, error_msg = [], False, "No broker credentials connected. Please connect your Zerodha account in Settings."

        # If live fetch is unavailable, attempt to re-hydrate user's saved portfolio from database
        if not is_live:
            persisted = load_portfolio(token_identifier, user_id=current_user.id)
            if persisted:
                logger.info("Holdings re-hydrated from database storage for user %s", current_user.id)
                cache.set(cache_key, persisted, ttl=settings.HOLDINGS_CACHE_TTL)
                return persisted

            if not effective_token:
                return {
                    "status": "warning",
                    "is_live": False,
                    "error_message": error_msg,
                    "summary": {
                        "total_holdings_count": 0,
                        "total_investment": 0.0,
                        "current_value": 0.0,
                        "total_pnl": 0.0,
                        "total_pnl_percentage": 0.0,
                    },
                    "holdings": [],
                }

        enriched_holdings = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)

        total_investment = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in enriched_holdings)
        current_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in enriched_holdings)
        total_pnl = current_value - total_investment
        total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0

        logger.info("Holdings fetched for user %s — count=%d is_live=%s pnl=%.2f (%.2f%%)",
                    current_user.id, len(enriched_holdings), is_live, total_pnl, total_pnl_pct)
        if error_msg:
            logger.warning("Holdings fetch warning for user %s: %s", current_user.id, error_msg)

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
        
        # Persist to database linked to user_id
        if is_live and enriched_holdings:
            save_portfolio(token_identifier, response, user_id=current_user.id)

        cache.set(cache_key, response, ttl=settings.HOLDINGS_CACHE_TTL)
        return response
    except Exception as e:
        logger.error("Holdings fetch error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
def get_positions(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns day and net positions for authenticated user."""
    try:
        effective_token = x_enctoken or get_user_enctoken(current_user.id) or settings.ZERODHA_ENCTOKEN
        if not effective_token:
            return {"status": "warning", "positions": {"net": [], "day": []}, "error_message": "No broker connected"}

        zerodha_service.set_enctoken(effective_token)
        positions = zerodha_service.get_positions()
        logger.info("Positions fetched for user %s — count=%d", current_user.id, len(positions) if isinstance(positions, list) else 1)
        return {"status": "success", "positions": positions}
    except Exception as e:
        logger.error("Positions fetch error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins")
def get_margins(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns cash balance and margin utilization for authenticated user."""
    try:
        effective_token = x_enctoken or get_user_enctoken(current_user.id) or settings.ZERODHA_ENCTOKEN
        if not effective_token:
            return {"status": "warning", "margins": {}, "error_message": "No broker connected"}

        zerodha_service.set_enctoken(effective_token)
        margins = zerodha_service.get_margins()
        logger.info("Margins fetched successfully for user %s", current_user.id)
        return {"status": "success", "margins": margins}
    except Exception as e:
        logger.error("Margins fetch error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/invalidate", tags=["Cache"])
def invalidate_cache(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Busts holdings and advisory cache for the authenticated user."""
    deleted = cache.delete_pattern(f"holdings:{current_user.id}:*")
    deleted += cache.delete_pattern(f"advisory:{current_user.id}:*")
    logger.info("Cache invalidated for user %s — %d keys deleted", current_user.id, deleted)
    return {"status": "success", "keys_deleted": deleted}
