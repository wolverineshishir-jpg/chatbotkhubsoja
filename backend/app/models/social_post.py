from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import PostGeneratedBy, PostStatus, PlatformType


class SocialPost(TimestampMixin, Base):
    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"), nullable=True, index=True
    )
    ai_agent_id: Mapped[int | None] = mapped_column(ForeignKey("ai_agents.id"), nullable=True, index=True)
    ai_prompt_id: Mapped[int | None] = mapped_column(ForeignKey("ai_prompts.id"), nullable=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    rejected_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    platform_type: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False, index=True)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    generated_by: Mapped[PostGeneratedBy] = mapped_column(
        Enum(PostGeneratedBy), default=PostGeneratedBy.HUMAN_ADMIN, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_llm_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="social_posts")
    platform_connection = relationship("PlatformConnection", back_populates="social_posts")
    ai_agent = relationship("AIAgent", back_populates="social_posts")
    ai_prompt = relationship("AIPrompt", back_populates="social_posts")
    created_by_user = relationship("User", back_populates="created_social_posts", foreign_keys=[created_by_user_id])
    approved_by_user = relationship("User", back_populates="approved_social_posts", foreign_keys=[approved_by_user_id])
    rejected_by_user = relationship("User", back_populates="rejected_social_posts", foreign_keys=[rejected_by_user_id])
