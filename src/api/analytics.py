from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.services.analytics_engine import analytics_engine
from src.services.tax_harvesting import tax_harvesting_analyzer
from src.core.config import settings

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/fundamentals")
def get_portfolio_fundamentals(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns holdings enriched with fundamental ratios (P/E, P/B, ROE, 200 SMA trend)."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        holdings = zerodha_service.get_holdings()
        enriched = market_data_service.enrich_holdings_with_fundamentals(holdings)
        return {"status": "success", "holdings": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
def get_portfolio_performance_metrics(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns XIRR, Sharpe Ratio, Sortino Ratio, Beta, and Herfindahl concentration index."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        holdings = zerodha_service.get_holdings()
        enriched = market_data_service.enrich_holdings_with_fundamentals(holdings)
        metrics = analytics_engine.calculate_portfolio_metrics(enriched)
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tax-harvesting")
def get_tax_harvesting_analysis(x_enctoken: Optional[str] = Header(None, alias="X-Enctoken")):
    """Returns STCG vs LTCG tax liability calculations and loss harvesting opportunities."""
    try:
        effective_token = x_enctoken if x_enctoken else settings.ZERODHA_ENCTOKEN
        if effective_token:
            zerodha_service.set_enctoken(effective_token)

        holdings = zerodha_service.get_holdings()
        analysis = tax_harvesting_analyzer.analyze_tax_harvesting(holdings)
        return {"status": "success", "tax_analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
