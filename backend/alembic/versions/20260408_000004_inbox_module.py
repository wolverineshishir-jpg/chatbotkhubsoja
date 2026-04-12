"""inbox module

Revision ID: 20260408_000004
Revises: 20260408_000003
Create Date: 2026-04-09 01:30:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000004"
down_revision = "20260408_000003"
branch_labels = None
depends_on = None

conversation_status_enum = sa.Enum("OPEN", "ASSIGNED", "PAUSED", "RESOLVED", "ESCALATED", name="conversationstatus")
sender_type_enum = sa.Enum("CUSTOMER", "LLM_BOT", "HUMAN_ADMIN", "SYSTEM", name="sendertype")
message_direction_enum = sa.Enum("INBOUND", "OUTBOUND", name="messagedirection")
message_delivery_status_enum = sa.Enum(
    "PENDING",
    "QUEUED",
    "SENT",
    "DELIVERED",
    "FAILED",
    name="messagedeliverystatus",
)


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("platform_type", sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype"), nullable=False),
        sa.Column("status", conversation_status_enum, nullable=False, server_default="OPEN"),
        sa.Column("external_thread_id", sa.String(length=255), nullable=True),
        sa.Column("customer_external_id", sa.String(length=255), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_avatar_url", sa.String(length=500), nullable=True),
        sa.Column("customer_phone", sa.String(length=64), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("latest_message_preview", sa.String(length=500), nullable=True),
        sa.Column("latest_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_inbound_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_conversations_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"], ["users.id"], name=op.f("fk_conversations_assigned_to_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_conversations_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_account_id"), "conversations", ["account_id"], unique=False)
    op.create_index(op.f("ix_conversations_assigned_to_user_id"), "conversations", ["assigned_to_user_id"], unique=False)
    op.create_index(op.f("ix_conversations_customer_external_id"), "conversations", ["customer_external_id"], unique=False)
    op.create_index(op.f("ix_conversations_customer_name"), "conversations", ["customer_name"], unique=False)
    op.create_index(op.f("ix_conversations_external_thread_id"), "conversations", ["external_thread_id"], unique=False)
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index(op.f("ix_conversations_latest_message_at"), "conversations", ["latest_message_at"], unique=False)
    op.create_index(op.f("ix_conversations_platform_connection_id"), "conversations", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_conversations_platform_type"), "conversations", ["platform_type"], unique=False)
    op.create_index(op.f("ix_conversations_status"), "conversations", ["status"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sender_type", sender_type_enum, nullable=False),
        sa.Column("direction", message_direction_enum, nullable=False),
        sa.Column("delivery_status", message_delivery_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("sender_external_id", sa.String(length=255), nullable=True),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_messages_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id_conversations")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name=op.f("fk_messages_created_by_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_account_id"), "messages", ["account_id"], unique=False)
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_messages_created_by_user_id"), "messages", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_messages_delivery_status"), "messages", ["delivery_status"], unique=False)
    op.create_index(op.f("ix_messages_direction"), "messages", ["direction"], unique=False)
    op.create_index(op.f("ix_messages_external_message_id"), "messages", ["external_message_id"], unique=False)
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)
    op.create_index(op.f("ix_messages_sender_external_id"), "messages", ["sender_external_id"], unique=False)
    op.create_index(op.f("ix_messages_sender_type"), "messages", ["sender_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_sender_type"), table_name="messages")
    op.drop_index(op.f("ix_messages_sender_external_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_external_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_direction"), table_name="messages")
    op.drop_index(op.f("ix_messages_delivery_status"), table_name="messages")
    op.drop_index(op.f("ix_messages_created_by_user_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_account_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_conversations_status"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_platform_type"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_platform_connection_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_latest_message_at"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_external_thread_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_customer_name"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_customer_external_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_assigned_to_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_account_id"), table_name="conversations")
    op.drop_table("conversations")

    message_delivery_status_enum.drop(op.get_bind(), checkfirst=False)
    message_direction_enum.drop(op.get_bind(), checkfirst=False)
    sender_type_enum.drop(op.get_bind(), checkfirst=False)
    conversation_status_enum.drop(op.get_bind(), checkfirst=False)
