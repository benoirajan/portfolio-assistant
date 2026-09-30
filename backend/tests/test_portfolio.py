import unittest
import os
import shutil
from sqlalchemy import create_engine
from src.db.session import bind_engine, check_db_connection
from src.models import Base
from src.services.portfolio_repository import save_portfolio, load_portfolio, _DATA_DIR


class TestPortfolioRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database specifically for test isolation
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        bind_engine(test_engine)
        Base.metadata.create_all(bind=test_engine)

    def setUp(self):
        if os.path.exists(_DATA_DIR):
            shutil.rmtree(_DATA_DIR)
        os.makedirs(_DATA_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(_DATA_DIR):
            shutil.rmtree(_DATA_DIR)

    def test_database_connection(self):
        is_connected, msg = check_db_connection()
        self.assertTrue(is_connected, f"Database check failed: {msg}")

    def test_save_and_load_portfolio(self):
        token = "test_token_123"
        data = {
            "status": "success",
            "summary": {
                "total_holdings_count": 2,
                "total_investment": 150000.0,
                "current_value": 165000.0,
                "total_pnl": 15000.0,
                "total_pnl_percentage": 10.0
            },
            "holdings": [
                {
                    "tradingsymbol": "RELIANCE",
                    "exchange": "NSE",
                    "quantity": 25,
                    "average_price": 2400.0,
                    "last_price": 2600.0,
                    "pnl": 5000.0,
                    "sector": "Energy"
                },
                {
                    "tradingsymbol": "INFY",
                    "exchange": "NSE",
                    "quantity": 50,
                    "average_price": 1800.0,
                    "last_price": 2000.0,
                    "pnl": 10000.0,
                    "sector": "IT"
                }
            ]
        }

        # Initially should be None for non-existent token
        self.assertIsNone(load_portfolio("unknown_token_999"))

        # Save and re-load from database
        save_portfolio(token, data)
        loaded = load_portfolio(token)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["status"], "success")
        self.assertEqual(len(loaded["holdings"]), 2)
        symbols = [h.get("tradingsymbol") for h in loaded["holdings"]]
        self.assertIn("RELIANCE", symbols)
        self.assertIn("INFY", symbols)
        self.assertEqual(loaded["summary"]["total_investment"], 150000.0)

    def test_portfolio_update_replaces_holdings(self):
        token = "update_token_456"
        data_v1 = {
            "status": "success",
            "summary": {"total_investment": 1000.0},
            "holdings": [{"tradingsymbol": "TCS", "quantity": 10, "average_price": 100.0, "last_price": 110.0}]
        }
        save_portfolio(token, data_v1)
        loaded_v1 = load_portfolio(token)
        self.assertEqual(len(loaded_v1["holdings"]), 1)
        self.assertEqual(loaded_v1["holdings"][0]["tradingsymbol"], "TCS")

        # Update with new holdings
        data_v2 = {
            "status": "success",
            "summary": {"total_investment": 2000.0},
            "holdings": [{"tradingsymbol": "HDFCBANK", "quantity": 20, "average_price": 100.0, "last_price": 120.0}]
        }
        save_portfolio(token, data_v2)
        loaded_v2 = load_portfolio(token)
        self.assertEqual(len(loaded_v2["holdings"]), 1)
        self.assertEqual(loaded_v2["holdings"][0]["tradingsymbol"], "HDFCBANK")


if __name__ == '__main__':
    unittest.main()
