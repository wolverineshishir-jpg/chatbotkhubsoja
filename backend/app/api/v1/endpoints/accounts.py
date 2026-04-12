from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_account_membership, get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.membership import Membership
from app.models.user import User
from app.schemas.account import (
    CreateAccountRequest,
    CreateOnboardingKeyRequest,
    CurrentAccountResponse,
    JoinAccountRequest,
    OnboardingKeyResponse,
)
from app.schemas.user import TeamMemberResponse
from app.services.account_service import AccountService

router = APIRouter()


@router.get("/current", response_model=CurrentAccountResponse)
def get_current_account(
    context: Annotated[tuple[Account, Membership], Depends(get_current_account_membership)],
) -> CurrentAccountResponse:
    account, membership = context
    return CurrentAccountResponse(
        id=account.id,
        name=account.name,
        slug=account.slug,
        role=membership.role,
        token_balance=account.token_balance,
        monthly_token_credit=account.monthly_token_credit,
    )


@router.get("/current/members", response_model=list[TeamMemberResponse])
def list_team_members(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("team:read"))],
    db: Session = Depends(get_db),
) -> list[TeamMemberResponse]:
    account, _ = context
    return AccountService(db).list_team_members(account.id)


@router.post("", response_model=CurrentAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: CreateAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> CurrentAccountResponse:
    return AccountService(db).create_account(current_user, payload)


@router.post("/join", response_model=CurrentAccountResponse)
def join_account(
    payload: JoinAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> CurrentAccountResponse:
    return AccountService(db).join_account(current_user, payload.onboarding_key)


@router.post("/current/onboarding-keys", response_model=OnboardingKeyResponse, status_code=status.HTTP_201_CREATED)
def create_onboarding_key(
    payload: CreateOnboardingKeyRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("key:manage"))],
    db: Session = Depends(get_db),
) -> OnboardingKeyResponse:
    account, _ = context
    return AccountService(db).create_onboarding_key(account, payload)
