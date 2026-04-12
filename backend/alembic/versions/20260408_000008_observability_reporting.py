"""observability and reporting basics

Revision ID: 20260408_000008
Revises: 20260408_000007
Create Date: 2026-04-09 06:10:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000008"
down_revision = "20260408_000007"
branch_labels = None
depends_on = None

action_usage_type_enum = sa.Enum(
    "INBOUND_MESSAGE",
    "OUTBOUND_MESSAGE",
    "COMMENT_REPLY",
    "POST_PUBLISH",
    "AI_REPLY_GENERATION",
    "TOKEN_CREDIT",
    "TOKEN_EXPIRATION",
    "ADMIN_ACTION",
    name="actionusagetype",
)
audit_action_type_enum = sa.Enum(
    "ADMIN_ACTION",
    "ACCOUNT_CREATED",
    "ACCOUNT_JOINED",
    "ONBOARDING_KEY_CREATED",
    "ONBOARDING_KEY_REVOKED",
    "CONNECTION_CREATED",
    "CONNECTION_UPDATED",
    "CONNECTION_STATUS_UPDATED",
    "CONNECTION_DISCONNECTED",
    "CONNECTION_DELETED",
    "CONVERSATION_ASSIGNED",
    "CONVERSATION_STATUS_UPDATED",
    "MESSAGE_REPLY_SENT",
    "COMMENT_STATUS_UPDATED",
    "COMMENT_REPLY_CREATED",
    "POST_CREATED",
    "POST_UPDATED",
    "POST_APPROVED",
    "POST_REJECTED",
    "POST_SCHEDULED",
    "POST_PUBLISH_NOW",
    "REPORT_VIEWED",
    name="auditactiontype",
)
audit_resource_type_enum = sa.Enum(
    "ACCOUNT",
    "PLATFORM_CONNECTION",
    "CONVERSATION",
    "MESSAGE",
    "FACEBOOK_COMMENT",
    "FACEBOOK_COMMENT_REPLY",
    "SOCIAL_POST",
    "REPORT",
    "TEAM",
    name="auditresourcetype",
)


def upgrade() -> None:
    op.create_table(
        "action_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", action_usage_type_enum, nullable=False),
        sa.Column("platform_type", sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype"), nullable=True),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tokens_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_action_usage_logs_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_action_usage_logs_actor_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_action_usage_logs_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_action_usage_logs")),
    )
    op.create_index(op.f("ix_action_usage_logs_account_id"), "action_usage_logs", ["account_id"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_action_type"), "action_usage_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_actor_user_id"), "action_usage_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_id"), "action_usage_logs", ["id"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_occurred_at"), "action_usage_logs", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_platform_connection_id"), "action_usage_logs", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_platform_type"), "action_usage_logs", ["platform_type"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_reference_id"), "action_usage_logs", ["reference_id"], unique=False)
    op.create_index(op.f("ix_action_usage_logs_reference_type"), "action_usage_logs", ["reference_type"], unique=False)

    op.create_table(
        "llm_token_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_llm_token_usage_account_id_accounts")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_llm_token_usage_actor_user_id_users")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_llm_token_usage_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_token_usage")),
    )
    op.create_index(op.f("ix_llm_token_usage_account_id"), "llm_token_usage", ["account_id"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_actor_user_id"), "llm_token_usage", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_feature_name"), "llm_token_usage", ["feature_name"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_id"), "llm_token_usage", ["id"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_model_name"), "llm_token_usage", ["model_name"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_platform_connection_id"), "llm_token_usage", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_provider"), "llm_token_usage", ["provider"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_reference_id"), "llm_token_usage", ["reference_id"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_reference_type"), "llm_token_usage", ["reference_type"], unique=False)
    op.create_index(op.f("ix_llm_token_usage_used_at"), "llm_token_usage", ["used_at"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", audit_action_type_enum, nullable=False),
        sa.Column("resource_type", audit_resource_type_enum, nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_audit_logs_account_id_accounts")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_account_id"), "audit_logs", ["account_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action_type"), "audit_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_occurred_at"), "audit_logs", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_occurred_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_account_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_llm_token_usage_used_at"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_reference_type"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_reference_id"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_provider"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_platform_connection_id"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_model_name"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_id"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_feature_name"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_actor_user_id"), table_name="llm_token_usage")
    op.drop_index(op.f("ix_llm_token_usage_account_id"), table_name="llm_token_usage")
    op.drop_table("llm_token_usage")

    op.drop_index(op.f("ix_action_usage_logs_reference_type"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_reference_id"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_platform_type"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_platform_connection_id"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_occurred_at"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_id"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_actor_user_id"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_action_type"), table_name="action_usage_logs")
    op.drop_index(op.f("ix_action_usage_logs_account_id"), table_name="action_usage_logs")
    op.drop_table("action_usage_logs")

    audit_resource_type_enum.drop(op.get_bind(), checkfirst=False)
    audit_action_type_enum.drop(op.get_bind(), checkfirst=False)
    action_usage_type_enum.drop(op.get_bind(), checkfirst=False)
