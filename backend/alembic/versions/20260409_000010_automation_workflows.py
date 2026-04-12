"""automation workflows

Revision ID: 20260409_000010
Revises: 20260409_000009
Create Date: 2026-04-09 10:40:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_000010"
down_revision = "20260409_000009"
branch_labels = None
depends_on = None

automation_workflow_status_enum = sa.Enum("DRAFT", "ACTIVE", "PAUSED", "ARCHIVED", name="automationworkflowstatus")
automation_trigger_type_enum = sa.Enum(
    "INBOX_MESSAGE_RECEIVED",
    "FACEBOOK_COMMENT_CREATED",
    "SCHEDULED_DAILY",
    name="automationtriggertype",
)
automation_action_type_enum = sa.Enum(
    "GENERATE_INBOX_REPLY",
    "GENERATE_COMMENT_REPLY",
    "GENERATE_POST_DRAFT",
    name="automationactiontype",
)
sync_job_type_enum = sa.Enum(
    "WEBHOOK_PROCESSING",
    "AI_REPLY_GENERATION",
    "AUTOMATION_RULE_EXECUTION",
    "SCHEDULED_POST_PUBLISH",
    "RETRY_FAILED_SEND",
    "TOKEN_EXPIRATION",
    "TOKEN_MONTHLY_CREDIT",
    name="syncjobtype",
)
old_sync_job_type_enum = sa.Enum(
    "WEBHOOK_PROCESSING",
    "AI_REPLY_GENERATION",
    "SCHEDULED_POST_PUBLISH",
    "RETRY_FAILED_SEND",
    "TOKEN_EXPIRATION",
    "TOKEN_MONTHLY_CREDIT",
    name="syncjobtype",
)


def upgrade() -> None:
    bind = op.get_bind()
    automation_workflow_status_enum.create(bind, checkfirst=True)
    automation_trigger_type_enum.create(bind, checkfirst=True)
    automation_action_type_enum.create(bind, checkfirst=True)
    sync_job_type_enum.create(bind, checkfirst=True)
    op.alter_column("sync_jobs", "job_type", existing_type=old_sync_job_type_enum, type_=sync_job_type_enum, existing_nullable=False)

    op.create_table(
        "automation_workflows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_connection_id", sa.Integer(), nullable=True),
        sa.Column("ai_agent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("status", automation_workflow_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("trigger_type", automation_trigger_type_enum, nullable=False),
        sa.Column("action_type", automation_action_type_enum, nullable=False),
        sa.Column("delay_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger_filters_json", sa.JSON(), nullable=False),
        sa.Column("action_config_json", sa.JSON(), nullable=False),
        sa.Column("schedule_timezone", sa.String(length=64), nullable=True),
        sa.Column("schedule_local_time", sa.String(length=5), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_automation_workflows_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["platform_connection_id"],
            ["platform_connections.id"],
            name=op.f("fk_automation_workflows_platform_connection_id_platform_connections"),
        ),
        sa.ForeignKeyConstraint(["ai_agent_id"], ["ai_agents.id"], name=op.f("fk_automation_workflows_ai_agent_id_ai_agents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_automation_workflows")),
    )
    op.create_index(op.f("ix_automation_workflows_id"), "automation_workflows", ["id"], unique=False)
    op.create_index(op.f("ix_automation_workflows_account_id"), "automation_workflows", ["account_id"], unique=False)
    op.create_index(op.f("ix_automation_workflows_platform_connection_id"), "automation_workflows", ["platform_connection_id"], unique=False)
    op.create_index(op.f("ix_automation_workflows_ai_agent_id"), "automation_workflows", ["ai_agent_id"], unique=False)
    op.create_index(op.f("ix_automation_workflows_status"), "automation_workflows", ["status"], unique=False)
    op.create_index(op.f("ix_automation_workflows_trigger_type"), "automation_workflows", ["trigger_type"], unique=False)
    op.create_index(op.f("ix_automation_workflows_action_type"), "automation_workflows", ["action_type"], unique=False)
    op.create_index(op.f("ix_automation_workflows_next_run_at"), "automation_workflows", ["next_run_at"], unique=False)

    op.alter_column("automation_workflows", "status", server_default=None)
    op.alter_column("automation_workflows", "delay_seconds", server_default=None)


def downgrade() -> None:
    op.alter_column("sync_jobs", "job_type", existing_type=sync_job_type_enum, type_=old_sync_job_type_enum, existing_nullable=False)
    op.drop_index(op.f("ix_automation_workflows_next_run_at"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_action_type"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_trigger_type"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_status"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_ai_agent_id"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_platform_connection_id"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_account_id"), table_name="automation_workflows")
    op.drop_index(op.f("ix_automation_workflows_id"), table_name="automation_workflows")
    op.drop_table("automation_workflows")
    automation_action_type_enum.drop(op.get_bind(), checkfirst=False)
    automation_trigger_type_enum.drop(op.get_bind(), checkfirst=False)
    automation_workflow_status_enum.drop(op.get_bind(), checkfirst=False)
