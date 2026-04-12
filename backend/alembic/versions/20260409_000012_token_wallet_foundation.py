"""token wallet foundation

Revision ID: 20260409_000012
Revises: 20260409_000011
Create Date: 2026-04-09 12:20:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_000012"
down_revision = "20260409_000011"
branch_labels = None
depends_on = None

tokenallocationtype = sa.Enum("MONTHLY_FREE", "PURCHASED", "MANUAL", name="tokenallocationtype")


def upgrade() -> None:
    bind = op.get_bind()
    tokenallocationtype.create(bind, checkfirst=True)

    op.add_column("billing_plans", sa.Column("setup_fee_usd", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.alter_column("billing_plans", "setup_fee_usd", server_default=None)

    op.add_column("token_ledger", sa.Column("allocation_type", tokenallocationtype, nullable=True))
    op.add_column("token_ledger", sa.Column("remaining_tokens", sa.Integer(), nullable=True))
    op.add_column("token_ledger", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("token_ledger", sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("token_ledger", sa.Column("is_expired", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index(op.f("ix_token_ledger_allocation_type"), "token_ledger", ["allocation_type"], unique=False)
    op.create_index(op.f("ix_token_ledger_expires_at"), "token_ledger", ["expires_at"], unique=False)
    op.create_index(op.f("ix_token_ledger_is_expired"), "token_ledger", ["is_expired"], unique=False)
    op.alter_column("token_ledger", "is_expired", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_token_ledger_is_expired"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_expires_at"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_allocation_type"), table_name="token_ledger")
    op.drop_column("token_ledger", "is_expired")
    op.drop_column("token_ledger", "expired_at")
    op.drop_column("token_ledger", "expires_at")
    op.drop_column("token_ledger", "remaining_tokens")
    op.drop_column("token_ledger", "allocation_type")
    op.drop_column("billing_plans", "setup_fee_usd")
    tokenallocationtype.drop(op.get_bind(), checkfirst=False)
