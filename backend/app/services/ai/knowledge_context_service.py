from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.ai_knowledge_source import AIKnowledgeSource
from app.models.enums import KnowledgeSourceStatus
from app.models.faq_knowledge import FAQKnowledge


class KnowledgeContextService:
    def __init__(self, db: Session):
        self.db = db

    def build_context(self, *, account_id: int, ai_agent_id: int | None, limit: int = 8) -> tuple[str, dict]:
        faq_rows = self.db.scalars(
            select(FAQKnowledge)
            .where(
                FAQKnowledge.account_id == account_id,
                FAQKnowledge.is_active.is_(True),
                or_(FAQKnowledge.ai_agent_id.is_(None), FAQKnowledge.ai_agent_id == ai_agent_id),
            )
            .order_by(FAQKnowledge.updated_at.desc())
            .limit(limit)
        ).all()
        knowledge_rows = self.db.scalars(
            select(AIKnowledgeSource)
            .where(
                AIKnowledgeSource.account_id == account_id,
                AIKnowledgeSource.status == KnowledgeSourceStatus.READY,
                or_(AIKnowledgeSource.ai_agent_id.is_(None), AIKnowledgeSource.ai_agent_id == ai_agent_id),
            )
            .order_by(AIKnowledgeSource.updated_at.desc())
            .limit(limit)
        ).all()

        faq_lines = [f"Q: {row.question}\nA: {row.answer}" for row in faq_rows]
        knowledge_lines: list[str] = []
        for row in knowledge_rows:
            if row.content_text:
                trimmed = row.content_text.strip()
                if trimmed:
                    knowledge_lines.append(f"{row.title}: {trimmed[:700]}")

        sections: list[str] = []
        if faq_lines:
            sections.append("FAQ\n" + "\n\n".join(faq_lines))
        if knowledge_lines:
            sections.append("KNOWLEDGE\n" + "\n\n".join(knowledge_lines))

        return (
            "\n\n".join(sections),
            {
                "faq_count": len(faq_rows),
                "knowledge_source_count": len(knowledge_rows),
            },
        )
