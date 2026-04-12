from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import AIAgentStatus


class AIAgent(TimestampMixin, Base):
    __tablename__ = "ai_agents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AIAgentStatus] = mapped_column(Enum(AIAgentStatus), default=AIAgentStatus.DRAFT, nullable=False)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    behavior_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="ai_agents")
    platform_connection = relationship("PlatformConnection", back_populates="ai_agents")
    automation_workflows = relationship("AutomationWorkflow", back_populates="ai_agent")
    prompts = relationship("AIPrompt", back_populates="ai_agent", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="ai_agent")
    knowledge_sources = relationship("AIKnowledgeSource", back_populates="ai_agent", cascade="all, delete-orphan")
    faq_entries = relationship("FAQKnowledge", back_populates="ai_agent", cascade="all, delete-orphan")
