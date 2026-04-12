from conftest import TestingSessionLocal

from app.models.account import Account
from app.models.account_user import AccountUser
from app.models.feature_catalog import FeatureCatalog
from app.models.membership import Membership
from app.models.permission import Permission
from app.models.role import Role
from app.models.token_purchase_package import TokenPurchasePackage
from app.models.token_wallet import TokenWallet
from app.models.user import User
from scripts.seed_system_data import (
    ensure_feature_catalog,
    ensure_permissions,
    ensure_role_permissions,
    ensure_roles,
    ensure_token_packages,
    ensure_wallets_and_account_users,
)


def test_system_seed_bootstraps_roles_permissions_features_and_wallets():
    with TestingSessionLocal() as db:
        user = User(email="seed-user@example.com", hashed_password="hashed-password")
        account = Account(name="Seed Workspace", slug="seed-workspace", token_balance=2500)
        db.add_all([user, account])
        db.flush()
        db.add(Membership(account_id=account.id, user_id=user.id))
        db.commit()

        permissions = ensure_permissions(db)
        roles = ensure_roles(db)
        ensure_role_permissions(db, roles=roles, permissions=permissions)
        ensure_feature_catalog(db)
        ensure_token_packages(db)
        ensure_wallets_and_account_users(db, roles=roles)
        db.commit()

        assert db.query(Role).count() >= 3
        assert db.query(Permission).count() >= 1
        assert db.query(FeatureCatalog).count() >= 1
        assert db.query(TokenPurchasePackage).count() >= 1
        assert db.query(TokenWallet).filter(TokenWallet.account_id == account.id).count() == 1
        assert db.query(AccountUser).filter(AccountUser.account_id == account.id, AccountUser.user_id == user.id).count() == 1
