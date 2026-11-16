"""Unit tests for PostgreSQL-backed AI quota enforcement & natural 30-day window reset."""

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.entitlements import check_and_consume_ai_quota
from src.core.config import settings
from src.core.security import create_access_token
from src.db.session import bind_engine
from src.main import app
from src.models import Base, User
from src.api.billing import _upgrade_user_tier


class TestPostgresAiQuota(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Isolated in-memory SQLite database
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        bind_engine(cls.engine)
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.user_id = str(uuid.uuid4())
        self.user = User(
            id=self.user_id,
            email=f"test_{self.user_id[:8]}@example.com",
            tier="FREE",
            is_active=True,
            is_verified=True,
            ai_quota_used=0,
            ai_quota_reset_at=None,
        )
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_day_1_initial_query_anchors_30_day_window(self):
        """First query initializes ai_quota_used=1 and sets ai_quota_reset_at = now + 30 days."""
        t0 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = t0
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            consumed_user = check_and_consume_ai_quota(self.user, self.db)
            self.assertEqual(consumed_user.ai_quota_used, 1)
            self.assertEqual(consumed_user.ai_quota_reset_at, t0 + timedelta(days=30))

    def test_day_15_and_day_28_do_not_slide_window(self):
        """Consecutive queries on Day 15 and Day 28 increment count but PRESERVE Day 31 reset date."""
        day_1 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        expected_reset = day_1 + timedelta(days=30)  # 2026-12-01 10:00:00

        # Day 1: 1st query
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_1
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            check_and_consume_ai_quota(self.user, self.db)

        # Day 15: 2nd query
        day_15 = datetime(2026, 11, 15, 14, 30, 0, tzinfo=timezone.utc)
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_15
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            user_day_15 = check_and_consume_ai_quota(self.user, self.db)

            self.assertEqual(user_day_15.ai_quota_used, 2)
            # Crucial assertion: reset date MUST NOT slide to Day 45
            self.assertEqual(user_day_15.ai_quota_reset_at, expected_reset)

        # Day 28: 3rd query
        day_28 = datetime(2026, 11, 28, 9, 15, 0, tzinfo=timezone.utc)
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_28
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            user_day_28 = check_and_consume_ai_quota(self.user, self.db)

            self.assertEqual(user_day_28.ai_quota_used, 3)
            # Crucial assertion: reset date MUST NOT slide to Day 58
            self.assertEqual(user_day_28.ai_quota_reset_at, expected_reset)

    def test_day_29_exhausted_quota_raises_429_with_headers(self):
        """Query 4 on FREE plan (limit 3) raises HTTP 429 and does not increment usage."""
        day_1 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        expected_reset = day_1 + timedelta(days=30)

        # Consume 3 queries
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_1
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            for _ in range(3):
                check_and_consume_ai_quota(self.user, self.db)

        # Day 29: 4th query attempts to execute
        day_29 = datetime(2026, 11, 29, 10, 0, 0, tzinfo=timezone.utc)
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_29
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            with self.assertRaises(HTTPException) as ctx:
                check_and_consume_ai_quota(self.user, self.db)

            self.assertEqual(ctx.exception.status_code, 429)
            self.assertEqual(ctx.exception.headers["X-Quota-Limit"], "3")
            self.assertEqual(ctx.exception.headers["X-Quota-Used"], "3")
            # 2 days remaining until expected_reset (172800 seconds)
            self.assertEqual(ctx.exception.headers["X-Quota-Reset"], str(2 * 86400))

            # Database usage must remain 3
            refreshed = self.db.get(User, self.user_id)
            self.assertEqual(refreshed.ai_quota_used, 3)
            self.assertEqual(refreshed.ai_quota_reset_at, expected_reset)

    def test_day_32_natural_window_reset(self):
        """After 30-day window expires (Day 32), quota automatically resets to 0 and starts fresh."""
        day_1 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

        # Exhaust quota on Day 1
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_1
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            for _ in range(3):
                check_and_consume_ai_quota(self.user, self.db)

        # Day 32: 31 days elapsed
        day_32 = datetime(2026, 12, 2, 10, 0, 0, tzinfo=timezone.utc)
        expected_new_reset = day_32 + timedelta(days=30)

        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = day_32
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            user_day_32 = check_and_consume_ai_quota(self.user, self.db)
            # Usage reset to 0 and consumed 1 run for this request
            self.assertEqual(user_day_32.ai_quota_used, 1)
            self.assertEqual(user_day_32.ai_quota_reset_at, expected_new_reset)

    def test_tier_upgrade_resets_quota_and_aligns_window(self):
        """Upgrading tier immediately resets ai_quota_used to 0 and aligns reset_at with billing period."""
        # User has used 3 runs
        self.user.ai_quota_used = 3
        self.user.ai_quota_reset_at = datetime(2026, 11, 25, 0, 0, 0, tzinfo=timezone.utc)
        self.db.commit()

        # Upgrade to PRO
        now = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
        with patch("src.api.billing.datetime") as mock_dt:
            mock_dt.now.return_value = now
            _upgrade_user_tier(self.db, self.user, "PRO", "order_123", "pay_456")
            self.db.commit()

        refreshed = self.db.get(User, self.user_id)
        self.assertEqual(refreshed.tier, "PRO")
        self.assertEqual(refreshed.ai_quota_used, 0)
        self.assertEqual(refreshed.ai_quota_reset_at, now + timedelta(days=30))

    def test_get_ai_quota_endpoint_reflects_postgres_data(self):
        """GET /api/v1/billing/quota returns current usage and remaining TTL accurately."""
        token = create_access_token({"sub": self.user.id, "email": self.user.email, "tier": "FREE"})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Initially unused
        resp = self.client.get("/api/v1/billing/quota", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["used"], 0)
        self.assertEqual(data["limit"], 3)
        self.assertEqual(data["remaining"], 3)
        self.assertIsNone(data["resets_at"])

        # 2. Consume 2 runs
        now = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
        with patch("src.core.entitlements.datetime") as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            check_and_consume_ai_quota(self.user, self.db)
            check_and_consume_ai_quota(self.user, self.db)

        with patch("src.api.billing.datetime") as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            resp = self.client.get("/api/v1/billing/quota", headers=headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["used"], 2)
            self.assertEqual(data["limit"], 3)
            self.assertEqual(data["remaining"], 1)
            self.assertEqual(data["resets_in_seconds"], 30 * 86400)
            self.assertIsNotNone(data["resets_at"])

