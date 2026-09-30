import json
import os
import hashlib
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.session import get_db_session, engine
from src.models.portfolio import Portfolio
from src.models.holding import UserHolding
from src.models.user import User

logger = logging.getLogger("portfolio_assistant.portfolio_repository")

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def _get_file_path(token: str) -> str:
    token_hash = _get_token_hash(token)
    return os.path.join(_DATA_DIR, f"portfolio_{token_hash}.json")


def _ensure_data_dir():
    if not os.path.exists(_DATA_DIR):
        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
        except Exception:
            pass


def _save_portfolio_to_db(token_hash: str, portfolio_data: Dict[str, Any]) -> bool:
    """Saves or updates portfolio and holdings in PostgreSQL / SQLite."""
    try:
        summary = portfolio_data.get("summary", {})
        holdings_list = portfolio_data.get("holdings", [])

        with get_db_session() as db:
            # Query existing portfolio
            stmt = select(Portfolio).where(Portfolio.token_hash == token_hash).options(selectinload(Portfolio.holdings))
            portfolio = db.execute(stmt).scalar_one_or_none()

            if not portfolio:
                portfolio = Portfolio(
                    token_hash=token_hash,
                    name=f"Portfolio-{token_hash[:6]}"
                )
                db.add(portfolio)
                db.flush()

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

        logger.info("Persisted portfolio to database for token hash %s (%d holdings)", token_hash, len(holdings_list))
        return True
    except Exception as e:
        logger.warning("Database persistence failed, relying on file fallback: %s", e)
        return False


def _load_portfolio_from_db(token_hash: str) -> Optional[Dict[str, Any]]:
    """Loads portfolio and holdings from PostgreSQL / SQLite."""
    try:
        with get_db_session() as db:
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
    except Exception as e:
        logger.warning("Failed to load portfolio from database: %s", e)
        return None


def save_portfolio(token: str, portfolio_data: Dict[str, Any]) -> None:
    """Save enriched portfolio data to database with local file backup."""
    token_hash = _get_token_hash(token)
    
    # 1. Primary: Save to Database (PostgreSQL / SQLite)
    _save_portfolio_to_db(token_hash, portfolio_data)

    # 2. Secondary: File backup
    _ensure_data_dir()
    try:
        with open(_get_file_path(token), "w") as f:
            json.dump(portfolio_data, f)
        logger.debug("Persisted portfolio file backup for token hash %s", token_hash)
    except Exception as e:
        logger.debug("File backup write skipped: %s", e)


def load_portfolio(token: str) -> Optional[Dict[str, Any]]:
    """Load previously saved portfolio data from database (or file fallback)."""
    token_hash = _get_token_hash(token)

    # 1. Primary: Try Database
    db_result = _load_portfolio_from_db(token_hash)
    if db_result and db_result.get("holdings"):
        logger.info("Loaded portfolio from database for token hash %s", token_hash)
        return db_result

    # 2. Secondary: Try File Backup
    try:
        path = _get_file_path(token)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                logger.info("Loaded portfolio from file backup for token hash %s", token_hash)
                # If loaded from file, migrate it back into database
                _save_portfolio_to_db(token_hash, data)
                return data
    except Exception as e:
        logger.error("Failed to load persisted portfolio from file: %s", e)

    return None
