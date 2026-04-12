from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FAQKnowledge(TimestampMixin, Base):
    __tablename__ = "faq_knowledge"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    ai_agent_id: Mapped[int | None] = mapped_column(ForeignKey("ai_agents.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    account = relationship("Account", back_populates="faq_entries")
    ai_agent = relationship("AIAgent", back_populates="faq_entries")
