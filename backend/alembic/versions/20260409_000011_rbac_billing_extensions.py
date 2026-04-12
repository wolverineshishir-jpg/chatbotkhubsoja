"""rbac and billing extensions

Revision ID: 20260409_000011
Revises: 20260409_000010
Create Date: 2026-04-09 11:20:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_000011"
down_revision = "20260409_000010"
branch_labels = None
depends_on = None

role_scope_enum = sa.Enum("SYSTEM", "ACCOUNT", name="rolescope")
feature_value_type_enum = sa.Enum("BOOLEAN", "INTEGER", "DECIMAL", "TOKEN", name="featurevaluetype")
token_wallet_status_enum = sa.Enum("ACTIVE", "FROZEN", "CLOSED", name="tokenwalletstatus")
token_ledger_entry_type_enum = sa.Enum("CREDIT", "DEBIT", "RESERVE", "RELEASE", "EXPIRE", "ADJUSTMENT", name="tokenledgerentrytype")
token_ledger_source_type_enum = sa.Enum("SUBSCRIPTION", "TOKEN_PACKAGE", "AI_USAGE", "ADMIN", "EXPIRATION", name="tokenledgersourcetype")
billing_transaction_type_enum = sa.Enum("SUBSCRIPTION", "TOKEN_PURCHASE", "ADJUSTMENT", "REFUND", name="billingtransactiontype")
billing_transaction_status_enum = sa.Enum("PENDING", "SUCCEEDED", "FAILED", "REFUNDED", "CANCELED", name="billingtransactionstatus")


def upgrade() -> None:
    bind = op.get_bind()
    role_scope_enum.create(bind, checkfirst=True)
    feature_value_type_enum.create(bind, checkfirst=True)
    token_wallet_status_enum.create(bind, checkfirst=True)
    token_ledger_entry_type_enum.create(bind, checkfirst=True)
    token_ledger_source_type_enum.create(bind, checkfirst=True)
    billing_transaction_type_enum.create(bind, checkfirst=True)
    billing_transaction_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("scope", role_scope_enum, nullable=False, server_default="SYSTEM"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_code"), "roles", ["code"], unique=True)
    op.create_index(op.f("ix_roles_scope"), "roles", ["scope"], unique=False)
    op.create_index(op.f("ix_roles_is_system"), "roles", ["is_system"], unique=False)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
    op.create_index(op.f("ix_permissions_code"), "permissions", ["code"], unique=True)
    op.create_index(op.f("ix_permissions_resource"), "permissions", ["resource"], unique=False)
    op.create_index(op.f("ix_permissions_action"), "permissions", ["action"], unique=False)
    op.create_index(op.f("ix_permissions_is_system"), "permissions", ["is_system"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], name=op.f("fk_role_permissions_permission_id_permissions")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_role_permissions_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_id_permission_id"),
    )
    op.create_index(op.f("ix_role_permissions_id"), "role_permissions", ["id"], unique=False)
    op.create_index(op.f("ix_role_permissions_role_id"), "role_permissions", ["role_id"], unique=False)
    op.create_index(op.f("ix_role_permissions_permission_id"), "role_permissions", ["permission_id"], unique=False)

    op.create_table(
        "account_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("invited_email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_account_users_account_id_accounts")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_account_users_role_id_roles")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_account_users_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_users")),
        sa.UniqueConstraint("account_id", "user_id", name="uq_account_users_account_id_user_id"),
    )
    op.create_index(op.f("ix_account_users_id"), "account_users", ["id"], unique=False)
    op.create_index(op.f("ix_account_users_account_id"), "account_users", ["account_id"], unique=False)
    op.create_index(op.f("ix_account_users_user_id"), "account_users", ["user_id"], unique=False)
    op.create_index(op.f("ix_account_users_role_id"), "account_users", ["role_id"], unique=False)
    op.create_index(op.f("ix_account_users_invited_email"), "account_users", ["invited_email"], unique=False)
    op.create_index(op.f("ix_account_users_is_active"), "account_users", ["is_active"], unique=False)

    op.create_table(
        "feature_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("value_type", feature_value_type_enum, nullable=False),
        sa.Column("unit_label", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feature_catalog")),
    )
    op.create_index(op.f("ix_feature_catalog_id"), "feature_catalog", ["id"], unique=False)
    op.create_index(op.f("ix_feature_catalog_code"), "feature_catalog", ["code"], unique=True)
    op.create_index(op.f("ix_feature_catalog_value_type"), "feature_catalog", ["value_type"], unique=False)
    op.create_index(op.f("ix_feature_catalog_is_active"), "feature_catalog", ["is_active"], unique=False)

    op.create_table(
        "plan_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("billing_plan_id", sa.Integer(), nullable=False),
        sa.Column("feature_catalog_id", sa.Integer(), nullable=False),
        sa.Column("included_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("overage_price_usd", sa.Numeric(12, 4), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["billing_plan_id"], ["billing_plans.id"], name=op.f("fk_plan_features_billing_plan_id_billing_plans")),
        sa.ForeignKeyConstraint(["feature_catalog_id"], ["feature_catalog.id"], name=op.f("fk_plan_features_feature_catalog_id_feature_catalog")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_features")),
        sa.UniqueConstraint("billing_plan_id", "feature_catalog_id", name="uq_plan_features_plan_feature"),
    )
    op.create_index(op.f("ix_plan_features_id"), "plan_features", ["id"], unique=False)
    op.create_index(op.f("ix_plan_features_billing_plan_id"), "plan_features", ["billing_plan_id"], unique=False)
    op.create_index(op.f("ix_plan_features_feature_catalog_id"), "plan_features", ["feature_catalog_id"], unique=False)

    op.create_table(
        "account_subscription_feature_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_subscription_id", sa.Integer(), nullable=False),
        sa.Column("feature_catalog_id", sa.Integer(), nullable=False),
        sa.Column("feature_code", sa.String(length=100), nullable=False),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("included_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_subscription_id"],
            ["account_subscriptions.id"],
            name=op.f("fk_account_subscription_feature_snapshot_account_subscription_id_account_subscriptions"),
        ),
        sa.ForeignKeyConstraint(
            ["feature_catalog_id"],
            ["feature_catalog.id"],
            name=op.f("fk_account_subscription_feature_snapshot_feature_catalog_id_feature_catalog"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_subscription_feature_snapshot")),
        sa.UniqueConstraint(
            "account_subscription_id",
            "feature_catalog_id",
            name="uq_account_subscription_feature_snapshot_subscription_feature",
        ),
    )
    op.create_index(op.f("ix_account_subscription_feature_snapshot_id"), "account_subscription_feature_snapshot", ["id"], unique=False)
    op.create_index(op.f("ix_account_subscription_feature_snapshot_account_subscription_id"), "account_subscription_feature_snapshot", ["account_subscription_id"], unique=False)
    op.create_index(op.f("ix_account_subscription_feature_snapshot_feature_catalog_id"), "account_subscription_feature_snapshot", ["feature_catalog_id"], unique=False)
    op.create_index(op.f("ix_account_subscription_feature_snapshot_feature_code"), "account_subscription_feature_snapshot", ["feature_code"], unique=False)

    op.create_table(
        "token_purchase_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("token_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_token_purchase_packages")),
    )
    op.create_index(op.f("ix_token_purchase_packages_id"), "token_purchase_packages", ["id"], unique=False)
    op.create_index(op.f("ix_token_purchase_packages_code"), "token_purchase_packages", ["code"], unique=True)
    op.create_index(op.f("ix_token_purchase_packages_is_active"), "token_purchase_packages", ["is_active"], unique=False)

    op.create_table(
        "token_wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("status", token_wallet_status_enum, nullable=False, server_default="ACTIVE"),
        sa.Column("balance_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_credited_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_debited_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_token_wallets_account_id_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_token_wallets")),
        sa.UniqueConstraint("account_id", name="uq_token_wallets_account_id"),
    )
    op.create_index(op.f("ix_token_wallets_id"), "token_wallets", ["id"], unique=False)
    op.create_index(op.f("ix_token_wallets_account_id"), "token_wallets", ["account_id"], unique=False)
    op.create_index(op.f("ix_token_wallets_status"), "token_wallets", ["status"], unique=False)

    op.create_table(
        "billing_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("account_subscription_id", sa.Integer(), nullable=True),
        sa.Column("token_purchase_package_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", billing_transaction_type_enum, nullable=False),
        sa.Column("status", billing_transaction_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("provider_name", sa.String(length=100), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("amount_usd", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax_usd", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_amount_usd", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_billing_transactions_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["account_subscription_id"],
            ["account_subscriptions.id"],
            name=op.f("fk_billing_transactions_account_subscription_id_account_subscriptions"),
        ),
        sa.ForeignKeyConstraint(
            ["token_purchase_package_id"],
            ["token_purchase_packages.id"],
            name=op.f("fk_billing_transactions_token_purchase_package_id_token_purchase_packages"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_transactions")),
    )
    op.create_index(op.f("ix_billing_transactions_id"), "billing_transactions", ["id"], unique=False)
    op.create_index(op.f("ix_billing_transactions_account_id"), "billing_transactions", ["account_id"], unique=False)
    op.create_index(op.f("ix_billing_transactions_account_subscription_id"), "billing_transactions", ["account_subscription_id"], unique=False)
    op.create_index(op.f("ix_billing_transactions_token_purchase_package_id"), "billing_transactions", ["token_purchase_package_id"], unique=False)
    op.create_index(op.f("ix_billing_transactions_transaction_type"), "billing_transactions", ["transaction_type"], unique=False)
    op.create_index(op.f("ix_billing_transactions_status"), "billing_transactions", ["status"], unique=False)
    op.create_index(op.f("ix_billing_transactions_provider_name"), "billing_transactions", ["provider_name"], unique=False)
    op.create_index(op.f("ix_billing_transactions_external_reference"), "billing_transactions", ["external_reference"], unique=False)
    op.create_index(op.f("ix_billing_transactions_occurred_at"), "billing_transactions", ["occurred_at"], unique=False)

    op.create_table(
        "token_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_wallet_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("account_subscription_id", sa.Integer(), nullable=True),
        sa.Column("billing_transaction_id", sa.Integer(), nullable=True),
        sa.Column("entry_type", token_ledger_entry_type_enum, nullable=False),
        sa.Column("source_type", token_ledger_source_type_enum, nullable=False),
        sa.Column("delta_tokens", sa.Integer(), nullable=False),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("unit_price_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("total_price_usd", sa.Numeric(12, 4), nullable=True),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name=op.f("fk_token_ledger_account_id_accounts")),
        sa.ForeignKeyConstraint(
            ["account_subscription_id"],
            ["account_subscriptions.id"],
            name=op.f("fk_token_ledger_account_subscription_id_account_subscriptions"),
        ),
        sa.ForeignKeyConstraint(
            ["billing_transaction_id"],
            ["billing_transactions.id"],
            name=op.f("fk_token_ledger_billing_transaction_id_billing_transactions"),
        ),
        sa.ForeignKeyConstraint(["token_wallet_id"], ["token_wallets.id"], name=op.f("fk_token_ledger_token_wallet_id_token_wallets")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_token_ledger")),
    )
    op.create_index(op.f("ix_token_ledger_id"), "token_ledger", ["id"], unique=False)
    op.create_index(op.f("ix_token_ledger_token_wallet_id"), "token_ledger", ["token_wallet_id"], unique=False)
    op.create_index(op.f("ix_token_ledger_account_id"), "token_ledger", ["account_id"], unique=False)
    op.create_index(op.f("ix_token_ledger_account_subscription_id"), "token_ledger", ["account_subscription_id"], unique=False)
    op.create_index(op.f("ix_token_ledger_billing_transaction_id"), "token_ledger", ["billing_transaction_id"], unique=False)
    op.create_index(op.f("ix_token_ledger_entry_type"), "token_ledger", ["entry_type"], unique=False)
    op.create_index(op.f("ix_token_ledger_source_type"), "token_ledger", ["source_type"], unique=False)
    op.create_index(op.f("ix_token_ledger_reference_type"), "token_ledger", ["reference_type"], unique=False)
    op.create_index(op.f("ix_token_ledger_reference_id"), "token_ledger", ["reference_id"], unique=False)
    op.create_index(op.f("ix_token_ledger_occurred_at"), "token_ledger", ["occurred_at"], unique=False)

    for table, column in (
        ("roles", "scope"),
        ("roles", "is_system"),
        ("permissions", "is_system"),
        ("account_users", "is_active"),
        ("feature_catalog", "is_active"),
        ("token_purchase_packages", "token_amount"),
        ("token_purchase_packages", "bonus_tokens"),
        ("token_purchase_packages", "price_usd"),
        ("token_purchase_packages", "currency"),
        ("token_purchase_packages", "is_active"),
        ("token_wallets", "status"),
        ("token_wallets", "balance_tokens"),
        ("token_wallets", "reserved_tokens"),
        ("token_wallets", "lifetime_credited_tokens"),
        ("token_wallets", "lifetime_debited_tokens"),
        ("billing_transactions", "status"),
        ("billing_transactions", "currency"),
        ("billing_transactions", "amount_usd"),
        ("billing_transactions", "tax_usd"),
        ("billing_transactions", "total_amount_usd"),
        ("plan_features", "included_value"),
        ("account_subscription_feature_snapshot", "included_value"),
    ):
        op.alter_column(table, column, server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_token_ledger_occurred_at"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_reference_id"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_reference_type"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_source_type"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_entry_type"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_billing_transaction_id"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_account_subscription_id"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_account_id"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_token_wallet_id"), table_name="token_ledger")
    op.drop_index(op.f("ix_token_ledger_id"), table_name="token_ledger")
    op.drop_table("token_ledger")

    op.drop_index(op.f("ix_billing_transactions_occurred_at"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_external_reference"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_provider_name"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_status"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_transaction_type"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_token_purchase_package_id"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_account_subscription_id"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_account_id"), table_name="billing_transactions")
    op.drop_index(op.f("ix_billing_transactions_id"), table_name="billing_transactions")
    op.drop_table("billing_transactions")

    op.drop_index(op.f("ix_token_wallets_status"), table_name="token_wallets")
    op.drop_index(op.f("ix_token_wallets_account_id"), table_name="token_wallets")
    op.drop_index(op.f("ix_token_wallets_id"), table_name="token_wallets")
    op.drop_table("token_wallets")

    op.drop_index(op.f("ix_token_purchase_packages_is_active"), table_name="token_purchase_packages")
    op.drop_index(op.f("ix_token_purchase_packages_code"), table_name="token_purchase_packages")
    op.drop_index(op.f("ix_token_purchase_packages_id"), table_name="token_purchase_packages")
    op.drop_table("token_purchase_packages")

    op.drop_index(op.f("ix_account_subscription_feature_snapshot_feature_code"), table_name="account_subscription_feature_snapshot")
    op.drop_index(op.f("ix_account_subscription_feature_snapshot_feature_catalog_id"), table_name="account_subscription_feature_snapshot")
    op.drop_index(op.f("ix_account_subscription_feature_snapshot_account_subscription_id"), table_name="account_subscription_feature_snapshot")
    op.drop_index(op.f("ix_account_subscription_feature_snapshot_id"), table_name="account_subscription_feature_snapshot")
    op.drop_table("account_subscription_feature_snapshot")

    op.drop_index(op.f("ix_plan_features_feature_catalog_id"), table_name="plan_features")
    op.drop_index(op.f("ix_plan_features_billing_plan_id"), table_name="plan_features")
    op.drop_index(op.f("ix_plan_features_id"), table_name="plan_features")
    op.drop_table("plan_features")

    op.drop_index(op.f("ix_feature_catalog_is_active"), table_name="feature_catalog")
    op.drop_index(op.f("ix_feature_catalog_value_type"), table_name="feature_catalog")
    op.drop_index(op.f("ix_feature_catalog_code"), table_name="feature_catalog")
    op.drop_index(op.f("ix_feature_catalog_id"), table_name="feature_catalog")
    op.drop_table("feature_catalog")

    op.drop_index(op.f("ix_account_users_is_active"), table_name="account_users")
    op.drop_index(op.f("ix_account_users_invited_email"), table_name="account_users")
    op.drop_index(op.f("ix_account_users_role_id"), table_name="account_users")
    op.drop_index(op.f("ix_account_users_user_id"), table_name="account_users")
    op.drop_index(op.f("ix_account_users_account_id"), table_name="account_users")
    op.drop_index(op.f("ix_account_users_id"), table_name="account_users")
    op.drop_table("account_users")

    op.drop_index(op.f("ix_role_permissions_permission_id"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_role_id"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_id"), table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index(op.f("ix_permissions_is_system"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_action"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_resource"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_code"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_table("permissions")

    op.drop_index(op.f("ix_roles_is_system"), table_name="roles")
    op.drop_index(op.f("ix_roles_scope"), table_name="roles")
    op.drop_index(op.f("ix_roles_code"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")

    billing_transaction_status_enum.drop(op.get_bind(), checkfirst=False)
    billing_transaction_type_enum.drop(op.get_bind(), checkfirst=False)
    token_ledger_source_type_enum.drop(op.get_bind(), checkfirst=False)
    token_ledger_entry_type_enum.drop(op.get_bind(), checkfirst=False)
    token_wallet_status_enum.drop(op.get_bind(), checkfirst=False)
    feature_value_type_enum.drop(op.get_bind(), checkfirst=False)
    role_scope_enum.drop(op.get_bind(), checkfirst=False)
