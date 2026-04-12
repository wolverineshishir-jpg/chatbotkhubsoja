from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.platform_connection import (
    FacebookManualConnectRequest,
    FacebookOAuthCompleteRequest,
    FacebookOAuthCompleteResponse,
    FacebookOAuthConnectRequest,
    FacebookPageCandidateResponse,
    FacebookOAuthStartResponse,
    WhatsAppManualConnectRequest,
    PlatformConnectionCreateRequest,
    PlatformConnectionListResponse,
    PlatformConnectionResponse,
    PlatformConnectionStatusUpdateRequest,
    PlatformConnectionUpdateRequest,
)
from app.services.platform_connection_service import PlatformConnectionService
from app.services.audit_log_service import AuditContext, AuditLogService

router = APIRouter()


@router.get("", response_model=PlatformConnectionListResponse)
def list_platform_connections(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:read"))],
    db: Session = Depends(get_db),
) -> PlatformConnectionListResponse:
    account, _ = context
    items = PlatformConnectionService(db).list_connections(account)
    return PlatformConnectionListResponse(items=items, total=len(items))


@router.post("", response_model=PlatformConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_platform_connection(
    request: Request,
    payload: PlatformConnectionCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).create_connection(account, payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_CREATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Created {response.platform_type.value} connection "{response.name}".',
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/facebook/oauth/start", response_model=FacebookOAuthStartResponse)
def start_facebook_oauth(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FacebookOAuthStartResponse:
    account, _ = context
    response = FacebookOAuthStartResponse.model_validate(
        PlatformConnectionService(db).facebook.start_oauth(account=account, actor=current_user)
    )
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        description="Started Facebook Page OAuth flow.",
        metadata_json={"provider": "facebook", "state": response.state},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/facebook/oauth/complete", response_model=FacebookOAuthCompleteResponse)
def complete_facebook_oauth(
    request: Request,
    payload: FacebookOAuthCompleteRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FacebookOAuthCompleteResponse:
    account, _ = context
    result = PlatformConnectionService(db).facebook.complete_oauth(
        account=account,
        actor=current_user,
        state=payload.state,
        code=payload.code,
    )
    response = FacebookOAuthCompleteResponse(
        state=result["state"],
        pages=[FacebookPageCandidateResponse.model_validate(page) for page in result["pages"]],
    )
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        description="Completed Facebook OAuth token exchange.",
        metadata_json={"provider": "facebook", "pages_discovered": len(response.pages)},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/facebook/oauth/connect", response_model=PlatformConnectionResponse, status_code=status.HTTP_201_CREATED)
def connect_facebook_oauth_page(
    request: Request,
    payload: FacebookOAuthConnectRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    connection = PlatformConnectionService(db).facebook.connect_page_from_oauth(
        account=account,
        actor=current_user,
        state=payload.state,
        page_id=payload.page_id,
        connection_name=payload.connection_name,
        webhook_verify_token=payload.webhook_verify_token,
        webhook_secret=payload.webhook_secret,
    )
    response = PlatformConnectionService(db).get_connection(account, connection.id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_CREATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Connected Facebook Page "{response.name}" via OAuth.',
        metadata_json={"provider": "facebook", "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/facebook/manual-connect", response_model=PlatformConnectionResponse, status_code=status.HTTP_201_CREATED)
def connect_facebook_page_manually(
    request: Request,
    payload: FacebookManualConnectRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).connect_facebook_page_manually(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_CREATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Connected Facebook Page "{response.name}" manually.',
        metadata_json={"provider": "facebook", "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/whatsapp/manual-connect", response_model=PlatformConnectionResponse, status_code=status.HTTP_201_CREATED)
def connect_whatsapp_manually(
    request: Request,
    payload: WhatsAppManualConnectRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).connect_whatsapp_manually(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_CREATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Connected WhatsApp number "{response.name}" manually.',
        metadata_json={"provider": "whatsapp", "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.get("/{connection_id}", response_model=PlatformConnectionResponse)
def get_platform_connection(
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:read"))],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    return PlatformConnectionService(db).get_connection(account, connection_id)


@router.put("/{connection_id}", response_model=PlatformConnectionResponse)
def update_platform_connection(
    request: Request,
    connection_id: int,
    payload: PlatformConnectionUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).update_connection(account, connection_id, payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Updated connection "{response.name}".',
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{connection_id}/facebook/sync", response_model=PlatformConnectionResponse)
def sync_facebook_platform_connection(
    request: Request,
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).sync_facebook_connection(account=account, connection_id=connection_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Synced Facebook connection "{response.name}".',
        metadata_json={"provider": "facebook", "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{connection_id}/whatsapp/sync", response_model=PlatformConnectionResponse)
def sync_whatsapp_platform_connection(
    request: Request,
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).sync_whatsapp_connection(account=account, connection_id=connection_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Synced WhatsApp connection "{response.name}".',
        metadata_json={"provider": "whatsapp", "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{connection_id}/facebook/subscribe-webhooks", response_model=PlatformConnectionResponse)
def subscribe_facebook_platform_connection_webhooks(
    request: Request,
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).subscribe_facebook_webhooks(account=account, connection_id=connection_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Subscribed Facebook connection "{response.name}" to webhooks.',
        metadata_json={"provider": "facebook", "webhook_active": response.webhook.webhook_active},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.patch("/{connection_id}/status", response_model=PlatformConnectionResponse)
def update_platform_connection_status(
    request: Request,
    connection_id: int,
    payload: PlatformConnectionStatusUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).update_status(account, connection_id, payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_STATUS_UPDATED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Updated connection status to {response.status.value}.',
        metadata_json={"last_error": response.last_error},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{connection_id}/disconnect", response_model=PlatformConnectionResponse)
def disconnect_platform_connection(
    request: Request,
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlatformConnectionResponse:
    account, _ = context
    response = PlatformConnectionService(db).disconnect_connection(account, connection_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_DISCONNECTED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(response.id),
        description=f'Disconnected connection "{response.name}".',
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_platform_connection(
    request: Request,
    connection_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("connection:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    PlatformConnectionService(db).delete_connection(account, connection_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONNECTION_DELETED,
        resource_type=AuditResourceType.PLATFORM_CONNECTION,
        resource_id=str(connection_id),
        description="Deleted platform connection.",
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
