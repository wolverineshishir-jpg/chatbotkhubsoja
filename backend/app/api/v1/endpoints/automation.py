from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.automation import (
    AutomationWorkflowCreateRequest,
    AutomationWorkflowListResponse,
    AutomationWorkflowResponse,
    AutomationWorkflowRunResponse,
    AutomationWorkflowUpdateRequest,
)
from app.services.audit_log_service import AuditContext, AuditLogService
from app.services.automation_workflow_service import AutomationWorkflowService

router = APIRouter()


@router.get("/workflows", response_model=AutomationWorkflowListResponse)
def list_automation_workflows(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:read"))],
    db: Session = Depends(get_db),
) -> AutomationWorkflowListResponse:
    account, _ = context
    return AutomationWorkflowService(db).list_workflows(account=account)


@router.post("/workflows", response_model=AutomationWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_automation_workflow(
    request: Request,
    payload: AutomationWorkflowCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AutomationWorkflowResponse:
    account, _ = context
    response = AutomationWorkflowService(db).create_workflow(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.AUTOMATION_WORKFLOW_CREATED,
        resource_type=AuditResourceType.AUTOMATION_WORKFLOW,
        resource_id=str(response.id),
        description=f'Created automation workflow "{response.name}".',
        metadata_json={"trigger_type": response.trigger_type.value, "action_type": response.action_type.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.get("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
def get_automation_workflow(
    workflow_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:read"))],
    db: Session = Depends(get_db),
) -> AutomationWorkflowResponse:
    account, _ = context
    return AutomationWorkflowService(db).get_workflow(account=account, workflow_id=workflow_id)


@router.put("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
def update_automation_workflow(
    request: Request,
    workflow_id: int,
    payload: AutomationWorkflowUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AutomationWorkflowResponse:
    account, _ = context
    response = AutomationWorkflowService(db).update_workflow(account=account, workflow_id=workflow_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.AUTOMATION_WORKFLOW_UPDATED,
        resource_type=AuditResourceType.AUTOMATION_WORKFLOW,
        resource_id=str(response.id),
        description=f'Updated automation workflow "{response.name}".',
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_automation_workflow(
    request: Request,
    workflow_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    service = AutomationWorkflowService(db)
    workflow = service.get_workflow(account=account, workflow_id=workflow_id)
    service.delete_workflow(account=account, workflow_id=workflow_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.AUTOMATION_WORKFLOW_DELETED,
        resource_type=AuditResourceType.AUTOMATION_WORKFLOW,
        resource_id=str(workflow_id),
        description=f'Deleted automation workflow "{workflow.name}".',
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/workflows/{workflow_id}/run", response_model=AutomationWorkflowRunResponse)
def run_automation_workflow_now(
    request: Request,
    workflow_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("automation:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AutomationWorkflowRunResponse:
    account, _ = context
    workflow, sync_job_id = AutomationWorkflowService(db).run_workflow_now(account=account, workflow_id=workflow_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.AUTOMATION_WORKFLOW_TRIGGERED,
        resource_type=AuditResourceType.AUTOMATION_WORKFLOW,
        resource_id=str(workflow.id),
        description=f'Manually queued automation workflow "{workflow.name}".',
        metadata_json={"sync_job_id": sync_job_id},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return AutomationWorkflowRunResponse(workflow=workflow, sync_job_id=sync_job_id)
