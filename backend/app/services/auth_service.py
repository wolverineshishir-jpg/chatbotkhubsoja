from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.membership import Membership
from app.models.enums import UserRole, UserStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.account_service import AccountService
from app.services.user_management_service import UserManagementService
from app.services.user_service import build_user_response


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def login(self, payload: LoginRequest) -> TokenResponse:
        UserManagementService(self.db).ensure_owner_user()
        user = self._get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        if user.user_role != UserRole.OWNER and (not user.is_active or user.status != UserStatus.ACTIVE):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

        return self._issue_tokens(user)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        existing_user = self._get_user_by_email(payload.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_active=True,
            is_superuser=False,
            status=UserStatus.ACTIVE,
            user_role=UserRole.ADMIN,
            permissions_json=[],
        )
        self.db.add(user)
        self.db.flush()

        if payload.onboarding_key:
            AccountService(self.db).join_account(user, payload.onboarding_key)

        return self._issue_tokens(user)

    def refresh(self, payload: RefreshRequest) -> TokenResponse:
        token_data = self._decode_refresh_token(payload.refresh_token)
        user = self._get_user_by_id(int(token_data["sub"]))
        refresh_token = self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_jti == token_data["jti"])
        )
        if not user or not refresh_token or refresh_token.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid.")

        if self._ensure_utc(refresh_token.expires_at) <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired.")

        refresh_token.revoked_at = datetime.now(UTC)
        self.db.flush()

        response = self._issue_tokens(user)
        self.db.commit()
        self.db.refresh(user)
        return response

    def logout(self, user: User, payload: LogoutRequest) -> None:
        token_data = self._decode_refresh_token(payload.refresh_token)
        query = select(RefreshToken).where(RefreshToken.user_id == user.id)

        if not payload.logout_all:
            query = query.where(RefreshToken.token_jti == token_data["jti"])

        tokens = self.db.scalars(query).all()
        now = datetime.now(UTC)
        for token in tokens:
            token.revoked_at = now

        self.db.commit()

    def change_password(self, user: User, payload: ChangePasswordRequest) -> TokenResponse:
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

        if payload.current_password == payload.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password.",
            )

        user.hashed_password = hash_password(payload.new_password)

        now = datetime.now(UTC)
        tokens = self.db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)).all()
        for token in tokens:
            token.revoked_at = now

        self.db.flush()
        return self._issue_tokens(user)

    def get_current_user(self, user_id: int) -> User:
        user = self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        if user.user_role != UserRole.OWNER and (not user.is_active or user.status != UserStatus.ACTIVE):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")
        return user

    def _issue_tokens(self, user: User) -> TokenResponse:
        user = self._get_user_by_id(user.id)
        access_token, access_expires_at = create_access_token(str(user.id))
        refresh_token, token_jti, refresh_expires_at = create_refresh_token(str(user.id))

        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_jti=token_jti,
                expires_at=refresh_expires_at,
            )
        )
        self.db.commit()
        self.db.refresh(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=max(int((access_expires_at - datetime.now(UTC)).total_seconds()), 0),
            user=build_user_response(user),
        )

    def _decode_refresh_token(self, token: str) -> dict:
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        if payload.get("type") != "refresh" or "jti" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid.")

        return payload

    def _get_user_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.memberships).selectinload(Membership.account),
                selectinload(User.refresh_tokens),
            )
        )
        return self.db.scalar(statement)

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    def _get_user_by_id(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.memberships).selectinload(Membership.account),
                selectinload(User.refresh_tokens),
            )
        )
        return self.db.scalar(statement)
