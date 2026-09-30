import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="Default Portfolio", nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False, unique=True)
    total_investment: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_pnl_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    raw_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="portfolios")
    holdings: Mapped[List["UserHolding"]] = relationship(
        "UserHolding", back_populates="portfolio", cascade="all, delete-orphan"
    )
