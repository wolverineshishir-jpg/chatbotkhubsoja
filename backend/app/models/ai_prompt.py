from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import PromptType


class AIPrompt(TimestampMixin, Base):
    __tablename__ = "ai_prompts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    ai_agent_id: Mapped[int | None] = mapped_column(ForeignKey("ai_agents.id"), nullable=True, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"), nullable=True, index=True
    )
    prompt_type: Mapped[PromptType] = mapped_column(Enum(PromptType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    account = relationship("Account", back_populates="ai_prompts")
    ai_agent = relationship("AIAgent", back_populates="prompts")
    platform_connection = relationship("PlatformConnection", back_populates="prompts")
    social_posts = relationship("SocialPost", back_populates="ai_prompt")
