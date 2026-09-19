import unittest
import os
import json
import shutil
from src.services.portfolio_repository import save_portfolio, load_portfolio, _DATA_DIR

class TestPortfolioRepository(unittest.TestCase):
    def setUp(self):
        if os.path.exists(_DATA_DIR):
            shutil.rmtree(_DATA_DIR)
        os.makedirs(_DATA_DIR)

    def tearDown(self):
        if os.path.exists(_DATA_DIR):
            shutil.rmtree(_DATA_DIR)

    def test_save_and_load_portfolio(self):
        token = "test_token_123"
        data = {
            "status": "success",
            "holdings": [{"symbol": "RELIANCE", "quantity": 10}]
        }
        
        # Initially should be None
        self.assertIsNone(load_portfolio(token))
        
        # Save and load
        save_portfolio(token, data)
        loaded = load_portfolio(token)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["status"], "success")
        self.assertEqual(len(loaded["holdings"]), 1)
        self.assertEqual(loaded["holdings"][0]["symbol"], "RELIANCE")

if __name__ == '__main__':
    unittest.main()
