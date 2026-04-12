"""add user hierarchy columns

Revision ID: 20260409_000013
Revises: 20260409_000012
Create Date: 2026-04-09 17:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260409_000013"
down_revision = "20260409_000012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role_enum = sa.Enum("OWNER", "SUPER_ADMIN", "ADMIN", name="userrole")

    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column("user_role", user_role_enum, nullable=False, server_default="ADMIN"),
    )
    op.add_column(
        "users",
        sa.Column("managed_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("permissions_json", sa.JSON(), nullable=True),
    )
    op.execute("UPDATE users SET permissions_json = JSON_ARRAY() WHERE permissions_json IS NULL")
    op.alter_column("users", "permissions_json", existing_type=sa.JSON(), nullable=False)
    op.create_index(op.f("ix_users_user_role"), "users", ["user_role"], unique=False)
    op.create_index(op.f("ix_users_managed_by_user_id"), "users", ["managed_by_user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_managed_by_user_id_users"),
        "users",
        "users",
        ["managed_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_users_managed_by_user_id_users"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_managed_by_user_id"), table_name="users")
    op.drop_index(op.f("ix_users_user_role"), table_name="users")
    op.drop_column("users", "permissions_json")
    op.drop_column("users", "managed_by_user_id")
    op.drop_column("users", "user_role")

    user_role_enum = sa.Enum("OWNER", "SUPER_ADMIN", "ADMIN", name="userrole")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
