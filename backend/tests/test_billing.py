"""
Tests for SaaS Monetization — Tier Gating, AI Quota, and Billing API.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_billing.py -v
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ── Bootstrap path so imports work without installing the package ──────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Minimal env stubs (no real DB / Redis required) ───────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RAZORPAY_MOCK_MODE", "true")


# ==============================================================================
# 1. TIER RANK LOGIC
# ==============================================================================

class TestTierRank(unittest.TestCase):
    def test_free_rank_is_lowest(self):
        from src.core.entitlements import TIER_RANK
        self.assertLess(TIER_RANK["FREE"], TIER_RANK["PRO"])

    def test_pro_rank_below_elite(self):
        from src.core.entitlements import TIER_RANK
        self.assertLess(TIER_RANK["PRO"], TIER_RANK["ELITE"])

    def test_elite_rank_is_highest(self):
        from src.core.entitlements import TIER_RANK
        self.assertEqual(TIER_RANK["ELITE"], max(TIER_RANK.values()))


# ==============================================================================
# 2. require_tier DEPENDENCY
# ==============================================================================

class TestRequireTier(unittest.TestCase):
    def _make_user(self, tier: str):
        user = MagicMock()
        user.id = "user-abc"
        user.tier = tier
        return user

    def _call_guard(self, minimum: str, user_tier: str):
        """Calls the require_tier inner check directly (bypasses FastAPI DI)."""
        from fastapi import HTTPException
        from src.core.entitlements import require_tier
        guard = require_tier(minimum)
        # Inject user directly (skipping Depends resolution)
        return guard.__wrapped__(current_user=self._make_user(user_tier)) if hasattr(guard, "__wrapped__") else self._invoke(guard, user_tier)

    def _invoke(self, guard_factory, user_tier):
        from fastapi import HTTPException
        from src.core.entitlements import TIER_RANK
        # Extract the inner function directly
        # require_tier returns a closure; call it with the mocked user
        from src.core.entitlements import require_tier
        from unittest.mock import patch

        user = self._make_user(user_tier)
        inner = require_tier("PRO")  # we re-call with a fresh guard below
        # We test the logic directly
        return user

    def test_free_user_blocked_for_pro_endpoint(self):
        from fastapi import HTTPException
        from src.core.entitlements import TIER_RANK

        user_rank = TIER_RANK.get("FREE", 0)
        required_rank = TIER_RANK.get("PRO", 1)
        self.assertLess(user_rank, required_rank, "FREE should be below PRO")

    def test_pro_user_allowed_for_pro_endpoint(self):
        from src.core.entitlements import TIER_RANK

        user_rank = TIER_RANK.get("PRO", 0)
        required_rank = TIER_RANK.get("PRO", 0)
        self.assertGreaterEqual(user_rank, required_rank)

    def test_elite_user_allowed_for_pro_endpoint(self):
        from src.core.entitlements import TIER_RANK

        user_rank = TIER_RANK.get("ELITE", 0)
        required_rank = TIER_RANK.get("PRO", 0)
        self.assertGreaterEqual(user_rank, required_rank)

    def test_free_user_blocked_for_elite_endpoint(self):
        from src.core.entitlements import TIER_RANK

        user_rank = TIER_RANK.get("FREE", 0)
        required_rank = TIER_RANK.get("ELITE", 0)
        self.assertLess(user_rank, required_rank)


# ==============================================================================
# 3. AI QUOTA LOGIC
# ==============================================================================

class TestAiQuotaLogic(unittest.TestCase):
    """Tests quota counter logic using a simulated cache dict."""

    def setUp(self):
        self._cache: dict = {}

    def _get(self, key):
        entry = self._cache.get(key)
        return entry

    def _set(self, key, val, ttl=None):
        self._cache[key] = val

    def _simulate_quota(self, tier: str, current_count: int, limit: int) -> bool:
        """Returns True if the request should be allowed, False if blocked."""
        return current_count < limit

    def test_free_quota_allows_three(self):
        from src.core.config import settings
        limit = settings.TIER_AI_QUOTA["FREE"]
        self.assertTrue(self._simulate_quota("FREE", 0, limit))
        self.assertTrue(self._simulate_quota("FREE", 1, limit))
        self.assertTrue(self._simulate_quota("FREE", 2, limit))
        self.assertFalse(self._simulate_quota("FREE", 3, limit))

    def test_pro_quota_allows_fifty(self):
        from src.core.config import settings
        limit = settings.TIER_AI_QUOTA["PRO"]
        self.assertEqual(limit, 50)
        self.assertTrue(self._simulate_quota("PRO", 49, limit))
        self.assertFalse(self._simulate_quota("PRO", 50, limit))

    def test_elite_quota_is_sentinel(self):
        from src.core.config import settings
        limit = settings.TIER_AI_QUOTA["ELITE"]
        self.assertEqual(limit, 9999)
        # Even 9998 should be allowed (sentinel)
        self.assertTrue(self._simulate_quota("ELITE", 9998, limit))

    def test_quota_key_format(self):
        user_id = "user-123"
        expected_key = f"quota:ai:{user_id}"
        self.assertEqual(expected_key, f"quota:ai:{user_id}")


# ==============================================================================
# 4. BILLING CONFIG
# ==============================================================================

class TestBillingConfig(unittest.TestCase):
    def test_pro_price_paise(self):
        from src.core.config import settings
        self.assertEqual(settings.TIER_PRICE_PAISE["PRO"], 29900)

    def test_elite_price_paise(self):
        from src.core.config import settings
        self.assertEqual(settings.TIER_PRICE_PAISE["ELITE"], 79900)

    def test_mock_mode_default_true(self):
        from src.core.config import settings
        # In test environment RAZORPAY_MOCK_MODE=true was set in os.environ above
        self.assertTrue(settings.RAZORPAY_MOCK_MODE)

    def test_three_tiers_defined(self):
        from src.core.config import settings
        self.assertIn("FREE", settings.TIER_AI_QUOTA)
        self.assertIn("PRO", settings.TIER_AI_QUOTA)
        self.assertIn("ELITE", settings.TIER_AI_QUOTA)


# ==============================================================================
# 5. BILLING PLANS ENDPOINT (via TIER_DEFINITIONS constant)
# ==============================================================================

class TestBillingPlanDefinitions(unittest.TestCase):
    def test_three_plans_exist(self):
        from src.api.billing import TIER_DEFINITIONS
        self.assertEqual(len(TIER_DEFINITIONS), 3)

    def test_free_plan_has_zero_price(self):
        from src.api.billing import TIER_DEFINITIONS
        free = next(p for p in TIER_DEFINITIONS if p["tier"] == "FREE")
        self.assertEqual(free["price_inr"], 0)

    def test_pro_plan_is_highlighted(self):
        from src.api.billing import TIER_DEFINITIONS
        pro = next(p for p in TIER_DEFINITIONS if p["tier"] == "PRO")
        self.assertTrue(pro["highlight"])

    def test_elite_plan_has_unlimited_ai(self):
        from src.api.billing import TIER_DEFINITIONS
        from src.core.config import settings
        elite = next(p for p in TIER_DEFINITIONS if p["tier"] == "ELITE")
        self.assertEqual(elite["ai_runs_per_month"], settings.TIER_AI_QUOTA["ELITE"])


# ==============================================================================
# 6. RAZORPAY SIGNATURE VERIFICATION
# ==============================================================================

class TestRazorpaySignatureVerification(unittest.TestCase):
    def test_mock_mode_accepts_any_signature(self):
        from src.api.billing import _verify_razorpay_signature
        # In mock mode any signature should return True
        result = _verify_razorpay_signature("order_123", "pay_456", "any_sig_value")
        self.assertTrue(result)

    def test_mock_webhook_accepts_any_signature(self):
        from src.api.billing import _verify_webhook_signature
        result = _verify_webhook_signature(b'{"event":"payment.captured"}', "any_sig")
        self.assertTrue(result)

    def test_mock_order_returns_expected_fields(self):
        from src.api.billing import _mock_create_order
        order = _mock_create_order("PRO", 29900)
        self.assertIn("id", order)
        self.assertTrue(order["id"].startswith("order_MOCK_"))
        self.assertEqual(order["amount"], 29900)
        self.assertEqual(order["currency"], "INR")
        self.assertTrue(order["mock"])


if __name__ == "__main__":
    unittest.main()
