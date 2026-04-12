from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_account_membership, get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    CreateAdminRequest,
    CreateSuperAdminRequest,
    ManagedUserResponse,
    UpdateAdminRequest,
    UpdateSuperAdminRequest,
)
from app.services.audit_log_service import AuditContext, AuditLogService
from app.services.user_management_service import UserManagementService

router = APIRouter()


@router.get("", response_model=list[ManagedUserResponse])
def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    x_account_id: Annotated[int | None, Header(alias="X-Account-ID")] = None,
    db: Session = Depends(get_db),
) -> list[ManagedUserResponse]:
    return UserManagementService(db).list_users_for_actor(current_user, account_id=x_account_id)


@router.post("/super-admins", response_model=ManagedUserResponse, status_code=status.HTTP_201_CREATED)
def create_super_admin(
    request: Request,
    payload: CreateSuperAdminRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ManagedUserResponse:
    response = UserManagementService(db).create_super_admin(current_user, payload)
    account = db.get(Account, response.account_id) if response.account_id else None
    if account:
        AuditLogService(db).record(
            account=account,
            actor=current_user,
            action_type=AuditActionType.ADMIN_ACTION,
            resource_type=AuditResourceType.TEAM,
            resource_id=str(response.id),
            description="Created super admin.",
            metadata_json={"email": response.email, "account_slug": response.account_slug},
            context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
        )
    return response


@router.patch("/super-admins/{user_id}", response_model=ManagedUserResponse)
def update_super_admin(
    request: Request,
    user_id: int,
    payload: UpdateSuperAdminRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ManagedUserResponse:
    response = UserManagementService(db).update_super_admin(current_user, user_id, payload)
    account = db.get(Account, response.account_id) if response.account_id else None
    if account:
        AuditLogService(db).record(
            account=account,
            actor=current_user,
            action_type=AuditActionType.ADMIN_ACTION,
            resource_type=AuditResourceType.TEAM,
            resource_id=str(user_id),
            description="Updated super admin.",
            metadata_json={"status": response.status.value},
            context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
        )
    return response


@router.post("/admins", response_model=ManagedUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    request: Request,
    payload: CreateAdminRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    context: Annotated[tuple[Account, Membership], Depends(get_current_account_membership)],
    db: Session = Depends(get_db),
) -> ManagedUserResponse:
    account, _ = context
    response = UserManagementService(db).create_admin(current_user, account, payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.TEAM,
        resource_id=str(response.id),
        description="Created admin user.",
        metadata_json={"email": response.email, "permissions": response.permissions},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.patch("/admins/{user_id}", response_model=ManagedUserResponse)
def update_admin(
    request: Request,
    user_id: int,
    payload: UpdateAdminRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ManagedUserResponse:
    response = UserManagementService(db).update_admin(current_user, user_id, payload)
    account = db.get(Account, response.account_id) if response.account_id else None
    if account:
        AuditLogService(db).record(
            account=account,
            actor=current_user,
            action_type=AuditActionType.ADMIN_ACTION,
            resource_type=AuditResourceType.TEAM,
            resource_id=str(user_id),
            description="Updated admin user.",
            metadata_json={"status": response.status.value, "permissions": response.permissions},
            context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
        )
    return response


@router.delete("/admins/{user_id}", response_model=MessageResponse)
def delete_admin(
    request: Request,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MessageResponse:
    UserManagementService(db).delete_admin(current_user, user_id)
    return MessageResponse(message="Admin user disabled successfully.")
