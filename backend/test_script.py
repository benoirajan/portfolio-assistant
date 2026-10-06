import sys
sys.path.append('backend')
from src.services.market_data import market_data_service, STOCK_METADATA_DB, _FUNDAMENTALS_CACHE

mock_yfinance_data = {
    "symbol": "BEL",
    "sector": "Defense",
    "cap_category": "Large Cap",
    "pe_ratio": None,
    "pb_ratio": 10.0,
    "roe": 0.0,
    "div_yield": 1.0,
    "sma_200": 250.0,
    "roce": 0.0,
    "fcf_yield": 2.0,
    "debt_to_equity": 0.1,
    "peg_ratio": 2.0,
    "forward_pe": 35.0,
    "promoter_holding_pct": 51.14,
    "promoter_pledge_pct": 0.0,
}
_FUNDAMENTALS_CACHE.clear()
market_data_service._fetch_yfinance = lambda sym: mock_yfinance_data
print("db:", STOCK_METADATA_DB["BEL"]["pb_ratio"])
print("mock before:", mock_yfinance_data["pb_ratio"])
data = market_data_service.get_stock_fundamental_data("BEL")
print("after:", data["pb_ratio"])
print(data)
