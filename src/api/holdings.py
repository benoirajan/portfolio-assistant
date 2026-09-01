from fastapi import APIRouter, HTTPException, Header
from typing import List, Dict, Any, Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Portfolio"])

@router.get("/holdings")
def get_holdings(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns long-term Demat holdings enriched with P&L, fundamentals, and metrics."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        raw_holdings, is_live, error_msg = zerodha_service.get_holdings_with_status()
        enriched_holdings = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)
        
        total_investment = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in enriched_holdings)
        current_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in enriched_holdings)
        total_pnl = current_value - total_investment
        total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0
        
        return {
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
def get_positions(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns day and net positions."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        positions = zerodha_service.get_positions()
        return {"status": "success", "positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/margins")
def get_margins(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns cash balance and margin utilization."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        margins = zerodha_service.get_margins()
        return {"status": "success", "margins": margins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
