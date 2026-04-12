from sqlalchemy import Boolean, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole, UserStatus


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    user_role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ADMIN, nullable=False, index=True)
    managed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    permissions_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    account_users = relationship("AccountUser", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    managed_by_user = relationship("User", remote_side="User.id", back_populates="managed_users")
    managed_users = relationship("User", back_populates="managed_by_user")
    assigned_conversations = relationship("Conversation", back_populates="assigned_to_user")
    assigned_facebook_comments = relationship("FacebookComment", back_populates="assigned_to_user")
    facebook_comment_replies = relationship("FacebookCommentReply", back_populates="created_by_user")
    created_social_posts = relationship("SocialPost", back_populates="created_by_user", foreign_keys="SocialPost.created_by_user_id")
    approved_social_posts = relationship("SocialPost", back_populates="approved_by_user", foreign_keys="SocialPost.approved_by_user_id")
    rejected_social_posts = relationship("SocialPost", back_populates="rejected_by_user", foreign_keys="SocialPost.rejected_by_user_id")
    messages = relationship("Message", back_populates="created_by_user")
    action_usage_logs = relationship("ActionUsageLog", back_populates="actor_user")
    llm_token_usage_entries = relationship("LLMTokenUsage", back_populates="actor_user")
    audit_logs = relationship("AuditLog", back_populates="actor_user")
