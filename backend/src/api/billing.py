"""
Billing API — SaaS Monetization, Tier Management & Razorpay Payment Integration.

Endpoints:
    GET  /api/v1/billing/plans           List tier definitions & pricing
    POST /api/v1/billing/create-order    Create Razorpay order for tier upgrade
    POST /api/v1/billing/verify-payment  Verify payment signature & upgrade tier
    GET  /api/v1/billing/status          Current subscription status
    POST /api/v1/billing/webhook         Razorpay webhook handler (HMAC verified)
    GET  /api/v1/billing/quota           Current AI quota usage

NOTE — Mock Mode:
    When RAZORPAY_MOCK_MODE=true (the default), this module stubs all Razorpay
    API calls so the full billing/gating flow works locally without real keys.
    Set RAZORPAY_MOCK_MODE=false and supply real RAZORPAY_KEY_ID / KEY_SECRET
    once you have a live Razorpay account.

    TODO: Integrate live Razorpay keys (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
          when a Razorpay account is provisioned.
          See docs/plans/todo_tomorrow_tasks.md for tracking.
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from src.core import cache
from src.core.config import settings
from src.core.security import get_current_user
from src.db.session import get_db_session
from src.models.subscription import Subscription
from src.models.user import User

logger = logging.getLogger("portfolio_assistant.api.billing")
router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])

# ---------------------------------------------------------------------------
# Tier definitions (single source of truth for pricing & feature labels)
# ---------------------------------------------------------------------------

TIER_DEFINITIONS = [
    {
        "tier": "FREE",
        "price_inr": 0,
        "price_paise": 0,
        "ai_runs_per_month": settings.TIER_AI_QUOTA["FREE"],
        "features": [
            "Rule-based advisory engine",
            "1 broker connection (Zerodha)",
            f"{settings.TIER_AI_QUOTA['FREE']} Gemini AI advisory runs / month",
            "Portfolio analytics (XIRR, Sharpe)",
            "Holdings & sector breakdown",
        ],
        "highlight": False,
    },
    {
        "tier": "PRO",
        "price_inr": 299,
        "price_paise": settings.TIER_PRICE_PAISE["PRO"],
        "ai_runs_per_month": settings.TIER_AI_QUOTA["PRO"],
        "features": [
            "Everything in Free",
            f"{settings.TIER_AI_QUOTA['PRO']} Gemini AI advisory runs / month",
            "3-Stage AI Advisory Pipeline",
            "Tax-loss harvesting analysis",
            "1-click Zerodha basket export",
            # TODO: Multi-broker support (future — track in todo_tomorrow_tasks.md)
        ],
        "highlight": True,  # Most popular — shown with a CTA badge in UI
    },
    {
        "tier": "ELITE",
        "price_inr": 799,
        "price_paise": settings.TIER_PRICE_PAISE["ELITE"],
        "ai_runs_per_month": settings.TIER_AI_QUOTA["ELITE"],
        "features": [
            "Everything in Pro",
            "Unlimited Gemini AI advisory runs",
            "Priority support",
            "Early access to new features",
        ],
        "highlight": False,
    },
]


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CreateOrderPayload(BaseModel):
    target_tier: str  # "PRO" | "ELITE"


class VerifyPaymentPayload(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    target_tier: str


class BillingStatusResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[str]
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mock_create_order(target_tier: str, amount_paise: int) -> dict:
    """Returns a mock Razorpay order payload for local development."""
    return {
        "id": f"order_MOCK_{uuid.uuid4().hex[:12].upper()}",
        "amount": amount_paise,
        "currency": "INR",
        "status": "created",
        "mock": True,
    }


def _real_create_order(target_tier: str, amount_paise: int) -> dict:
    """Creates a real Razorpay order using the Razorpay Python SDK."""
    import razorpay  # type: ignore[import]
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "notes": {"target_tier": target_tier},
        }
    )
    return order


def _verify_razorpay_signature(
    order_id: str, payment_id: str, signature: str
) -> bool:
    """Verifies Razorpay HMAC-SHA256 payment signature."""
    if settings.RAZORPAY_MOCK_MODE:
        # Accept any signature in mock mode
        return True
    msg = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_webhook_signature(body_bytes: bytes, signature: str) -> bool:
    """Verifies Razorpay webhook HMAC-SHA256 signature."""
    if settings.RAZORPAY_MOCK_MODE:
        return True
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _upgrade_user_tier(db_session, user: User, target_tier: str, order_id: str, payment_id: str) -> None:
    """Upgrades user tier in DB and upserts subscription record. Must be called inside an open db session."""
    # Update user tier
    db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one_or_none()
    if db_user:
        db_user.tier = target_tier.upper()

    # Upsert subscription record
    existing_sub = db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)

    if existing_sub:
        existing_sub.plan_type = target_tier.upper()
        existing_sub.razorpay_order_id = order_id
        existing_sub.razorpay_payment_id = payment_id
        existing_sub.status = "active"
        existing_sub.current_period_start = now
        existing_sub.current_period_end = period_end
        existing_sub.updated_at = now
    else:
        new_sub = Subscription(
            user_id=user.id,
            plan_type=target_tier.upper(),
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            status="active",
            current_period_start=now,
            current_period_end=period_end,
        )
        db_session.add(new_sub)

    # Reset AI quota counter so the new tier's limit kicks in immediately
    cache.delete(f"quota:ai:{user.id}")

    logger.info(
        "User tier upgraded — user=%s new_tier=%s order=%s payment=%s",
        user.id,
        target_tier.upper(),
        order_id,
        payment_id,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/plans")
def list_plans():
    """Returns all available subscription tiers with pricing and feature lists."""
    return {
        "status": "success",
        "mock_mode": settings.RAZORPAY_MOCK_MODE,
        "plans": TIER_DEFINITIONS,
    }


@router.post("/create-order")
def create_order(
    payload: CreateOrderPayload,
    current_user: User = Depends(get_current_user),
):
    """Creates a Razorpay payment order for a tier upgrade.

    In mock mode (RAZORPAY_MOCK_MODE=true) returns a synthetic order ID so the
    full checkout flow can be tested locally without a Razorpay account.
    """
    target_tier = payload.target_tier.upper()
    if target_tier not in ("PRO", "ELITE"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_tier must be PRO or ELITE",
        )

    if target_tier == (current_user.tier or "FREE").upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already on the {target_tier} plan.",
        )

    amount_paise = settings.TIER_PRICE_PAISE.get(target_tier, 0)

    try:
        if settings.RAZORPAY_MOCK_MODE:
            logger.info(
                "Mock Razorpay order for user=%s tier=%s amount=%d paise",
                current_user.id,
                target_tier,
                amount_paise,
            )
            order = _mock_create_order(target_tier, amount_paise)
        else:
            order = _real_create_order(target_tier, amount_paise)
    except Exception as exc:
        logger.error("Razorpay order creation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        )

    return {
        "status": "success",
        "razorpay_order_id": order["id"],
        "amount": order["amount"],
        "currency": order.get("currency", "INR"),
        "key_id": settings.RAZORPAY_KEY_ID,
        "mock_mode": settings.RAZORPAY_MOCK_MODE,
        "target_tier": target_tier,
    }


@router.post("/verify-payment")
def verify_payment(
    payload: VerifyPaymentPayload,
    current_user: User = Depends(get_current_user),
):
    """Verifies Razorpay payment HMAC signature and upgrades the user's tier.

    In mock mode, any non-empty signature is accepted so the flow can be tested
    end-to-end without real Razorpay keys.
    """
    target_tier = payload.target_tier.upper()
    if target_tier not in ("PRO", "ELITE"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_tier must be PRO or ELITE",
        )

    sig_valid = _verify_razorpay_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    )
    if not sig_valid:
        logger.warning(
            "Invalid Razorpay signature — user=%s order=%s",
            current_user.id,
            payload.razorpay_order_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed. Transaction may be tampered.",
        )

    with get_db_session() as db:
        _upgrade_user_tier(
            db,
            current_user,
            target_tier,
            payload.razorpay_order_id,
            payload.razorpay_payment_id,
        )

    return {
        "status": "success",
        "message": f"Congratulations! Your plan has been upgraded to {target_tier}.",
        "tier": target_tier,
        "mock_mode": settings.RAZORPAY_MOCK_MODE,
    }


@router.get("/status", response_model=BillingStatusResponse)
def get_billing_status(current_user: User = Depends(get_current_user)):
    """Returns the user's current subscription tier and billing record."""
    with get_db_session() as db:
        sub = db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        ).scalar_one_or_none()

    return BillingStatusResponse(
        tier=current_user.tier or "FREE",
        status=sub.status if sub else "active",
        current_period_end=sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        razorpay_order_id=sub.razorpay_order_id if sub else None,
        razorpay_payment_id=sub.razorpay_payment_id if sub else None,
    )


