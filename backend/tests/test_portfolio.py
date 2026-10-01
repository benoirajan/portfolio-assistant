import unittest
import os
import shutil
import hashlib
from typing import Dict, Any
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.db.session import bind_engine, check_db_connection, get_db_session
from src.models import Base, User, Portfolio, UserHolding, UserSession
from src.services.portfolio_repository import (
    save_portfolio,
    load_portfolio,
    _get_token_hash,
)


class TestPortfolioPersistenceComprehensive(unittest.TestCase):
    """
    Comprehensive test suite for Database Persistence, ORM constraints,
    Repository Layer, Resilient Fallbacks, and End-to-End API integration.
    """

    @classmethod
    def setUpClass(cls):
        cls._orig_demo_mode = settings.DEMO_MODE
        settings.DEMO_MODE = True
        
        # Setup isolated in-memory SQLite database with StaticPool so all connections share the same memory DB
        cls.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        bind_engine(cls.test_engine)
        Base.metadata.create_all(bind=cls.test_engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        settings.DEMO_MODE = cls._orig_demo_mode
        Base.metadata.drop_all(bind=cls.test_engine)

    def setUp(self):
        # Clean database tables before each test
        with get_db_session() as db:
            db.query(UserHolding).delete()
            db.query(Portfolio).delete()
            db.query(UserSession).delete()
            db.query(User).delete()

    def tearDown(self):
        pass

    # -------------------------------------------------------------------------
    # 1. DATABASE CONNECTIVITY & ORM SCHEMA INTEGRITY
    # -------------------------------------------------------------------------

    def test_database_health_check(self):
        """Verify DB ping returns successful connected state."""
        is_connected, msg = check_db_connection()
        self.assertTrue(is_connected)
        self.assertEqual(msg, "connected")

    def test_orm_cascade_deletion(self):
        """Verify deleting a Portfolio cascades and deletes all associated UserHoldings."""
        with get_db_session() as db:
            portfolio = Portfolio(
                token_hash="cascade_test_token",
                name="Cascade Test",
                total_investment=1000.0,
                current_value=1200.0
            )
            db.add(portfolio)
            db.flush()

            holding1 = UserHolding(portfolio_id=portfolio.id, tradingsymbol="INFY", quantity=10, average_price=100.0, last_price=120.0)
            holding2 = UserHolding(portfolio_id=portfolio.id, tradingsymbol="TCS", quantity=5, average_price=200.0, last_price=220.0)
            db.add_all([holding1, holding2])
            db.flush()

            portfolio_id = portfolio.id

        # Verify holdings exist
        with get_db_session() as db:
            holdings_count = db.query(UserHolding).filter(UserHolding.portfolio_id == portfolio_id).count()
            self.assertEqual(holdings_count, 2)

            # Delete portfolio
            p = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            db.delete(p)

        # Verify cascade deleted child holdings
        with get_db_session() as db:
            holdings_count = db.query(UserHolding).filter(UserHolding.portfolio_id == portfolio_id).count()
            self.assertEqual(holdings_count, 0)

    # -------------------------------------------------------------------------
    # 2. REPOSITORY PERSISTENCE & DIRECT DB ROW VALIDATION
    # -------------------------------------------------------------------------

    def test_save_and_direct_db_inspection(self):
        """Verify that save_portfolio directly inserts rows with correct columns in PostgreSQL/SQLite."""
        token = "test_user_token_abc"
        token_hash = _get_token_hash(token)

        payload = {
            "status": "success",
            "summary": {
                "total_holdings_count": 2,
                "total_investment": 250000.0,
                "current_value": 290000.0,
                "total_pnl": 40000.0,
                "total_pnl_percentage": 16.0
            },
            "holdings": [
                {
                    "tradingsymbol": "RELIANCE",
                    "exchange": "NSE",
                    "isin": "INE002A01018",
                    "quantity": 50,
                    "average_price": 2400.0,
                    "last_price": 2600.0,
                    "close_price": 2550.0,
                    "pnl": 10000.0,
                    "pnl_percentage": 8.33,
                    "sector": "Energy",
                    "cap_category": "Large Cap"
                },
                {
                    "tradingsymbol": "HDFCBANK",
                    "exchange": "NSE",
                    "isin": "INE040A01034",
                    "quantity": 100,
                    "average_price": 1300.0,
                    "last_price": 1600.0,
                    "close_price": 1580.0,
                    "pnl": 30000.0,
                    "pnl_percentage": 23.08,
                    "sector": "Financial Services",
                    "cap_category": "Large Cap"
                }
            ]
        }

        save_portfolio(token, payload)

        # Direct SQL inspection
        with get_db_session() as db:
            db_portfolio = db.query(Portfolio).filter(Portfolio.token_hash == token_hash).first()
            self.assertIsNotNone(db_portfolio)
            self.assertEqual(db_portfolio.total_investment, 250000.0)
            self.assertEqual(db_portfolio.current_value, 290000.0)
            self.assertEqual(db_portfolio.total_pnl, 40000.0)
            self.assertEqual(db_portfolio.total_pnl_percentage, 16.0)

            db_holdings = db.query(UserHolding).filter(UserHolding.portfolio_id == db_portfolio.id).all()
            self.assertEqual(len(db_holdings), 2)
            symbols = {h.tradingsymbol: h for h in db_holdings}
            self.assertIn("RELIANCE", symbols)
            self.assertIn("HDFCBANK", symbols)
            self.assertEqual(symbols["RELIANCE"].isin, "INE002A01018")
            self.assertEqual(symbols["RELIANCE"].quantity, 50)
            self.assertEqual(symbols["HDFCBANK"].sector, "Financial Services")

    def test_load_portfolio_reconstruction(self):
        """Verify that load_portfolio accurately reconstructs the full response dictionary."""
        token = "reconstruction_test_token"
        payload = {
            "status": "success",
            "summary": {
                "total_holdings_count": 1,
                "total_investment": 5000.0,
                "current_value": 6000.0,
                "total_pnl": 1000.0,
                "total_pnl_percentage": 20.0
            },
            "holdings": [
                {
                    "tradingsymbol": "TATAMOTORS",
                    "exchange": "NSE",
                    "quantity": 10,
                    "average_price": 500.0,
                    "last_price": 600.0,
                    "pnl": 1000.0,
                    "sector": "Automobile"
                }
            ]
        }

        save_portfolio(token, payload)
        loaded = load_portfolio(token)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["status"], "success")
        self.assertFalse(loaded["is_live"])  # Re-hydrated state
        self.assertEqual(loaded["summary"]["total_investment"], 5000.0)
        self.assertEqual(len(loaded["holdings"]), 1)
        self.assertEqual(loaded["holdings"][0]["tradingsymbol"], "TATAMOTORS")
        self.assertEqual(loaded["holdings"][0]["sector"], "Automobile")

    # -------------------------------------------------------------------------
    # 3. MULTI-TENANT ISOLATION & DATA INTEGRITY
    # -------------------------------------------------------------------------

    def test_multi_user_portfolio_isolation(self):
        """Verify User A and User B portfolios are completely isolated."""
        token_a = "user_alpha_token"
        token_b = "user_beta_token"

        data_a = {
            "status": "success",
            "summary": {"total_investment": 10000.0, "current_value": 11000.0, "total_pnl": 1000.0, "total_pnl_percentage": 10.0},
            "holdings": [{"tradingsymbol": "WIPRO", "quantity": 20, "average_price": 500.0, "last_price": 550.0}]
        }
        data_b = {
            "status": "success",
            "summary": {"total_investment": 50000.0, "current_value": 60000.0, "total_pnl": 10000.0, "total_pnl_percentage": 20.0},
            "holdings": [{"tradingsymbol": "ICICIBANK", "quantity": 50, "average_price": 1000.0, "last_price": 1200.0}]
        }

        save_portfolio(token_a, data_a)
        save_portfolio(token_b, data_b)

        loaded_a = load_portfolio(token_a)
        loaded_b = load_portfolio(token_b)

        self.assertIsNotNone(loaded_a)
        self.assertIsNotNone(loaded_b)
        self.assertEqual(loaded_a["holdings"][0]["tradingsymbol"], "WIPRO")
        self.assertEqual(loaded_b["holdings"][0]["tradingsymbol"], "ICICIBANK")
        self.assertEqual(loaded_a["summary"]["total_investment"], 10000.0)
        self.assertEqual(loaded_b["summary"]["total_investment"], 50000.0)

    def test_atomic_holding_replacement_on_rebalance(self):
        """Verify saving updated portfolio replaces old holdings without orphaned entries."""
        token = "rebalance_token"

        # Batch 1: RELIANCE & TCS
        save_portfolio(token, {
            "status": "success",
            "summary": {"total_investment": 3000.0},
            "holdings": [
                {"tradingsymbol": "RELIANCE", "quantity": 1, "average_price": 2000.0, "last_price": 2000.0},
                {"tradingsymbol": "TCS", "quantity": 1, "average_price": 1000.0, "last_price": 1000.0},
            ]
        })
        self.assertEqual(len(load_portfolio(token)["holdings"]), 2)

        # Batch 2: Sold TCS, bought INFY & LT
        save_portfolio(token, {
            "status": "success",
            "summary": {"total_investment": 4500.0},
            "holdings": [
                {"tradingsymbol": "RELIANCE", "quantity": 1, "average_price": 2000.0, "last_price": 2100.0},
                {"tradingsymbol": "INFY", "quantity": 1, "average_price": 1500.0, "last_price": 1600.0},
                {"tradingsymbol": "LT", "quantity": 1, "average_price": 1000.0, "last_price": 1100.0},
            ]
        })

        loaded = load_portfolio(token)
        self.assertEqual(len(loaded["holdings"]), 3)
        symbols = [h["tradingsymbol"] for h in loaded["holdings"]]
        self.assertNotIn("TCS", symbols)
        self.assertIn("RELIANCE", symbols)
        self.assertIn("INFY", symbols)
        self.assertIn("LT", symbols)

    # -------------------------------------------------------------------------
    # 4. EDGE CASES & RESILIENT FALLBACKS
    # -------------------------------------------------------------------------

    def test_empty_portfolio_handling(self):
        """Verify handling of empty holdings list."""
        token = "empty_portfolio_token"
        save_portfolio(token, {"status": "success", "summary": {}, "holdings": []})

        loaded = load_portfolio(token)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded["holdings"]), 0)


    # -------------------------------------------------------------------------
    # 5. END-TO-END FASTAPI INTEGRATION
    # -------------------------------------------------------------------------

    def test_api_health_endpoint(self):
        """Verify GET /health returns database status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")

    def test_api_holdings_and_cache_invalidation(self):
        """Verify GET /api/v1/holdings with auth and DELETE /api/v1/cache/invalidate."""
        from src.services.zerodha_client import zerodha_service
        from src.core.security import create_access_token

        # Create user
        with get_db_session() as db:
            user = User(email="test_portfolio_user@example.com", full_name="Portfolio Tester", tier="FREE")
            db.add(user)
            db.flush()
            user_id = user.id

        auth_token = create_access_token({"sub": user_id, "email": "test_portfolio_user@example.com", "tier": "FREE"})
        auth_headers = {"Authorization": f"Bearer {auth_token}"}

        orig_enctoken = settings.ZERODHA_ENCTOKEN
        orig_service_token = zerodha_service.enctoken
        settings.ZERODHA_ENCTOKEN = ""
        zerodha_service.set_enctoken("")
        try:
            # 1. Fetch holdings with auth
            res = self.client.get("/api/v1/holdings", headers=auth_headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn(data["status"], ("success", "warning"))

            # 2. Invalidate cache with auth
            inv_res = self.client.delete("/api/v1/cache/invalidate", headers=auth_headers)
            self.assertEqual(inv_res.status_code, 200)
            self.assertEqual(inv_res.json()["status"], "success")
        finally:
            settings.ZERODHA_ENCTOKEN = orig_enctoken
            zerodha_service.set_enctoken(orig_service_token)



if __name__ == "__main__":
    unittest.main()
