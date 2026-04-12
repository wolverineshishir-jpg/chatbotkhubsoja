from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models.account import Account
from app.models.enums import MembershipRole, MembershipStatus, UserRole, UserStatus
from app.models.membership import Membership
from app.models.user import User
from app.schemas.user import CreateAdminRequest, CreateSuperAdminRequest, UpdateAdminRequest, UpdateSuperAdminRequest
from app.services.token_wallet_service import TokenWalletService
from app.services.user_service import build_managed_user_response

SUPER_ADMIN_FEATURE_PERMISSIONS = {
    "feature:whatsapp_inbox",
    "feature:facebook_inbox",
    "feature:facebook_comments",
    "feature:facebook_posts",
}


class UserManagementService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def ensure_owner_user(self) -> User:
        owner = self.db.scalar(select(User).where(User.email == self.settings.owner_email))
        if owner:
            changed = False
            if owner.user_role != UserRole.OWNER:
                owner.user_role = UserRole.OWNER
                changed = True
            if not owner.is_superuser:
                owner.is_superuser = True
                changed = True
            if not owner.is_active:
                owner.is_active = True
                changed = True
            if owner.status != UserStatus.ACTIVE:
                owner.status = UserStatus.ACTIVE
                changed = True
            if changed:
                self.db.commit()
                self.db.refresh(owner)
            return owner

        owner = User(
            email=self.settings.owner_email,
            full_name=self.settings.owner_full_name,
            hashed_password=hash_password(self.settings.owner_password.get_secret_value()),
            is_active=True,
            is_superuser=True,
            status=UserStatus.ACTIVE,
            user_role=UserRole.OWNER,
            permissions_json=[],
        )
        self.db.add(owner)
        self.db.commit()
        self.db.refresh(owner)
        return owner

    def list_users_for_actor(self, actor: User, account_id: int | None = None):
        statement = select(User).options(
            selectinload(User.memberships).selectinload(Membership.account),
        )
        if actor.user_role == UserRole.OWNER:
            statement = statement.where(User.user_role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
        elif actor.user_role == UserRole.SUPER_ADMIN:
            statement = statement.where(User.managed_by_user_id == actor.id, User.user_role == UserRole.ADMIN)
            if account_id is not None:
                statement = statement.join(User.memberships).where(Membership.account_id == account_id)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to user management.")

        users = self.db.scalars(statement.order_by(User.created_at.asc())).unique().all()
        return [build_managed_user_response(user) for user in users]

    def create_super_admin(self, actor: User, payload: CreateSuperAdminRequest):
        self._require_owner(actor)
        self._ensure_email_available(payload.email)
        permissions = self._normalize_super_admin_permissions(payload.permissions)

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_active=payload.status == UserStatus.ACTIVE,
            is_superuser=False,
            status=payload.status,
            user_role=UserRole.SUPER_ADMIN,
            managed_by_user_id=actor.id,
            permissions_json=permissions,
        )
        self.db.add(user)
        self.db.flush()

        account = Account(name=payload.account_name, slug=payload.account_slug)
        self.db.add(account)
        self.db.flush()

        membership = Membership(
            account_id=account.id,
            user_id=user.id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )
        self.db.add(membership)
        TokenWalletService(self.db).ensure_wallet(account=account)
        self.db.commit()
        self.db.refresh(user)
        return build_managed_user_response(self._get_user_with_membership(user.id))

    def update_super_admin(self, actor: User, user_id: int, payload: UpdateSuperAdminRequest):
        self._require_owner(actor)
        user = self._get_user_by_role(user_id, UserRole.SUPER_ADMIN)
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password:
            user.hashed_password = hash_password(payload.password)
        if payload.status is not None:
            self._apply_status(user, payload.status)
            if payload.status in {UserStatus.DISABLED, UserStatus.INVITED}:
                self._cascade_status_to_admins(user, payload.status)
        if payload.permissions is not None:
            user.permissions_json = self._normalize_super_admin_permissions(payload.permissions)
        self.db.commit()
        self.db.refresh(user)
        return build_managed_user_response(self._get_user_with_membership(user.id))

    def create_admin(self, actor: User, account: Account, payload: CreateAdminRequest):
        self._require_super_admin(actor)
        self._ensure_email_available(payload.email)
        permissions = self._normalize_admin_permissions(payload.permissions)

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_active=payload.status == UserStatus.ACTIVE,
            is_superuser=False,
            status=payload.status,
            user_role=UserRole.ADMIN,
            managed_by_user_id=actor.id,
            permissions_json=permissions,
        )
        self.db.add(user)
        self.db.flush()

        membership = Membership(
            account_id=account.id,
            user_id=user.id,
            role=MembershipRole.ADMIN,
            status=MembershipStatus.ACTIVE,
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(user)
        return build_managed_user_response(self._get_user_with_membership(user.id))

    def update_admin(self, actor: User, user_id: int, payload: UpdateAdminRequest):
        self._require_super_admin(actor)
        user = self._get_managed_admin(actor.id, user_id)
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password:
            user.hashed_password = hash_password(payload.password)
        if payload.status is not None:
            self._apply_status(user, payload.status)
        if payload.permissions is not None:
            user.permissions_json = self._normalize_admin_permissions(payload.permissions)
        self.db.commit()
        self.db.refresh(user)
        return build_managed_user_response(self._get_user_with_membership(user.id))

    def delete_admin(self, actor: User, user_id: int) -> None:
        self._require_super_admin(actor)
        user = self._get_managed_admin(actor.id, user_id)
        self._apply_status(user, UserStatus.DISABLED)
        now = datetime.now(UTC)
        for token in user.refresh_tokens:
            token.revoked_at = now
        self.db.commit()

    def _cascade_status_to_admins(self, super_admin: User, status_to_apply: UserStatus) -> None:
        admins = self.db.scalars(
            select(User)
            .where(User.managed_by_user_id == super_admin.id, User.user_role == UserRole.ADMIN)
            .options(selectinload(User.refresh_tokens))
        ).all()
        now = datetime.now(UTC)
        for admin in admins:
            self._apply_status(admin, status_to_apply)
            for token in admin.refresh_tokens:
                token.revoked_at = now

    @staticmethod
    def _apply_status(user: User, status_to_apply: UserStatus) -> None:
        user.status = status_to_apply
        user.is_active = status_to_apply == UserStatus.ACTIVE

    def _get_user_by_role(self, user_id: int, expected_role: UserRole) -> User:
        user = self.db.scalar(
            select(User)
            .where(User.id == user_id, User.user_role == expected_role)
            .options(selectinload(User.memberships).selectinload(Membership.account), selectinload(User.refresh_tokens))
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    def _get_managed_admin(self, manager_user_id: int, user_id: int) -> User:
        user = self.db.scalar(
            select(User)
            .where(
                User.id == user_id,
                User.user_role == UserRole.ADMIN,
                User.managed_by_user_id == manager_user_id,
            )
            .options(selectinload(User.memberships).selectinload(Membership.account), selectinload(User.refresh_tokens))
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found.")
        return user

    def _get_user_with_membership(self, user_id: int) -> User:
        user = self.db.scalar(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.memberships).selectinload(Membership.account))
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    def _ensure_email_available(self, email: str) -> None:
        existing = self.db.scalar(select(User).where(User.email == email))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    @staticmethod
    def _require_owner(actor: User) -> None:
        if actor.user_role != UserRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can manage super admins.")

    @staticmethod
    def _require_super_admin(actor: User) -> None:
        if actor.user_role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a super admin can manage admins.")

    @staticmethod
    def _normalize_admin_permissions(permissions: list[str]) -> list[str]:
        allowed = ROLE_PERMISSIONS[MembershipRole.ADMIN]
        invalid = sorted(set(permissions) - allowed)
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid admin permissions: {', '.join(invalid)}",
            )
        return sorted(set(permissions))

    @staticmethod
    def _normalize_super_admin_permissions(permissions: list[str]) -> list[str]:
        normalized = sorted(set(permissions))
        invalid = sorted(set(normalized) - SUPER_ADMIN_FEATURE_PERMISSIONS)
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid super admin feature permissions: {', '.join(invalid)}",
            )
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one super admin feature permission must be selected.",
            )
        return normalized
