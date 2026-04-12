"""social posts

Revision ID: 20260408_000006
Revises: 20260408_000005
Create Date: 2026-04-09 03:15:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000006"
down_revision = "20260408_000005"
branch_labels = None
depends_on = None

post_status_enum = sa.Enum("DRAFT", "APPROVED", "SCHEDULED", "PUBLISHED", "FAILED", "REJECTED", name="poststatus")
post_generated_by_enum = sa.Enum("HUMAN_ADMIN", "LLM_BOT", "SYSTEM", name="postgeneratedby")


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("ai_agent_id", sa.Integer(), nullable=True),
        sa.Column("ai_prompt_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rejected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("platform_type", sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype"), nullable=False),
        sa.Column("status", post_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("generated_by", post_generated_by_enum, nullable=False, server_default="HUMAN_ADMIN"),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_urls", sa.JSON(), nullable=False),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("is_llm_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_social_posts_account_id_accounts")),
        sa.ForeignKeyConstraint(["ai_agent_id"], ["ai_agents.id"], name=op.f("fk_social_posts_ai_agent_id_ai_agents")),
        sa.ForeignKeyConstraint(["ai_prompt_id"], ["ai_prompts.id"], name=op.f("fk_social_posts_ai_prompt_id_ai_prompts")),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], name=op.f("fk_social_posts_approved_by_user_id_users")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_social_posts_created_by_user_id_users")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_social_posts_platform_connection_id_platform_connections"),
        ),
        sa.ForeignKeyConstraint(["rejected_by_user_id"], ["users.id"], name=op.f("fk_social_posts_rejected_by_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_social_posts")),
    )
    op.create_index(op.f("ix_social_posts_account_id"), "social_posts", ["account_id"], unique=False)
    op.create_index(op.f("ix_social_posts_ai_agent_id"), "social_posts", ["ai_agent_id"], unique=False)
    op.create_index(op.f("ix_social_posts_ai_prompt_id"), "social_posts", ["ai_prompt_id"], unique=False)
    op.create_index(op.f("ix_social_posts_approved_by_user_id"), "social_posts", ["approved_by_user_id"], unique=False)
    op.create_index(op.f("ix_social_posts_created_by_user_id"), "social_posts", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_social_posts_external_post_id"), "social_posts", ["external_post_id"], unique=False)
    op.create_index(op.f("ix_social_posts_id"), "social_posts", ["id"], unique=False)
    op.create_index(op.f("ix_social_posts_platform_connection_id"), "social_posts", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_social_posts_platform_type"), "social_posts", ["platform_type"], unique=False)
    op.create_index(op.f("ix_social_posts_rejected_by_user_id"), "social_posts", ["rejected_by_user_id"], unique=False)
    op.create_index(op.f("ix_social_posts_scheduled_for"), "social_posts", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_social_posts_status"), "social_posts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_posts_status"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_scheduled_for"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_rejected_by_user_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_platform_type"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_platform_connection_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_external_post_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_created_by_user_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_approved_by_user_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_ai_prompt_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_ai_agent_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_account_id"), table_name="social_posts")
    op.drop_table("social_posts")

    post_generated_by_enum.drop(op.get_bind(), checkfirst=False)
    post_status_enum.drop(op.get_bind(), checkfirst=False)
