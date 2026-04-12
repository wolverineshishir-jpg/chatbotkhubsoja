from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LLMTokenUsage(TimestampMixin, Base):
    __tablename__ = "llm_token_usage"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(ForeignKey("platform_connections.id"), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="llm_token_usage_entries")
    platform_connection = relationship("PlatformConnection", back_populates="llm_token_usage_entries")
    actor_user = relationship("User", back_populates="llm_token_usage_entries")