@router.get("/quota")
def get_ai_quota(current_user: User = Depends(get_current_user)):
    """Returns the user's current monthly Gemini AI advisory usage vs. quota."""
    tier = (current_user.tier or "FREE").upper()
    quota_limit: int = settings.TIER_AI_QUOTA.get(tier, 3)
    quota_key = f"quota:ai:{current_user.id}"

    try:
        current_count_raw = cache.get(quota_key)
        current_count = int(current_count_raw) if current_count_raw is not None else 0
    except Exception as exc:
        logger.warning("AI quota Redis read error for user=%s: %s", current_user.id, exc)
        current_count = 0

    return {
        "status": "success",
        "tier": tier,
        "used": current_count,
        "limit": quota_limit,
        "remaining": max(0, quota_limit - current_count),
    }


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """Razorpay webhook handler — processes payment & subscription lifecycle events.

    Validates the HMAC-SHA256 signature on all incoming webhook payloads.
    All upgrades are idempotent via the webhook_event_id field.

    Supported events:
        payment.captured    → upgrade user tier
        subscription.charged → (future) recurring renewal handling
        subscription.cancelled → (future) downgrade to FREE on cancellation
    """
    body_bytes = await request.body()

    if not _verify_webhook_signature(body_bytes, x_razorpay_signature or ""):
        logger.warning("Razorpay webhook signature mismatch — rejecting")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook signature verification failed",
        )

    try:
        event = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type: str = event.get("event", "")
    event_id: str = event.get("id", "")
    logger.info("Razorpay webhook received — event=%s id=%s", event_type, event_id)

    if event_type == "payment.captured":
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id", "")
        payment_id = payment_entity.get("id", "")
        notes = payment_entity.get("notes", {})
        target_tier = notes.get("target_tier", "PRO").upper()

        if not order_id:
            logger.warning("Webhook payment.captured missing order_id — skipping")
            return {"status": "ignored"}

        # Find user by subscription order_id (idempotency check)
        with get_db_session() as db:
            existing = db.execute(
                select(Subscription).where(
                    Subscription.razorpay_order_id == order_id
                )
            ).scalar_one_or_none()

            if existing and existing.webhook_event_id == event_id:
                logger.info("Webhook event %s already processed — idempotent skip", event_id)
                return {"status": "already_processed"}

            if existing:
                # Upgrade the user associated with this subscription
                user = db.execute(
                    select(User).where(User.id == existing.user_id)
                ).scalar_one_or_none()
                if user:
                    _upgrade_user_tier(db, user, target_tier, order_id, payment_id)
                    existing.webhook_event_id = event_id

    # Future: handle subscription.charged, subscription.cancelled
    # TODO: Implement recurring subscription lifecycle events when UPI Autopay is enabled.

    return {"status": "ok"}
