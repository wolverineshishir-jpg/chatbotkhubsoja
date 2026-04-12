from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import CommentStatus, PlatformType


class FacebookComment(TimestampMixin, Base):
    __tablename__ = "facebook_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"), nullable=True, index=True
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    platform_type: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False, index=True)
    status: Mapped[CommentStatus] = mapped_column(
        Enum(CommentStatus), default=CommentStatus.PENDING, nullable=False, index=True
    )
    post_external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    post_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    post_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_comment_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parent_external_comment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    commenter_external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    commenter_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    commenter_avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    moderation_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    commented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="facebook_comments")
    platform_connection = relationship("PlatformConnection", back_populates="facebook_comments")
    assigned_to_user = relationship("User", back_populates="assigned_facebook_comments")
    replies = relationship("FacebookCommentReply", back_populates="comment", cascade="all, delete-orphan")
