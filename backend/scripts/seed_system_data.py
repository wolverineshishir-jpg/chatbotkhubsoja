from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.exc import OperationalError
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "seed-secret-key-with-at-least-32-characters")

from app.core.permissions import ROLE_PERMISSIONS
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.account_user import AccountUser
from app.models.billing_plan import BillingPlan
from app.models.enums import BillingInterval, FeatureValueType, MembershipRole, RoleScope, TokenWalletStatus
from app.models.feature_catalog import FeatureCatalog
from app.models.membership import Membership
from app.models.permission import Permission
from app.models.plan_feature import PlanFeature
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.token_purchase_package import TokenPurchasePackage
from app.models.token_wallet import TokenWallet


DEFAULT_ROLES = [
    {
        "code": "owner",
        "name": "Owner",
        "description": "Full workspace administration role.",
        "scope": RoleScope.SYSTEM,
        "is_system": True,
    },
    {
        "code": "admin",
        "name": "Admin",
        "description": "Operational administrator role.",
        "scope": RoleScope.SYSTEM,
        "is_system": True,
    },
    {
        "code": "super_admin",
        "name": "Super Admin",
        "description": "Cross-workspace supervisory role for operational governance.",
        "scope": RoleScope.SYSTEM,
        "is_system": True,
    },
]

DEFAULT_FEATURES = [
    {
        "code": "monthly_tokens",
        "name": "Monthly token credit",
        "description": "Tokens included with the active plan each billing cycle.",
        "value_type": FeatureValueType.TOKEN,
        "unit_label": "tokens",
    },
    {
        "code": "team_members",
        "name": "Team members",
        "description": "Maximum active account members supported by the plan.",
        "value_type": FeatureValueType.INTEGER,
        "unit_label": "members",
    },
    {
        "code": "platform_connections",
        "name": "Platform connections",
        "description": "Maximum connected Facebook or WhatsApp channels.",
        "value_type": FeatureValueType.INTEGER,
        "unit_label": "connections",
    },
    {
        "code": "ai_agents",
        "name": "AI agents",
        "description": "Maximum AI agents configurable on the account.",
        "value_type": FeatureValueType.INTEGER,
        "unit_label": "agents",
    },
    {
        "code": "automation_workflows",
        "name": "Automation workflows",
        "description": "Maximum saved automation workflows available to the account.",
        "value_type": FeatureValueType.INTEGER,
        "unit_label": "workflows",
    },
    {
        "code": "advanced_reporting",
        "name": "Advanced reporting",
        "description": "Whether advanced dashboards and export capabilities are enabled.",
        "value_type": FeatureValueType.BOOLEAN,
        "unit_label": None,
    },
]

DEFAULT_TOKEN_PACKAGES = [
    {
        "code": "tokens_10k",
        "name": "10K tokens",
        "description": "Starter token top-up package.",
        "token_amount": 10000,
        "bonus_tokens": 0,
        "price_usd": 19,
        "currency": "USD",
    },
    {
        "code": "tokens_50k",
        "name": "50K tokens",
        "description": "Growth token top-up package.",
        "token_amount": 50000,
        "bonus_tokens": 5000,
        "price_usd": 79,
        "currency": "USD",
    },
]

DEFAULT_PLANS = [
    {
        "code": "starter_monthly",
        "name": "Starter Monthly",
        "description": "Starter plan for growing teams launching automation workflows.",
        "billing_interval": "monthly",
        "setup_fee_usd": 0,
        "price_usd": 29,
        "monthly_token_credit": 15000,
        "features": {
            "monthly_tokens": 15000,
            "team_members": 3,
            "platform_connections": 2,
            "ai_agents": 2,
            "automation_workflows": 5,
            "advanced_reporting": 0,
        },
    },
    {
        "code": "growth_monthly",
        "name": "Growth Monthly",
        "description": "Growth plan for active teams with higher automation volume.",
        "billing_interval": "monthly",
        "setup_fee_usd": 99,
        "price_usd": 99,
        "monthly_token_credit": 60000,
        "features": {
            "monthly_tokens": 60000,
            "team_members": 10,
            "platform_connections": 10,
            "ai_agents": 8,
            "automation_workflows": 25,
            "advanced_reporting": 1,
        },
    },
]


def ensure_permissions(db) -> dict[str, Permission]:
    all_codes = sorted({permission for permission_set in ROLE_PERMISSIONS.values() for permission in permission_set})
    permissions: dict[str, Permission] = {}
    for code in all_codes:
        resource, action = code.split(":", 1)
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(
                code=code,
                name=f"{resource.replace('_', ' ').title()} {action.replace('_', ' ').title()}",
                description=f"Allows {action.replace('_', ' ')} access for {resource.replace('_', ' ')}.",
                resource=resource,
                action=action,
                is_system=True,
                metadata_json={"seeded_by": "seed_system_data"},
            )
            db.add(permission)
            db.flush()
        permissions[code] = permission
    return permissions


def ensure_roles(db) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for payload in DEFAULT_ROLES:
        role = db.scalar(select(Role).where(Role.code == payload["code"]))
        if role is None:
            role = Role(**payload, metadata_json={"seeded_by": "seed_system_data"})
            db.add(role)
            db.flush()
        else:
            role.name = payload["name"]
            role.description = payload["description"]
            role.scope = payload["scope"]
            role.is_system = payload["is_system"]
        roles[role.code] = role
    return roles


