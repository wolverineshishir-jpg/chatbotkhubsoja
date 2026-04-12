from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import CommentReplyStatus, SenderType


class FacebookCommentReply(TimestampMixin, Base):
    __tablename__ = "facebook_comment_replies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("facebook_comments.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False, index=True)
    reply_status: Mapped[CommentReplyStatus] = mapped_column(
        Enum(CommentReplyStatus), default=CommentReplyStatus.DRAFT, nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    external_reply_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="facebook_comment_replies")
    comment = relationship("FacebookComment", back_populates="replies")
    created_by_user = relationship("User", back_populates="facebook_comment_replies")
