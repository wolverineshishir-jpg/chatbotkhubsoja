"""async processing foundation

Revision ID: 20260408_000007
Revises: 20260408_000006
Create Date: 2026-04-09 04:20:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000007"
down_revision = "20260408_000006"
branch_labels = None
depends_on = None

webhook_event_source_enum = sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="webhookeventsource")
webhook_event_status_enum = sa.Enum("PENDING", "PROCESSING", "PROCESSED", "FAILED", "IGNORED", name="webhookeventstatus")
sync_job_type_enum = sa.Enum(
    "WEBHOOK_PROCESSING",
    "AI_REPLY_GENERATION",
    "SCHEDULED_POST_PUBLISH",
    "RETRY_FAILED_SEND",
    "TOKEN_EXPIRATION",
    "TOKEN_MONTHLY_CREDIT",
    name="syncjobtype",
)
sync_job_status_enum = sa.Enum(
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "RETRY_SCHEDULED",
    "CANCELED",
    name="syncjobstatus",
)


def upgrade() -> None:
    op.add_column("accounts", sa.Column("token_balance", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("accounts", sa.Column("monthly_token_credit", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("accounts", sa.Column("token_credit_last_applied_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("accounts", sa.Column("token_credit_next_reset_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        op.f("ix_accounts_token_credit_next_reset_at"),
        "accounts",
        ["token_credit_next_reset_at"],
        unique=False,
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("platform_type", sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype"), nullable=False),
        sa.Column("source", webhook_event_source_enum, nullable=False),
        sa.Column("status", webhook_event_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_key", sa.String(length=255), nullable=False),
        sa.Column("delivery_id", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_task_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("headers_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_webhook_events_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_webhook_events_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_events")),
        sa.UniqueConstraint("event_key", name="uq_webhook_events_event_key"),
    )
    op.create_index(op.f("ix_webhook_events_account_id"), "webhook_events", ["account_id"], unique=False)
    op.create_index(op.f("ix_webhook_events_delivery_id"), "webhook_events", ["delivery_id"], unique=False)
    op.create_index(op.f("ix_webhook_events_event_type"), "webhook_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_webhook_events_id"), "webhook_events", ["id"], unique=False)
    op.create_index(op.f("ix_webhook_events_platform_connection_id"), "webhook_events", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_webhook_events_platform_type"), "webhook_events", ["platform_type"], unique=False)
    op.create_index(op.f("ix_webhook_events_processed_at"), "webhook_events", ["processed_at"], unique=False)
    op.create_index(op.f("ix_webhook_events_received_at"), "webhook_events", ["received_at"], unique=False)
    op.create_index(op.f("ix_webhook_events_source"), "webhook_events", ["source"], unique=False)
    op.create_index(op.f("ix_webhook_events_status"), "webhook_events", ["status"], unique=False)

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("status", sync_job_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("job_type", sync_job_type_enum, nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retry_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_task_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_sync_jobs_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_sync_jobs_platform_connection_id_platform_connections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_jobs")),
        sa.UniqueConstraint("dedupe_key", name="uq_sync_jobs_dedupe_key"),
    )
    op.create_index(op.f("ix_sync_jobs_account_id"), "sync_jobs", ["account_id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_id"), "sync_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_job_type"), "sync_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_sync_jobs_platform_connection_id"), "sync_jobs", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_retry_after"), "sync_jobs", ["retry_after"], unique=False)
    op.create_index(op.f("ix_sync_jobs_scheduled_for"), "sync_jobs", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_sync_jobs_status"), "sync_jobs", ["status"], unique=False)

    op.alter_column("accounts", "token_balance", server_default=None)
    op.alter_column("accounts", "monthly_token_credit", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_jobs_status"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_scheduled_for"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_retry_after"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_platform_connection_id"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_job_type"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_id"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_account_id"), table_name="sync_jobs")
    op.drop_table("sync_jobs")

    op.drop_index(op.f("ix_webhook_events_status"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_source"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_received_at"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_processed_at"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_platform_type"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_platform_connection_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_event_type"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_delivery_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_account_id"), table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index(op.f("ix_accounts_token_credit_next_reset_at"), table_name="accounts")
    op.drop_column("accounts", "token_credit_next_reset_at")
    op.drop_column("accounts", "token_credit_last_applied_at")
    op.drop_column("accounts", "monthly_token_credit")
    op.drop_column("accounts", "token_balance")

    sync_job_status_enum.drop(op.get_bind(), checkfirst=False)
    sync_job_type_enum.drop(op.get_bind(), checkfirst=False)
    webhook_event_status_enum.drop(op.get_bind(), checkfirst=False)
    webhook_event_source_enum.drop(op.get_bind(), checkfirst=False)
