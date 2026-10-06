"""
Entitlement middleware for SaaS tier gating and Gemini AI quota enforcement.

Usage:
    # Gate an endpoint to PRO tier or above:
    @router.get("/premium-feature")
    def premium(current_user: User = Depends(require_tier("PRO"))):
        ...

    # Consume one Gemini AI quota unit (raises 429 when exhausted):
    @router.get("/advisory/pipeline")
    def pipeline(current_user: User = Depends(check_and_consume_ai_quota)):
        ...
"""

import logging
from typing import Literal

from fastapi import Depends, HTTPException, status

from src.core import cache
from src.core.config import settings
from src.core.security import get_current_user
from src.models.user import User

logger = logging.getLogger("portfolio_assistant.entitlements")

# Tier rank map — higher is better
TIER_RANK: dict[str, int] = {"FREE": 0, "PRO": 1, "ELITE": 2}


def require_tier(minimum_tier: Literal["FREE", "PRO", "ELITE"]):
    """FastAPI dependency factory that enforces a minimum subscription tier.

    Returns a dependency that resolves to the authenticated User if their
    tier meets the requirement, or raises HTTP 403 otherwise.

    Example::

        @router.get("/tax-harvesting")
        def tax(current_user: User = Depends(require_tier("PRO"))):
            ...
    """

    def _check_tier(current_user: User = Depends(get_current_user)) -> User:
        user_tier = (current_user.tier or "FREE").upper()
        user_rank = TIER_RANK.get(user_tier, 0)
        required_rank = TIER_RANK.get(minimum_tier, 0)

        if user_rank < required_rank:
            logger.warning(
                "Tier gate blocked — user=%s tier=%s required=%s",
                current_user.id,
                user_tier,
                minimum_tier,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This feature requires {minimum_tier} plan or above. "
                    f"Your current plan is {user_tier}. "
                    f"Upgrade at /api/v1/billing/plans."
                ),
                headers={"X-Required-Tier": minimum_tier},
            )
        return current_user

    return _check_tier


def check_and_consume_ai_quota(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency: checks and atomically increments the monthly Gemini AI quota.

    Quota is stored in Redis (container-ready; no disk fallback).
    If Redis is unavailable the request is allowed through with a warning log
    rather than hard-blocking users — fail-open is the safer UX choice here.

    Quota resets: TTL is set to 30 days on first write; it resets naturally
    when the key expires. Billing webhooks can proactively delete the key on
    tier upgrade/renewal via ``cache.delete(f"quota:ai:{user_id}")``.

    Raises:
        HTTP 429 when the user's monthly AI run quota is exhausted.
    """
    tier = (current_user.tier or "FREE").upper()
    quota_limit: int = settings.TIER_AI_QUOTA.get(tier, 3)
    quota_key = f"quota:ai:{current_user.id}"

    # --- Quota read ---
    try:
        current_count_raw = cache.get(quota_key)
        current_count = int(current_count_raw) if current_count_raw is not None else 0
    except Exception as exc:
        # Redis unavailable — fail open so users are never hard-blocked by infra issues
        logger.warning(
            "AI quota check Redis error for user=%s — allowing request: %s",
            current_user.id,
            exc,
        )
        return current_user

    if current_count >= quota_limit:
        logger.info(
            "AI quota exhausted — user=%s tier=%s used=%d limit=%d",
            current_user.id,
            tier,
            current_count,
            quota_limit,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Monthly AI advisory quota exhausted "
                f"({quota_limit} runs for {tier} plan). "
                f"Upgrade your plan to get more runs."
            ),
            headers={
                "X-Quota-Limit": str(quota_limit),
                "X-Quota-Used": str(current_count),
                "X-Required-Tier": "PRO" if tier == "FREE" else "ELITE",
            },
        )

    # --- Quota increment (30-day rolling TTL = 2_592_000 seconds) ---
    try:
        new_count = current_count + 1
        cache.set(quota_key, new_count, ttl=2_592_000)
        logger.info(
            "AI quota consumed — user=%s tier=%s used=%d/%d",
            current_user.id,
            tier,
            new_count,
            quota_limit,
        )
    except Exception as exc:
        logger.warning(
            "AI quota increment Redis error for user=%s — allowing request: %s",
            current_user.id,
            exc,
        )

    return current_user
