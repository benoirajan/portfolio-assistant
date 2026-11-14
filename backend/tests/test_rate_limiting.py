"""
Tests for HTTP Rate Limiting (CRIT-03) and Advisory Quota Gating (CRIT-04).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RAZORPAY_MOCK_MODE", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_12345678901234567890")
#just mock key don't panic
os.environ.setdefault("ENCRYPTION_SECRET_KEY", "vXz7e9K3N4P1Q8R6T2U5W7Y9A1B3C5E7G9I1K3M5O7Q=")

from src.main import app
from src.core.rate_limit import limiter
from src.models.user import User
from src.core.entitlements import check_and_consume_ai_quota
from src.db.session import bind_engine
from src.models import Base
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


class TestRateLimitingAndQuota(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        Base.metadata.drop_all(bind=cls.test_engine)

    def setUp(self):
        limiter.reset()

    def tearDown(self):
        limiter.reset()

    def test_rate_limiter_exceeded_returns_429(self):
        """Verify endpoints decorated with @limiter.limit return 429 once limit is exceeded."""
        # /api/v1/auth/resend-otp is limited to 3/minute
        for i in range(3):
            resp = self.client.post("/api/v1/auth/resend-otp", json={"email": "nobody@example.com"})
            # Prior to exceeding, status is 404 (user not found) or 200, but not 429
            self.assertNotEqual(resp.status_code, 429, f"Request {i+1} unexpectedly hit rate limit")

        # 4th request within 1 minute MUST return HTTP 429 RateLimitExceeded
        resp_blocked = self.client.post("/api/v1/auth/resend-otp", json={"email": "nobody@example.com"})
        self.assertEqual(resp_blocked.status_code, 429)
        self.assertIn("Rate limit exceeded", resp_blocked.text)

    def test_advisory_recommendations_enforces_ai_quota_gate(self):
        """CRIT-04: Verify /advisory/recommendations depends on check_and_consume_ai_quota."""
        # Inspect route dependency signatures
        from src.api.advisory import router
        rec_route = next(r for r in router.routes if r.path == "/api/v1/advisory/recommendations")
        dep_callables = [d.call for d in rec_route.dependant.dependencies]
        self.assertIn(
            check_and_consume_ai_quota,
            dep_callables,
            "CRIT-04 verification failed: check_and_consume_ai_quota is not in /recommendations dependencies",
        )

