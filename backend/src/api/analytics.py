import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Dict, Any, Optional
from src.services.zerodha_client import zerodha_service
from src.services.market_data import market_data_service
from src.services.analytics_engine import analytics_engine
from src.services.tax_harvesting import tax_harvesting_analyzer
from src.core.config import settings
from src.core.security import get_current_user, get_user_enctoken
from src.models.user import User

logger = logging.getLogger("portfolio_assistant.api.analytics")
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/fundamentals")
def get_portfolio_fundamentals(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns holdings enriched with fundamental ratios for authenticated user."""
    try:
        effective_token = x_enctoken or get_user_enctoken(current_user.id) or settings.ZERODHA_ENCTOKEN
        if not effective_token:
            return {"status": "warning", "holdings": [], "error_message": "No broker connected"}

        zerodha_service.set_enctoken(effective_token)
        holdings = zerodha_service.get_holdings()
        enriched = market_data_service.enrich_holdings_with_fundamentals(holdings)
        logger.info("Fundamentals fetched for user %s — %d holdings enriched", current_user.id, len(enriched))
        return {"status": "success", "holdings": enriched}
    except Exception as e:
        logger.error("Fundamentals error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
def get_portfolio_performance_metrics(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns XIRR, Sharpe Ratio, Sortino Ratio, Beta, and Herfindahl index for authenticated user."""
    try:
        effective_token = x_enctoken or get_user_enctoken(current_user.id) or settings.ZERODHA_ENCTOKEN
        if not effective_token:
            return {
                "status": "warning",
                "metrics": {
                    "xirr_percentage": 0.0,
                    "portfolio_beta": 1.0,
                    "sharpe_ratio": 0.0,
                    "sortino_ratio": 0.0,
                    "cagr_percentage": 0.0,
                    "herfindahl_index": 0.0,
                },
                "error_message": "No broker connected",
            }

        zerodha_service.set_enctoken(effective_token)
        holdings = zerodha_service.get_holdings()
        enriched = market_data_service.enrich_holdings_with_fundamentals(holdings)
        trades = zerodha_service.get_trades()
        metrics = analytics_engine.calculate_portfolio_metrics(enriched, trades=trades)
        logger.info("Performance metrics for user %s — xirr=%.2f%% beta=%.2f sharpe=%.2f",
                    current_user.id, metrics.get("xirr_percentage", 0), metrics.get("portfolio_beta", 0), metrics.get("sharpe_ratio", 0))
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.error("Performance metrics error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tax-harvesting")
def get_tax_harvesting_analysis(
    x_enctoken: Optional[str] = Header(None, alias="X-Enctoken"),
    current_user: User = Depends(get_current_user)
):
    """Returns STCG vs LTCG tax calculations and loss harvesting opportunities for authenticated user."""
    try:
        effective_token = x_enctoken or get_user_enctoken(current_user.id) or settings.ZERODHA_ENCTOKEN
        if not effective_token:
            return {
                "status": "warning",
                "tax_analysis": {
                    "net_stcg": 0.0,
                    "net_ltcg": 0.0,
                    "harvestable_loss_candidates": [],
                },
                "error_message": "No broker connected",
            }

        zerodha_service.set_enctoken(effective_token)
        holdings = zerodha_service.get_holdings()
        analysis = tax_harvesting_analyzer.analyze_tax_harvesting(holdings)
        logger.info("Tax analysis for user %s — stcg=%.2f ltcg=%.2f candidates=%d",
                    current_user.id, analysis.get("net_stcg", 0), analysis.get("net_ltcg", 0),
                    len(analysis.get("harvestable_loss_candidates", [])))
        return {"status": "success", "tax_analysis": analysis}
    except Exception as e:
        logger.error("Tax harvesting error for user %s: %s", current_user.id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
