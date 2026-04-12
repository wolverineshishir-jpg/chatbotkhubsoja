"""platform connections

Revision ID: 20260408_000002
Revises: 20260408_000001
Create Date: 2026-04-08 23:40:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260408_000002"
down_revision = "20260408_000001"
branch_labels = None
depends_on = None

platform_type_enum = sa.Enum("FACEBOOK_PAGE", "WHATSAPP", name="platformtype")
connection_status_enum = sa.Enum(
    "PENDING",
    "CONNECTED",
    "ACTION_REQUIRED",
    "DISCONNECTED",
    "ERROR",
    name="connectionstatus",
)


def upgrade() -> None:
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform_type", platform_type_enum, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("external_name", sa.String(length=255), nullable=True),
        sa.Column("status", connection_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("encrypted_access_token", sa.String(length=2048), nullable=True),
        sa.Column("encrypted_refresh_token", sa.String(length=2048), nullable=True),
        sa.Column("token_hint", sa.String(length=16), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("webhook_secret", sa.String(length=255), nullable=True),
        sa.Column("webhook_verify_token", sa.String(length=255), nullable=True),
        sa.Column("webhook_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_platform_connections_account_id_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_connections")),
    )
    op.create_index(op.f("ix_platform_connections_account_id"), "platform_connections", ["account_id"], unique=False)
    op.create_index(op.f("ix_platform_connections_external_id"), "platform_connections", ["external_id"], unique=False)
    op.create_index(op.f("ix_platform_connections_id"), "platform_connections", ["id"], unique=False)
    op.create_index(
        op.f("ix_platform_connections_platform_type"),
        "platform_connections",
        ["platform_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_connections_platform_type"), table_name="platform_connections")
    op.drop_index(op.f("ix_platform_connections_id"), table_name="platform_connections")
    op.drop_index(op.f("ix_platform_connections_external_id"), table_name="platform_connections")
    op.drop_index(op.f("ix_platform_connections_account_id"), table_name="platform_connections")
    op.drop_table("platform_connections")
    connection_status_enum.drop(op.get_bind(), checkfirst=False)
    platform_type_enum.drop(op.get_bind(), checkfirst=False)
