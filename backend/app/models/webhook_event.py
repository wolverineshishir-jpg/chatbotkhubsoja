from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import PlatformType, WebhookEventSource, WebhookEventStatus


class WebhookEvent(TimestampMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("event_key", name="uq_webhook_events_event_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"),
        nullable=True,
        index=True,
    )
    platform_type: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False, index=True)
    source: Mapped[WebhookEventSource] = mapped_column(Enum(WebhookEventSource), nullable=False, index=True)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus),
        default=WebhookEventStatus.PENDING,
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    headers_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="webhook_events")
    platform_connection = relationship("PlatformConnection", back_populates="webhook_events")
