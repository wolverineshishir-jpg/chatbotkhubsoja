from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ConversationStatus, PlatformType


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"), nullable=True, index=True
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    platform_type: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False, index=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False, index=True
    )
    external_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    customer_external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    customer_avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_message_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latest_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_inbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="conversations")
    platform_connection = relationship("PlatformConnection", back_populates="conversations")
    assigned_to_user = relationship("User", back_populates="assigned_conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
