from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MessageDeliveryStatus, MessageDirection, SenderType


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False, index=True)
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection), nullable=False, index=True)
    delivery_status: Mapped[MessageDeliveryStatus] = mapped_column(
        Enum(MessageDeliveryStatus), default=MessageDeliveryStatus.PENDING, nullable=False, index=True
    )
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")
    created_by_user = relationship("User", back_populates="messages")
