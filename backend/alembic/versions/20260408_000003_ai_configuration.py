"""ai configuration

Revision ID: 20260408_000003
Revises: 20260408_000002
Create Date: 2026-04-09 00:10:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000003"
down_revision = "20260408_000002"
branch_labels = None
depends_on = None

ai_agent_status_enum = sa.Enum("DRAFT", "ACTIVE", "PAUSED", "ARCHIVED", name="aiagentstatus")
prompt_type_enum = sa.Enum(
    "SYSTEM_INSTRUCTION",
    "INBOX_REPLY",
    "COMMENT_REPLY",
    "POST_GENERATION",
    name="prompttype",
)
knowledge_source_status_enum = sa.Enum("DRAFT", "READY", "PROCESSING", "ARCHIVED", name="knowledgesourcestatus")
knowledge_source_type_enum = sa.Enum("FILE", "URL", "TEXT", name="knowledgesourcetype")


def upgrade() -> None:
    op.create_table(
        "ai_agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("business_type", sa.String(length=255), nullable=True),
        sa.Column("status", ai_agent_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("behavior_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_ai_agents_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_ai_agents_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_agents")),
    )
    op.create_index(op.f("ix_ai_agents_account_id"), "ai_agents", ["account_id"], unique=False)
    op.create_index(op.f("ix_ai_agents_id"), "ai_agents", ["id"], unique=False)
    op.create_index(op.f("ix_ai_agents_platform_connection_id"), "ai_agents", ["platform_connection_id"], unique=False)

    op.create_table(
        "ai_prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("ai_agent_id", sa.Integer(), nullable=True),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("prompt_type", prompt_type_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_ai_prompts_account_id_accounts")),
        sa.ForeignKeyConstraint(["ai_agent_id"], ["ai_agents.id"], name=op.f("fk_ai_prompts_ai_agent_id_ai_agents")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_ai_prompts_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_prompts")),
    )
    op.create_index(op.f("ix_ai_prompts_account_id"), "ai_prompts", ["account_id"], unique=False)
    op.create_index(op.f("ix_ai_prompts_ai_agent_id"), "ai_prompts", ["ai_agent_id"], unique=False)
    op.create_index(op.f("ix_ai_prompts_id"), "ai_prompts", ["id"], unique=False)
    op.create_index(op.f("ix_ai_prompts_platform_connection_id"), "ai_prompts", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_ai_prompts_prompt_type"), "ai_prompts", ["prompt_type"], unique=False)

    op.create_table(
        "ai_knowledge_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("ai_agent_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", knowledge_source_type_enum, nullable=False),
        sa.Column("status", knowledge_source_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_ai_knowledge_sources_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["ai_agent_id"], ["ai_agents.id"], name=op.f("fk_ai_knowledge_sources_ai_agent_id_ai_agents")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge_sources")),
    )
    op.create_index(op.f("ix_ai_knowledge_sources_account_id"), "ai_knowledge_sources", ["account_id"], unique=False)
    op.create_index(op.f("ix_ai_knowledge_sources_ai_agent_id"), "ai_knowledge_sources", ["ai_agent_id"], unique=False)
    op.create_index(op.f("ix_ai_knowledge_sources_id"), "ai_knowledge_sources", ["id"], unique=False)

    op.create_table(
        "faq_knowledge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("ai_agent_id", sa.Integer(), nullable=True),
        sa.Column("question", sa.String(length=500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_faq_knowledge_account_id_accounts")),
        sa.ForeignKeyConstraint(["ai_agent_id"], ["ai_agents.id"], name=op.f("fk_faq_knowledge_ai_agent_id_ai_agents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_faq_knowledge")),
    )
    op.create_index(op.f("ix_faq_knowledge_account_id"), "faq_knowledge", ["account_id"], unique=False)
    op.create_index(op.f("ix_faq_knowledge_ai_agent_id"), "faq_knowledge", ["ai_agent_id"], unique=False)
    op.create_index(op.f("ix_faq_knowledge_id"), "faq_knowledge", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_faq_knowledge_id"), table_name="faq_knowledge")
    op.drop_index(op.f("ix_faq_knowledge_ai_agent_id"), table_name="faq_knowledge")
    op.drop_index(op.f("ix_faq_knowledge_account_id"), table_name="faq_knowledge")
    op.drop_table("faq_knowledge")

    op.drop_index(op.f("ix_ai_knowledge_sources_id"), table_name="ai_knowledge_sources")
    op.drop_index(op.f("ix_ai_knowledge_sources_ai_agent_id"), table_name="ai_knowledge_sources")
    op.drop_index(op.f("ix_ai_knowledge_sources_account_id"), table_name="ai_knowledge_sources")
    op.drop_table("ai_knowledge_sources")

    op.drop_index(op.f("ix_ai_prompts_prompt_type"), table_name="ai_prompts")
    op.drop_index(op.f("ix_ai_prompts_platform_connection_id"), table_name="ai_prompts")
    op.drop_index(op.f("ix_ai_prompts_id"), table_name="ai_prompts")
    op.drop_index(op.f("ix_ai_prompts_ai_agent_id"), table_name="ai_prompts")
    op.drop_index(op.f("ix_ai_prompts_account_id"), table_name="ai_prompts")
    op.drop_table("ai_prompts")

    op.drop_index(op.f("ix_ai_agents_platform_connection_id"), table_name="ai_agents")
    op.drop_index(op.f("ix_ai_agents_id"), table_name="ai_agents")
    op.drop_index(op.f("ix_ai_agents_account_id"), table_name="ai_agents")
    op.drop_table("ai_agents")

    knowledge_source_type_enum.drop(op.get_bind(), checkfirst=False)
    knowledge_source_status_enum.drop(op.get_bind(), checkfirst=False)
    prompt_type_enum.drop(op.get_bind(), checkfirst=False)
    ai_agent_status_enum.drop(op.get_bind(), checkfirst=False)
