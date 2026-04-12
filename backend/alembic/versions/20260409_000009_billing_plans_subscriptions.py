"""billing plans and account subscriptions

Revision ID: 20260409_000009
Revises: 20260408_000008
Create Date: 2026-04-09 09:10:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_000009"
down_revision = "20260408_000008"
branch_labels = None
depends_on = None

billing_interval_enum = sa.Enum("MONTHLY", "YEARLY", name="billinginterval")
subscription_status_enum = sa.Enum(
    "TRIALING",
    "ACTIVE",
    "PAST_DUE",
    "CANCELED",
    "EXPIRED",
    name="subscriptionstatus",
)


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("billing_interval", billing_interval_enum, nullable=False),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("monthly_token_credit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_plans")),
    )
    op.create_index(op.f("ix_billing_plans_id"), "billing_plans", ["id"], unique=False)
    op.create_index(op.f("ix_billing_plans_code"), "billing_plans", ["code"], unique=True)
    op.create_index(op.f("ix_billing_plans_billing_interval"), "billing_plans", ["billing_interval"], unique=False)
    op.create_index(op.f("ix_billing_plans_is_active"), "billing_plans", ["is_active"], unique=False)

    op.create_table(
        "account_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("billing_plan_id", sa.Integer(), nullable=False),
        sa.Column("status", subscription_status_enum, nullable=False, server_default="TRIALING"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("renews_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_account_subscriptions_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["billing_plan_id"], ["billing_plans.id"], name=op.f("fk_account_subscriptions_billing_plan_id_billing_plans")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_subscriptions")),
    )
    op.create_index(op.f("ix_account_subscriptions_id"), "account_subscriptions", ["id"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_account_id"), "account_subscriptions", ["account_id"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_billing_plan_id"), "account_subscriptions", ["billing_plan_id"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_status"), "account_subscriptions", ["status"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_starts_at"), "account_subscriptions", ["starts_at"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_ends_at"), "account_subscriptions", ["ends_at"], unique=False)
    op.create_index(op.f("ix_account_subscriptions_renews_at"), "account_subscriptions", ["renews_at"], unique=False)
    op.create_index(
        op.f("ix_account_subscriptions_external_subscription_id"),
        "account_subscriptions",
        ["external_subscription_id"],
        unique=False,
    )

    op.alter_column("billing_plans", "price_usd", server_default=None)
    op.alter_column("billing_plans", "monthly_token_credit", server_default=None)
    op.alter_column("account_subscriptions", "status", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_account_subscriptions_external_subscription_id"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_renews_at"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_ends_at"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_starts_at"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_status"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_billing_plan_id"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_account_id"), table_name="account_subscriptions")
    op.drop_index(op.f("ix_account_subscriptions_id"), table_name="account_subscriptions")
    op.drop_table("account_subscriptions")

    op.drop_index(op.f("ix_billing_plans_is_active"), table_name="billing_plans")
    op.drop_index(op.f("ix_billing_plans_billing_interval"), table_name="billing_plans")
    op.drop_index(op.f("ix_billing_plans_code"), table_name="billing_plans")
    op.drop_index(op.f("ix_billing_plans_id"), table_name="billing_plans")
    op.drop_table("billing_plans")

    subscription_status_enum.drop(op.get_bind(), checkfirst=False)
    billing_interval_enum.drop(op.get_bind(), checkfirst=False)
