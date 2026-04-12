from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import KnowledgeSourceStatus, KnowledgeSourceType


class AIKnowledgeSource(TimestampMixin, Base):
    __tablename__ = "ai_knowledge_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    ai_agent_id: Mapped[int | None] = mapped_column(ForeignKey("ai_agents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[KnowledgeSourceType] = mapped_column(Enum(KnowledgeSourceType), nullable=False)
    status: Mapped[KnowledgeSourceStatus] = mapped_column(
        Enum(KnowledgeSourceStatus), default=KnowledgeSourceStatus.DRAFT, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="knowledge_sources")
    ai_agent = relationship("AIAgent", back_populates="knowledge_sources")
