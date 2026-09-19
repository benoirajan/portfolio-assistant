import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("portfolio_assistant.portfolio_repository")

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def _get_file_path(token: str) -> str:
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    return os.path.join(_DATA_DIR, f"portfolio_{token_hash}.json")

def _ensure_data_dir():
    if not os.path.exists(_DATA_DIR):
        os.makedirs(_DATA_DIR, exist_ok=True)

def save_portfolio(token: str, portfolio_data: Dict[str, Any]) -> None:
    """Save enriched portfolio data to disk for persistence across restarts."""
    _ensure_data_dir()
    try:
        with open(_get_file_path(token), "w") as f:
            json.dump(portfolio_data, f)
        logger.info(f"Persisted portfolio to disk for token hash {token[:8]}...")
    except Exception as e:
        logger.error(f"Failed to persist portfolio: {e}")

def load_portfolio(token: str) -> Optional[Dict[str, Any]]:
    """Load previously saved portfolio data from disk."""
    try:
        path = _get_file_path(token)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded portfolio from disk for token hash {token[:8]}...")
                return data
    except Exception as e:
        logger.error(f"Failed to load persisted portfolio: {e}")
    return None
