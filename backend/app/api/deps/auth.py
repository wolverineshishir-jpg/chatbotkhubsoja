from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.permissions import has_user_permissions
from app.core.security import decode_token
from app.db.session import get_db
from app.models.account import Account
from app.models.membership import Membership
from app.models.user import User
from app.services.account_service import AccountService
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided.")

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

    return AuthService(db).get_current_user(int(payload["sub"]))


def get_current_account_membership(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    x_account_id: Annotated[int | None, Header(alias="X-Account-ID")] = None,
) -> tuple[Account, Membership]:
    return AccountService(db).resolve_active_account(current_user, x_account_id)


def require_permissions(*permissions: str) -> Callable:
    def dependency(
        context: Annotated[tuple[Account, Membership], Depends(get_current_account_membership)],
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> tuple[Account, Membership]:
        account, membership = context
        if not has_user_permissions(current_user.user_role, membership.role, current_user.permissions_json or [], permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required permissions.")
        return account, membership

    return dependency
