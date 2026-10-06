import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base


class UserHolding(Base):
    __tablename__ = "user_holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tradingsymbol: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(20), default="NSE", nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    pnl_percentage: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cap_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")