def ensure_role_permissions(db, *, roles: dict[str, Role], permissions: dict[str, Permission]) -> None:
    role_map = {
        MembershipRole.OWNER: roles["owner"],
        MembershipRole.ADMIN: roles["admin"],
    }
    for membership_role, permission_codes in ROLE_PERMISSIONS.items():
        role = role_map[membership_role]
        for code in permission_codes:
            existing = db.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[code].id,
                )
            )
            if existing is None:
                db.add(RolePermission(role_id=role.id, permission_id=permissions[code].id))


def ensure_feature_catalog(db) -> None:
    for payload in DEFAULT_FEATURES:
        feature = db.scalar(select(FeatureCatalog).where(FeatureCatalog.code == payload["code"]))
        if feature is None:
            db.add(FeatureCatalog(**payload, is_active=True, metadata_json={"seeded_by": "seed_system_data"}))
        else:
            feature.name = payload["name"]
            feature.description = payload["description"]
            feature.value_type = payload["value_type"]
            feature.unit_label = payload["unit_label"]
            feature.is_active = True


def ensure_plans_and_feature_links(db) -> None:
    feature_map = {feature.code: feature for feature in db.scalars(select(FeatureCatalog)).all()}
    for payload in DEFAULT_PLANS:
        plan = db.scalar(select(BillingPlan).where(BillingPlan.code == payload["code"]))
        if plan is None:
            plan = BillingPlan(
                code=payload["code"],
                name=payload["name"],
                description=payload["description"],
                billing_interval=BillingInterval(payload["billing_interval"]),
                setup_fee_usd=payload["setup_fee_usd"],
                price_usd=payload["price_usd"],
                monthly_token_credit=payload["monthly_token_credit"],
                is_active=True,
                metadata_json={"seeded_by": "seed_system_data"},
            )
            db.add(plan)
            db.flush()
        else:
            plan.name = payload["name"]
            plan.description = payload["description"]
            plan.billing_interval = BillingInterval(payload["billing_interval"])
            plan.setup_fee_usd = payload["setup_fee_usd"]
            plan.price_usd = payload["price_usd"]
            plan.monthly_token_credit = payload["monthly_token_credit"]
            plan.is_active = True

        for feature_code, included_value in payload["features"].items():
            feature = feature_map.get(feature_code)
            if feature is None:
                continue
            link = db.scalar(
                select(PlanFeature).where(
                    PlanFeature.billing_plan_id == plan.id,
                    PlanFeature.feature_catalog_id == feature.id,
                )
            )
            if link is None:
                db.add(
                    PlanFeature(
                        billing_plan_id=plan.id,
                        feature_catalog_id=feature.id,
                        included_value=included_value,
                        config_json={"seeded_by": "seed_system_data"},
                    )
                )
            else:
                link.included_value = included_value


def ensure_token_packages(db) -> None:
    for payload in DEFAULT_TOKEN_PACKAGES:
        package = db.scalar(select(TokenPurchasePackage).where(TokenPurchasePackage.code == payload["code"]))
        if package is None:
            db.add(TokenPurchasePackage(**payload, is_active=True, metadata_json={"seeded_by": "seed_system_data"}))
        else:
            package.name = payload["name"]
            package.description = payload["description"]
            package.token_amount = payload["token_amount"]
            package.bonus_tokens = payload["bonus_tokens"]
            package.price_usd = payload["price_usd"]
            package.currency = payload["currency"]
            package.is_active = True


def ensure_wallets_and_account_users(db, *, roles: dict[str, Role]) -> None:
    memberships = db.scalars(select(Membership)).all()
    for membership in memberships:
        existing_link = db.scalar(
            select(AccountUser).where(
                AccountUser.account_id == membership.account_id,
                AccountUser.user_id == membership.user_id,
            )
        )
        if existing_link is None:
            db.add(
                AccountUser(
                    account_id=membership.account_id,
                    user_id=membership.user_id,
                    role_id=roles[membership.role.value].id if membership.role.value in roles else None,
                    invited_email=membership.invited_email,
                    is_active=True,
                )
            )

    accounts = db.scalars(select(Account)).all()
    for account in accounts:
        wallet = db.scalar(select(TokenWallet).where(TokenWallet.account_id == account.id))
        if wallet is None:
            db.add(
                TokenWallet(
                    account_id=account.id,
                    status=TokenWalletStatus.ACTIVE,
                    balance_tokens=account.token_balance,
                    reserved_tokens=0,
                    lifetime_credited_tokens=max(account.token_balance, 0),
                    lifetime_debited_tokens=0,
                    metadata_json={"seeded_by": "seed_system_data", "created_at": datetime.now(UTC).isoformat()},
                )
            )


def main() -> None:
    db = SessionLocal()
    try:
        permissions = ensure_permissions(db)
        roles = ensure_roles(db)
        ensure_role_permissions(db, roles=roles, permissions=permissions)
        ensure_feature_catalog(db)
        ensure_plans_and_feature_links(db)
        ensure_token_packages(db)
        ensure_wallets_and_account_users(db, roles=roles)
        db.commit()
        print("Seeded system roles, permissions, feature catalog, token packages, account-user links, and token wallets.")
    except OperationalError as exc:
        message = (
            "Database connection failed while running seed_system_data.py. "
            "Start MySQL first or set DATABASE_URL/MYSQL_HOST for your current environment."
        )
        raise SystemExit(f"{message}\nOriginal error: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
