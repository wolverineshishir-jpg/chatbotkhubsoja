from datetime import UTC, datetime
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.enums import MembershipRole, MembershipStatus
from app.models.membership import Membership
from app.models.onboarding_key import OnboardingKey
from app.models.user import User
from app.schemas.account import (
    CreateAccountRequest,
    CreateOnboardingKeyRequest,
    CurrentAccountResponse,
    OnboardingKeyResponse,
)
from app.services.token_wallet_service import TokenWalletService
from app.services.user_service import build_team_member_response


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, user: User, payload: CreateAccountRequest) -> CurrentAccountResponse:
        existing_account = self.db.scalar(select(Account).where(Account.slug == payload.slug))
        if existing_account:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account slug is already in use.")

        account = Account(name=payload.name, slug=payload.slug)
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
        self.db.refresh(account)

        return CurrentAccountResponse(
            id=account.id,
            name=account.name,
            slug=account.slug,
            role=membership.role,
            token_balance=account.token_balance,
            monthly_token_credit=account.monthly_token_credit,
        )

    def join_account(self, user: User, onboarding_key_value: str) -> CurrentAccountResponse:
        onboarding_key = self._get_valid_onboarding_key(onboarding_key_value, user.email)

        existing_membership = self.db.scalar(
            select(Membership).where(Membership.account_id == onboarding_key.account_id, Membership.user_id == user.id)
        )
        if existing_membership:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already belongs to this account.")

        membership = Membership(
            account_id=onboarding_key.account_id,
            user_id=user.id,
            role=onboarding_key.role,
            status=MembershipStatus.ACTIVE,
            invited_email=onboarding_key.invited_email,
        )
        onboarding_key.used_count += 1
        self.db.add(membership)
        self.db.commit()

        account = self.db.get(Account, onboarding_key.account_id)
        return CurrentAccountResponse(
            id=account.id,
            name=account.name,
            slug=account.slug,
            role=membership.role,
            token_balance=account.token_balance,
            monthly_token_credit=account.monthly_token_credit,
        )

    def create_onboarding_key(
        self,
        account: Account,
        payload: CreateOnboardingKeyRequest,
    ) -> OnboardingKeyResponse:
        if payload.expires_at and self._ensure_utc(payload.expires_at) <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Expiration must be in the future.")

        onboarding_key = OnboardingKey(
            account_id=account.id,
            key=token_urlsafe(24),
            role=payload.role,
            max_uses=payload.max_uses,
            expires_at=payload.expires_at,
            invited_email=payload.invited_email,
        )
        self.db.add(onboarding_key)
        self.db.commit()
        self.db.refresh(onboarding_key)
        return OnboardingKeyResponse.model_validate(onboarding_key)

    def list_team_members(self, account_id: int):
        memberships = self.db.scalars(
            select(Membership)
            .where(Membership.account_id == account_id)
            .options(selectinload(Membership.user))
            .order_by(Membership.created_at.asc())
        ).all()
        return [build_team_member_response(membership) for membership in memberships]

    def assign_role(
        self,
        account: Account,
        actor_membership: Membership,
        membership_id: int,
        role: MembershipRole,
    ) -> None:
        membership = self.db.scalar(
            select(Membership).where(Membership.id == membership_id, Membership.account_id == account.id)
        )
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
        if role == MembershipRole.OWNER and actor_membership.role != MembershipRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner can assign owner role.")
        if membership.role == MembershipRole.OWNER and actor_membership.role != MembershipRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner can update another owner.")
        if membership.role == MembershipRole.OWNER and role != MembershipRole.OWNER:
            owner_count = self.db.scalar(
                select(func.count(Membership.id)).where(
                    Membership.account_id == account.id,
                    Membership.role == MembershipRole.OWNER,
                    Membership.status == MembershipStatus.ACTIVE,
                )
            )
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account must retain at least one owner.")
        membership.role = role
        self.db.commit()

    def revoke_onboarding_key(self, account: Account, key_id: int) -> None:
        onboarding_key = self.db.scalar(
            select(OnboardingKey).where(OnboardingKey.id == key_id, OnboardingKey.account_id == account.id)
        )
        if not onboarding_key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding key not found.")
        onboarding_key.revoked_at = datetime.now(UTC)
        self.db.commit()

    def resolve_active_account(self, user: User, requested_account_id: int | None) -> tuple[Account, Membership]:
        if user.is_superuser:
            return self._resolve_superuser_account(user, requested_account_id)

        memberships = [membership for membership in user.memberships if membership.status == MembershipStatus.ACTIVE]
        if not memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to an active account.")

        membership: Membership | None = None
        if requested_account_id is not None:
            membership = next((item for item in memberships if item.account_id == requested_account_id), None)
            if membership is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to the requested account.")
        elif len(memberships) == 1:
            membership = memberships[0]
        else:
            owner_membership = next((item for item in memberships if item.role == MembershipRole.OWNER), None)
            membership = owner_membership or memberships[0]

        account = self.db.scalar(
            select(Account)
            .where(Account.id == membership.account_id)
            .options(selectinload(Account.memberships))
        )
        if not account or not account.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active account is unavailable.")

        return account, membership

    def _resolve_superuser_account(self, user: User, requested_account_id: int | None) -> tuple[Account, Membership]:
        statement = select(Account).where(Account.is_active.is_(True)).options(selectinload(Account.memberships))
        if requested_account_id is not None:
            statement = statement.where(Account.id == requested_account_id)
            account = self.db.scalar(statement)
            if account is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested account was not found.")
        else:
            account = self.db.scalar(statement.order_by(Account.id.asc()))
            if account is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active account is available.")

        membership = Membership(
            account_id=account.id,
            user_id=user.id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )
        return account, membership

    def _get_valid_onboarding_key(self, key: str, user_email: str) -> OnboardingKey:
        onboarding_key = self.db.scalar(select(OnboardingKey).where(func.lower(OnboardingKey.key) == key.lower()))
        if not onboarding_key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding key not found.")
        if onboarding_key.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Onboarding key has been revoked.")
        if onboarding_key.expires_at and self._ensure_utc(onboarding_key.expires_at) <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Onboarding key has expired.")
        if onboarding_key.used_count >= onboarding_key.max_uses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Onboarding key has been exhausted.")
        if onboarding_key.invited_email and onboarding_key.invited_email.lower() != user_email.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Onboarding key is not valid for this email.")
        return onboarding_key

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
