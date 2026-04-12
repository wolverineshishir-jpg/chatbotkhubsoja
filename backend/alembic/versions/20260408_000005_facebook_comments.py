"""facebook comments moderation

Revision ID: 20260408_000005
Revises: 20260408_000004
Create Date: 2026-04-09 02:20:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000005"
down_revision = "20260408_000004"
branch_labels = None
depends_on = None

comment_status_enum = sa.Enum("PENDING", "REPLIED", "IGNORED", "FLAGGED", "NEED_REVIEW", name="commentstatus")
comment_reply_status_enum = sa.Enum("DRAFT", "QUEUED", "SENT", "FAILED", name="commentreplystatus")


def upgrade() -> None:
    op.create_table(
        "facebook_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("platform_type", sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype"), nullable=False),
        sa.Column("status", comment_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("post_external_id", sa.String(length=255), nullable=False),
        sa.Column("post_title", sa.String(length=255), nullable=True),
        sa.Column("post_url", sa.String(length=500), nullable=True),
        sa.Column("external_comment_id", sa.String(length=255), nullable=False),
        sa.Column("parent_external_comment_id", sa.String(length=255), nullable=True),
        sa.Column("commenter_external_id", sa.String(length=255), nullable=False),
        sa.Column("commenter_name", sa.String(length=255), nullable=True),
        sa.Column("commenter_avatar_url", sa.String(length=500), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("ai_draft_reply", sa.Text(), nullable=True),
        sa.Column("flagged_reason", sa.String(length=500), nullable=True),
        sa.Column("moderation_notes", sa.String(length=1000), nullable=True),
        sa.Column("commented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_facebook_comments_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"], ["users.id"], name=op.f("fk_facebook_comments_assigned_to_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_facebook_comments_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facebook_comments")),
    )
    op.create_index(op.f("ix_facebook_comments_account_id"), "facebook_comments", ["account_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_assigned_to_user_id"), "facebook_comments", ["assigned_to_user_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_commenter_external_id"), "facebook_comments", ["commenter_external_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_commenter_name"), "facebook_comments", ["commenter_name"], unique=False)
    op.create_index(op.f("ix_facebook_comments_commented_at"), "facebook_comments", ["commented_at"], unique=False)
    op.create_index(op.f("ix_facebook_comments_external_comment_id"), "facebook_comments", ["external_comment_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_id"), "facebook_comments", ["id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_parent_external_comment_id"), "facebook_comments", ["parent_external_comment_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_platform_connection_id"), "facebook_comments", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_platform_type"), "facebook_comments", ["platform_type"], unique=False)
    op.create_index(op.f("ix_facebook_comments_post_external_id"), "facebook_comments", ["post_external_id"], unique=False)
    op.create_index(op.f("ix_facebook_comments_status"), "facebook_comments", ["status"], unique=False)

    op.create_table(
        "facebook_comment_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sender_type", sa.Enum("CUSTOMER", "LLM_BOT", "HUMAN_ADMIN", "SYSTEM", name="sendertype"), nullable=False),
        sa.Column("reply_status", comment_reply_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("external_reply_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_facebook_comment_replies_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["comment_id"], ["facebook_comments.id"], name=op.f("fk_facebook_comment_replies_comment_id_facebook_comments")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name=op.f("fk_facebook_comment_replies_created_by_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facebook_comment_replies")),
    )
    op.create_index(op.f("ix_facebook_comment_replies_account_id"), "facebook_comment_replies", ["account_id"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_comment_id"), "facebook_comment_replies", ["comment_id"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_created_by_user_id"), "facebook_comment_replies", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_external_reply_id"), "facebook_comment_replies", ["external_reply_id"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_id"), "facebook_comment_replies", ["id"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_reply_status"), "facebook_comment_replies", ["reply_status"], unique=False)
    op.create_index(op.f("ix_facebook_comment_replies_sender_type"), "facebook_comment_replies", ["sender_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_facebook_comment_replies_sender_type"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_reply_status"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_id"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_external_reply_id"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_created_by_user_id"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_comment_id"), table_name="facebook_comment_replies")
    op.drop_index(op.f("ix_facebook_comment_replies_account_id"), table_name="facebook_comment_replies")
    op.drop_table("facebook_comment_replies")

    op.drop_index(op.f("ix_facebook_comments_status"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_post_external_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_platform_type"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_platform_connection_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_parent_external_comment_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_external_comment_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_commented_at"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_commenter_name"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_commenter_external_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_assigned_to_user_id"), table_name="facebook_comments")
    op.drop_index(op.f("ix_facebook_comments_account_id"), table_name="facebook_comments")
    op.drop_table("facebook_comments")

    comment_reply_status_enum.drop(op.get_bind(), checkfirst=False)
    comment_status_enum.drop(op.get_bind(), checkfirst=False)
