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
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.security import get_current_user
from src.db.session import get_db, get_db_session
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


def _check_and_consume_db(current_user: User, db: Session) -> User:
    tier = (current_user.tier or "FREE").upper()
    quota_limit: int = settings.TIER_AI_QUOTA.get(tier, 3)
    now = datetime.now(timezone.utc)

    # Lock user row for atomic check-and-increment (SELECT ... FOR UPDATE)
    try:
        user = db.execute(
            select(User).where(User.id == current_user.id).with_for_update()
        ).scalar_one_or_none()
    except Exception as exc:
        # In case DB is temporarily unreachable or SQLite doesn't support lock
        logger.warning(
            "AI quota DB lock error for user=%s — falling back to standard query: %s",
            current_user.id,
            exc,
        )
        user = db.execute(select(User).where(User.id == current_user.id)).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    reset_at = user.ai_quota_reset_at
    if reset_at is not None and reset_at.tzinfo is None:
        reset_at = reset_at.replace(tzinfo=timezone.utc)

    # Natural window reset: first query ever or 30 days elapsed since window start
    if reset_at is None or now >= reset_at:
        user.ai_quota_used = 0
        user.ai_quota_reset_at = now + timedelta(days=30)
        reset_at = user.ai_quota_reset_at

    # Check quota limit
    if user.ai_quota_used >= quota_limit:
        resets_in = (
            max(0, int((reset_at - now).total_seconds()))
            if reset_at
            else 0
        )
        logger.info(
            "AI quota exhausted — user=%s tier=%s used=%d limit=%d resets_in=%ds",
            user.id,
            tier,
            user.ai_quota_used,
            quota_limit,
            resets_in,
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
                "X-Quota-Used": str(user.ai_quota_used),
                "X-Quota-Reset": str(resets_in),
                "X-Required-Tier": "PRO" if tier == "FREE" else "ELITE",
            },
        )

    # Increment quota — ai_quota_reset_at is deliberately NOT touched (prevents sliding window bug)
    user.ai_quota_used += 1
    db.commit()

    logger.info(
        "AI quota consumed — user=%s tier=%s used=%d/%d resets_at=%s",
        user.id,
        tier,
        user.ai_quota_used,
        quota_limit,
        user.ai_quota_reset_at,
    )
    return user


def check_and_consume_ai_quota(
    current_user: User = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
) -> User:
    """FastAPI dependency: checks and atomically increments monthly Gemini AI quota in PostgreSQL.

    Quota is stored directly in PostgreSQL on the `users` table:
    - `ai_quota_used`: count of runs consumed in the active cycle.
    - `ai_quota_reset_at`: fixed 30-day window anchor (set on first query or tier upgrade).

    Consecutive queries within the 30-day window increment `ai_quota_used` without
    shifting `ai_quota_reset_at`, eliminating the sliding window bug.
    Once `now >= ai_quota_reset_at`, the counter resets naturally to 0.

    Raises:
        HTTP 429 when the user's monthly AI run quota is exhausted.
    """
    if db is None:
        with get_db_session() as session:
            return _check_and_consume_db(current_user, session)
    return _check_and_consume_db(current_user, db)
