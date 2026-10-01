import hashlib
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.session import get_db_session
from src.models.portfolio import Portfolio
from src.models.holding import UserHolding

logger = logging.getLogger("portfolio_assistant.portfolio_repository")


def _get_token_hash(token: str, user_id: Optional[str] = None) -> str:
    seed = f"{user_id}:{token}" if user_id else token
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def save_portfolio(
    token: str,
    portfolio_data: Dict[str, Any],
    user_id: Optional[str] = None
) -> bool:
    """Saves or updates portfolio and holdings strictly in PostgreSQL with tenant isolation."""
    token_hash = _get_token_hash(token, user_id)
    summary = portfolio_data.get("summary", {})
    holdings_list = portfolio_data.get("holdings", [])

    with get_db_session() as db:
        # Query existing portfolio by user_id (if available) or token_hash
        if user_id:
            stmt = select(Portfolio).where(Portfolio.user_id == user_id).options(selectinload(Portfolio.holdings))
        else:
            stmt = select(Portfolio).where(Portfolio.token_hash == token_hash).options(selectinload(Portfolio.holdings))
        
        portfolio = db.execute(stmt).scalar_one_or_none()

        if not portfolio:
            portfolio = Portfolio(
                user_id=user_id,
                token_hash=token_hash,
                name=f"Portfolio-{token_hash[:6]}"
            )
            db.add(portfolio)
            db.flush()
        else:
            if user_id and not portfolio.user_id:
                portfolio.user_id = user_id
            portfolio.token_hash = token_hash

        portfolio.total_investment = float(summary.get("total_investment", 0.0) or 0.0)
        portfolio.current_value = float(summary.get("current_value", 0.0) or 0.0)
        portfolio.total_pnl = float(summary.get("total_pnl", 0.0) or 0.0)
        portfolio.total_pnl_percentage = float(summary.get("total_pnl_percentage", 0.0) or 0.0)
        portfolio.raw_summary = summary

        # Clear existing holdings and replace with latest batch
        portfolio.holdings.clear()
        db.flush()

        for h in holdings_list:
            holding = UserHolding(
                portfolio_id=portfolio.id,
                tradingsymbol=str(h.get("tradingsymbol") or h.get("symbol") or "UNKNOWN"),
                exchange=str(h.get("exchange", "NSE")),
                isin=h.get("isin"),
                quantity=int(h.get("quantity", 0)),
                average_price=float(h.get("average_price", 0.0) or 0.0),
                last_price=float(h.get("last_price", 0.0) or 0.0),
                close_price=float(h.get("close_price", 0.0)) if h.get("close_price") is not None else None,
                pnl=float(h.get("pnl", 0.0)) if h.get("pnl") is not None else None,
                pnl_percentage=float(h.get("pnl_percentage", 0.0)) if h.get("pnl_percentage") is not None else None,
                sector=h.get("sector"),
                cap_category=h.get("cap_category"),
                raw_data=h
            )
            portfolio.holdings.append(holding)

    logger.info("Persisted portfolio to PostgreSQL (user_id=%s, token_hash=%s, holdings=%d)",
                user_id, token_hash, len(holdings_list))
    return True


def load_portfolio(
    token: str,
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Loads tenant-isolated portfolio and holdings directly from PostgreSQL."""
    token_hash = _get_token_hash(token, user_id)

    with get_db_session() as db:
        if user_id:
            stmt = select(Portfolio).where(Portfolio.user_id == user_id).options(selectinload(Portfolio.holdings))
        else:
            stmt = select(Portfolio).where(Portfolio.token_hash == token_hash).options(selectinload(Portfolio.holdings))
        
        portfolio = db.execute(stmt).scalar_one_or_none()

        if not portfolio:
            return None

        reconstructed_holdings: List[Dict[str, Any]] = []
        for h in portfolio.holdings:
            if h.raw_data and isinstance(h.raw_data, dict):
                holding_dict = dict(h.raw_data)
            else:
                holding_dict = {
                    "tradingsymbol": h.tradingsymbol,
                    "exchange": h.exchange,
                    "isin": h.isin,
                    "quantity": h.quantity,
                    "average_price": h.average_price,
                    "last_price": h.last_price,
                    "pnl": h.pnl,
                    "sector": h.sector,
                    "cap_category": h.cap_category,
                }
            reconstructed_holdings.append(holding_dict)

        summary = portfolio.raw_summary or {
            "total_holdings_count": len(reconstructed_holdings),
            "total_investment": round(portfolio.total_investment, 2),
            "current_value": round(portfolio.current_value, 2),
            "total_pnl": round(portfolio.total_pnl, 2),
            "total_pnl_percentage": round(portfolio.total_pnl_percentage, 2)
        }

        return {
            "status": "success",
            "is_live": False,
            "summary": summary,
            "holdings": reconstructed_holdings
        }
