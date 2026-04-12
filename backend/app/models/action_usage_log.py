from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ActionUsageType, PlatformType


class ActionUsageLog(TimestampMixin, Base):
    __tablename__ = "action_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(ForeignKey("platform_connections.id"), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action_type: Mapped[ActionUsageType] = mapped_column(Enum(ActionUsageType), nullable=False, index=True)
    platform_type: Mapped[PlatformType | None] = mapped_column(Enum(PlatformType), nullable=True, index=True)
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 4), default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="action_usage_logs")
    platform_connection = relationship("PlatformConnection", back_populates="action_usage_logs")
    actor_user = relationship("User", back_populates="action_usage_logs")
