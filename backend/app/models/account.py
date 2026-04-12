from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_token_credit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_credit_last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_credit_next_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    memberships = relationship("Membership", back_populates="account", cascade="all, delete-orphan")
    account_users = relationship("AccountUser", back_populates="account", cascade="all, delete-orphan")
    onboarding_keys = relationship("OnboardingKey", back_populates="account", cascade="all, delete-orphan")
    platform_connections = relationship(
        "PlatformConnection", back_populates="account", cascade="all, delete-orphan"
    )
    conversations = relationship("Conversation", back_populates="account", cascade="all, delete-orphan")
    facebook_comments = relationship("FacebookComment", back_populates="account", cascade="all, delete-orphan")
    facebook_comment_replies = relationship(
        "FacebookCommentReply", back_populates="account", cascade="all, delete-orphan"
    )
    social_posts = relationship("SocialPost", back_populates="account", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="account", cascade="all, delete-orphan")
    ai_agents = relationship("AIAgent", back_populates="account", cascade="all, delete-orphan")
    automation_workflows = relationship("AutomationWorkflow", back_populates="account", cascade="all, delete-orphan")
    ai_prompts = relationship("AIPrompt", back_populates="account", cascade="all, delete-orphan")
    knowledge_sources = relationship("AIKnowledgeSource", back_populates="account", cascade="all, delete-orphan")
    faq_entries = relationship("FAQKnowledge", back_populates="account", cascade="all, delete-orphan")
    webhook_events = relationship("WebhookEvent", back_populates="account", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="account", cascade="all, delete-orphan")
    action_usage_logs = relationship("ActionUsageLog", back_populates="account", cascade="all, delete-orphan")
    llm_token_usage_entries = relationship("LLMTokenUsage", back_populates="account", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="account", cascade="all, delete-orphan")
    subscriptions = relationship("AccountSubscription", back_populates="account", cascade="all, delete-orphan")
    token_wallets = relationship("TokenWallet", back_populates="account", cascade="all, delete-orphan")
    token_ledger_entries = relationship("TokenLedger", back_populates="account", cascade="all, delete-orphan")
    billing_transactions = relationship("BillingTransaction", back_populates="account", cascade="all, delete-orphan")
