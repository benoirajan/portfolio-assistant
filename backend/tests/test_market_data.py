import unittest
from unittest.mock import patch
from src.core.config import settings
from src.services.market_data import market_data_service, STOCK_METADATA_DB, _FUNDAMENTALS_CACHE

class TestMarketData(unittest.TestCase):
    def test_get_stock_fundamental_data_fallback_merge(self):
        # Clear cache before test
        _FUNDAMENTALS_CACHE.clear()
        
        # Mock _fetch_yfinance to return some valid data but with 0.0 for roe and roce
        # and None for pe_ratio
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
        
        with patch.object(settings, "DEMO_MODE", False), patch.object(market_data_service, "_fetch_yfinance", return_value=mock_yfinance_data):
            # We test with "BEL" which we just added to the DB
            data = market_data_service.get_stock_fundamental_data("BEL")
            
            # Verify that the 0.0 and None values got replaced by the DB values
            self.assertEqual(data["roe"], STOCK_METADATA_DB["BEL"]["roe"])
            self.assertEqual(data["roce"], STOCK_METADATA_DB["BEL"]["roce"])
            self.assertEqual(data["pe_ratio"], STOCK_METADATA_DB["BEL"]["pe_ratio"])
            
            # Verify that other valid values from yfinance were NOT replaced
            self.assertEqual(data["pb_ratio"], 10.0)
            self.assertEqual(data["promoter_holding_pct"], 51.14)

    def test_get_stock_fundamental_data_no_yfinance_data(self):
        _FUNDAMENTALS_CACHE.clear()
        with patch.object(settings, "DEMO_MODE", False), patch.object(market_data_service, "_fetch_yfinance", return_value=None):
            data = market_data_service.get_stock_fundamental_data("ONGC")
            self.assertEqual(data["roe"], STOCK_METADATA_DB["ONGC"]["roe"])
            self.assertEqual(data["symbol"], "ONGC")

if __name__ == '__main__':
    unittest.main()
