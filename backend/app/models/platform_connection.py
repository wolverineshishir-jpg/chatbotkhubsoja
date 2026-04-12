from sqlalchemy import Boolean, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ConnectionStatus, PlatformType


class PlatformConnection(TimestampMixin, Base):
    __tablename__ = "platform_connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_type: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    external_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False
    )
    encrypted_access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    token_hint: Mapped[str | None] = mapped_column(String(16), nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    webhook_verify_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    webhook_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    account = relationship("Account", back_populates="platform_connections")
    conversations = relationship("Conversation", back_populates="platform_connection")
    facebook_comments = relationship("FacebookComment", back_populates="platform_connection")
    social_posts = relationship("SocialPost", back_populates="platform_connection")
    ai_agents = relationship("AIAgent", back_populates="platform_connection")
    automation_workflows = relationship("AutomationWorkflow", back_populates="platform_connection")
    prompts = relationship("AIPrompt", back_populates="platform_connection")
    webhook_events = relationship("WebhookEvent", back_populates="platform_connection")
    sync_jobs = relationship("SyncJob", back_populates="platform_connection")
    action_usage_logs = relationship("ActionUsageLog", back_populates="platform_connection")
    llm_token_usage_entries = relationship("LLMTokenUsage", back_populates="platform_connection")
