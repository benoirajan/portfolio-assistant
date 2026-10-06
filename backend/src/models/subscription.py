import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base


class Subscription(Base):
    """Tracks SaaS subscription billing records per user.

    Stores Razorpay order/payment IDs, billing period dates, and webhook
    idempotency keys. One active record per user; historical records are kept
    for audit purposes via the status column.
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tier being subscribed to: FREE | PRO | ELITE
    plan_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="FREE"
    )

    # Razorpay identifiers (null until payment is attempted)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    # Populated only when using Razorpay Subscriptions (future UPI Autopay)
    razorpay_sub_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # active | cancelled | expired | pending
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="active"
    )

    # Billing period window dates
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Webhook idempotency — prevents duplicate tier upgrades from replayed webhooks
    webhook_event_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship back to User (lazy loads fine; no cascade needed here)
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")  # type: ignore[name-defined]
