from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.ai_agent import AIAgent
from app.models.automation_workflow import AutomationWorkflow
from app.models.conversation import Conversation
from app.models.enums import (
    AutomationActionType,
    AutomationTriggerType,
    AutomationWorkflowStatus,
    SyncJobType,
)
from app.models.facebook_comment import FacebookComment
from app.models.message import Message
from app.models.platform_connection import PlatformConnection
from app.schemas.automation import (
    AutomationActionConfig,
    AutomationTriggerFilters,
    AutomationWorkflowCreateRequest,
    AutomationWorkflowListResponse,
    AutomationWorkflowResponse,
    AutomationWorkflowUpdateRequest,
)
from app.services.ai.orchestration_service import AIOrchestrationService
from app.services.sync_job_service import SyncJobService


class AutomationWorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.sync_jobs = SyncJobService(db)

    def list_workflows(self, *, account: Account) -> AutomationWorkflowListResponse:
        statement = (
            select(AutomationWorkflow)
            .where(AutomationWorkflow.account_id == account.id)
            .order_by(AutomationWorkflow.created_at.desc(), AutomationWorkflow.id.desc())
        )
        items = self.db.scalars(statement).all()
        total = self.db.scalar(
            select(func.count(AutomationWorkflow.id)).where(AutomationWorkflow.account_id == account.id)
        ) or 0
        return AutomationWorkflowListResponse(
            items=[AutomationWorkflowResponse.model_validate(item) for item in items],
            total=total,
        )

    def get_workflow(self, *, account: Account, workflow_id: int) -> AutomationWorkflowResponse:
        workflow = self._get_owned_workflow(account.id, workflow_id)
        return AutomationWorkflowResponse.model_validate(workflow)

    def create_workflow(self, *, account: Account, payload: AutomationWorkflowCreateRequest) -> AutomationWorkflowResponse:
        connection = self._resolve_connection(account.id, payload.platform_connection_id)
        agent = self._resolve_agent(account.id, payload.ai_agent_id)
        workflow = AutomationWorkflow(
            account_id=account.id,
            platform_connection_id=connection.id if connection else None,
            ai_agent_id=agent.id if agent else None,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            trigger_type=payload.trigger_type,
            action_type=payload.action_type,
            delay_seconds=payload.delay_seconds,
            trigger_filters_json=payload.trigger_filters.model_dump(),
            action_config_json=payload.action_config.model_dump(),
            schedule_timezone=payload.schedule_timezone,
            schedule_local_time=payload.schedule_local_time,
            next_run_at=self._compute_next_run_at(
                trigger_type=payload.trigger_type,
                schedule_timezone=payload.schedule_timezone,
                schedule_local_time=payload.schedule_local_time,
            ),
            last_result_json={},
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return AutomationWorkflowResponse.model_validate(workflow)

    def update_workflow(
        self,
        *,
        account: Account,
        workflow_id: int,
        payload: AutomationWorkflowUpdateRequest,
    ) -> AutomationWorkflowResponse:
        workflow = self._get_owned_workflow(account.id, workflow_id)
        data = payload.model_dump(exclude_unset=True)
        trigger_type = data.get("trigger_type", workflow.trigger_type)
        action_type = data.get("action_type", workflow.action_type)

        if "name" in data:
            workflow.name = data["name"]
        if "description" in data:
            workflow.description = data["description"]
        if "status" in data:
            workflow.status = data["status"]
        if "platform_connection_id" in data:
            connection = self._resolve_connection(account.id, data["platform_connection_id"])
            workflow.platform_connection_id = connection.id if connection else None
        if "ai_agent_id" in data:
            agent = self._resolve_agent(account.id, data["ai_agent_id"])
            workflow.ai_agent_id = agent.id if agent else None
        if "delay_seconds" in data:
            workflow.delay_seconds = data["delay_seconds"]
        if "trigger_filters" in data:
            workflow.trigger_filters_json = data["trigger_filters"].model_dump()
        if "action_config" in data:
            workflow.action_config_json = data["action_config"].model_dump()
        if "trigger_type" in data:
            workflow.trigger_type = data["trigger_type"]
        if "action_type" in data:
            workflow.action_type = data["action_type"]
        if "schedule_timezone" in data:
            workflow.schedule_timezone = data["schedule_timezone"]
        if "schedule_local_time" in data:
            workflow.schedule_local_time = data["schedule_local_time"]

        self._validate_workflow_shape(
            trigger_type=trigger_type,
            action_type=action_type,
            schedule_timezone=workflow.schedule_timezone,
            schedule_local_time=workflow.schedule_local_time,
        )
        workflow.next_run_at = self._compute_next_run_at(
            trigger_type=trigger_type,
            schedule_timezone=workflow.schedule_timezone,
            schedule_local_time=workflow.schedule_local_time,
            reference=workflow.last_triggered_at,
        )
        self.db.commit()
        self.db.refresh(workflow)
        return AutomationWorkflowResponse.model_validate(workflow)

    def delete_workflow(self, *, account: Account, workflow_id: int) -> None:
        workflow = self._get_owned_workflow(account.id, workflow_id)
        self.db.delete(workflow)
        self.db.commit()

    def run_workflow_now(self, *, account: Account, workflow_id: int) -> tuple[AutomationWorkflowResponse, int]:
        workflow = self._get_owned_workflow(account.id, workflow_id)
        job = self._create_execution_job(
            workflow=workflow,
            payload_json={"workflow_id": workflow.id, "manual_run": True},
            dedupe_key=f"automation:manual:{workflow.id}:{self._utcnow().isoformat()}",
            scheduled_for=self._utcnow(),
        )
        return AutomationWorkflowResponse.model_validate(workflow), job.id

    def queue_matching_message_workflows(self, *, conversation: Conversation, message: Message) -> list[int]:
        workflows = self._list_active_trigger_workflows(
            account_id=conversation.account_id,
            trigger_type=AutomationTriggerType.INBOX_MESSAGE_RECEIVED,
            platform_connection_id=conversation.platform_connection_id,
        )
        created_jobs: list[int] = []
        for workflow in workflows:
            if not self._matches_filters(workflow, content=message.content, customer_name=conversation.customer_name):
                continue
            job = self._create_execution_job(
                workflow=workflow,
                payload_json={
                    "workflow_id": workflow.id,
                    "conversation_id": conversation.id,
                    "message_id": message.id,
                },
                dedupe_key=f"automation:workflow:{workflow.id}:message:{message.id}",
                scheduled_for=self._utcnow() + timedelta(seconds=workflow.delay_seconds),
            )
            created_jobs.append(job.id)
        return created_jobs

    def queue_matching_comment_workflows(self, *, comment: FacebookComment) -> list[int]:
        workflows = self._list_active_trigger_workflows(
            account_id=comment.account_id,
            trigger_type=AutomationTriggerType.FACEBOOK_COMMENT_CREATED,
            platform_connection_id=comment.platform_connection_id,
        )
        created_jobs: list[int] = []
        for workflow in workflows:
            if not self._matches_filters(workflow, content=comment.comment_text, customer_name=comment.commenter_name):
                continue
            job = self._create_execution_job(
                workflow=workflow,
                payload_json={"workflow_id": workflow.id, "comment_id": comment.id},
                dedupe_key=f"automation:workflow:{workflow.id}:comment:{comment.id}",
                scheduled_for=self._utcnow() + timedelta(seconds=workflow.delay_seconds),
            )
            created_jobs.append(job.id)
        return created_jobs

    def queue_due_scheduled_workflows(self) -> int:
        workflows = self.db.scalars(
            select(AutomationWorkflow).where(
                AutomationWorkflow.trigger_type == AutomationTriggerType.SCHEDULED_DAILY,
                AutomationWorkflow.status == AutomationWorkflowStatus.ACTIVE,
                AutomationWorkflow.next_run_at.is_not(None),
                AutomationWorkflow.next_run_at <= self._utcnow(),
            )
        ).all()
        created = 0
        for workflow in workflows:
            run_at = workflow.next_run_at or self._utcnow()
            job = self._create_execution_job(
                workflow=workflow,
                payload_json={"workflow_id": workflow.id, "scheduled_run": run_at.isoformat()},
                dedupe_key=f"automation:scheduled:{workflow.id}:{run_at.isoformat()}",
                scheduled_for=run_at,
            )
            workflow.next_run_at = self._compute_next_run_at(
                trigger_type=workflow.trigger_type,
                schedule_timezone=workflow.schedule_timezone,
                schedule_local_time=workflow.schedule_local_time,
                reference=run_at,
            )
            if job.created_at == job.updated_at and job.attempts == 0:
                created += 1
        self.db.commit()
        return created

    def execute_job(self, *, workflow_id: int, payload_json: dict) -> dict:
        workflow = self.db.get(AutomationWorkflow, workflow_id)
        if workflow is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation workflow not found.")
        if workflow.status != AutomationWorkflowStatus.ACTIVE:
            return {"workflow_id": workflow_id, "status": "skipped", "detail": "Workflow is not active."}

        account = self.db.get(Account, workflow.account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
        orchestrator = AIOrchestrationService(self.db)
        config = AutomationActionConfig.model_validate(workflow.action_config_json or {})

        if workflow.action_type == AutomationActionType.GENERATE_INBOX_REPLY:
            conversation_id = payload_json.get("conversation_id")
            if not conversation_id:
                return {"workflow_id": workflow_id, "status": "skipped", "detail": "Missing conversation_id."}
            outcome = orchestrator.generate_inbox_reply(
                account=account,
                conversation_id=conversation_id,
                actor=None,
                ai_agent_id=workflow.ai_agent_id,
                platform_connection_id=workflow.platform_connection_id,
                instructions=config.instructions,
                send_now=config.send_now,
                persist_draft=True,
            )
        elif workflow.action_type == AutomationActionType.GENERATE_COMMENT_REPLY:
            comment_id = payload_json.get("comment_id")
            if not comment_id:
                return {"workflow_id": workflow_id, "status": "skipped", "detail": "Missing comment_id."}
            outcome = orchestrator.generate_comment_reply(
                account=account,
                comment_id=comment_id,
                actor=None,
                ai_agent_id=workflow.ai_agent_id,
                instructions=config.instructions,
                send_now=config.send_now,
                persist_draft=True,
            )
        elif workflow.action_type == AutomationActionType.GENERATE_POST_DRAFT:
            outcome = orchestrator.generate_post(
                account=account,
                actor=None,
                platform_connection_id=workflow.platform_connection_id,
                ai_agent_id=workflow.ai_agent_id,
                title_hint=config.title_hint,
                instructions=config.instructions,
                persist_draft=True,
            )
        else:
            return {"workflow_id": workflow_id, "status": "skipped", "detail": "Unsupported automation action."}

        workflow.last_triggered_at = self._utcnow()
        workflow.last_result_json = {
            "status": "generated",
            "draft_reference_type": outcome.draft_reference_type,
            "draft_object_id": outcome.draft_object_id,
            "total_tokens": outcome.total_tokens,
        }
        if workflow.trigger_type == AutomationTriggerType.SCHEDULED_DAILY:
            workflow.next_run_at = self._compute_next_run_at(
                trigger_type=workflow.trigger_type,
                schedule_timezone=workflow.schedule_timezone,
                schedule_local_time=workflow.schedule_local_time,
                reference=workflow.last_triggered_at,
            )
        self.db.commit()
        return {
            "workflow_id": workflow.id,
            "status": "generated",
            "draft_reference_type": outcome.draft_reference_type,
            "draft_object_id": outcome.draft_object_id,
            "total_tokens": outcome.total_tokens,
        }

    def has_active_workflows(
        self,
        *,
        account_id: int,
        trigger_type: AutomationTriggerType,
        platform_connection_id: int | None,
    ) -> bool:
        statement = select(func.count(AutomationWorkflow.id)).where(
            AutomationWorkflow.account_id == account_id,
            AutomationWorkflow.trigger_type == trigger_type,
            AutomationWorkflow.status == AutomationWorkflowStatus.ACTIVE,
        )
        if platform_connection_id is not None:
            statement = statement.where(
                (AutomationWorkflow.platform_connection_id.is_(None))
                | (AutomationWorkflow.platform_connection_id == platform_connection_id)
            )
        return (self.db.scalar(statement) or 0) > 0

    def _list_active_trigger_workflows(
        self,
        *,
        account_id: int,
        trigger_type: AutomationTriggerType,
        platform_connection_id: int | None,
    ) -> list[AutomationWorkflow]:
        statement = (
            select(AutomationWorkflow)
            .where(
                AutomationWorkflow.account_id == account_id,
                AutomationWorkflow.trigger_type == trigger_type,
                AutomationWorkflow.status == AutomationWorkflowStatus.ACTIVE,
            )
            .order_by(AutomationWorkflow.id.asc())
        )
        if platform_connection_id is not None:
            statement = statement.where(
                (AutomationWorkflow.platform_connection_id.is_(None))
                | (AutomationWorkflow.platform_connection_id == platform_connection_id)
            )
        return self.db.scalars(statement).all()

    def _matches_filters(self, workflow: AutomationWorkflow, *, content: str, customer_name: str | None) -> bool:
        filters = AutomationTriggerFilters.model_validate(workflow.trigger_filters_json or {})
        lowered_content = content.lower()
        lowered_customer = (customer_name or "").lower()
        if filters.include_keywords and not any(keyword.lower() in lowered_content for keyword in filters.include_keywords):
            return False
        if any(keyword.lower() in lowered_content for keyword in filters.exclude_keywords):
            return False
        if filters.customer_contains and filters.customer_contains.lower() not in lowered_customer:
            return False
        return True

    def _create_execution_job(
        self,
        *,
        workflow: AutomationWorkflow,
        payload_json: dict,
        dedupe_key: str,
        scheduled_for: datetime,
    ):
        return self.sync_jobs.create_job(
            job_type=SyncJobType.AUTOMATION_RULE_EXECUTION,
            account_id=workflow.account_id,
            platform_connection_id=workflow.platform_connection_id,
            scheduled_for=scheduled_for,
            dedupe_key=dedupe_key,
            payload_json=payload_json,
        )

    def _get_owned_workflow(self, account_id: int, workflow_id: int) -> AutomationWorkflow:
        workflow = self.db.scalar(
            select(AutomationWorkflow).where(
                AutomationWorkflow.id == workflow_id,
                AutomationWorkflow.account_id == account_id,
            )
        )
        if workflow is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation workflow not found.")
        return workflow

    def _resolve_connection(self, account_id: int, connection_id: int | None) -> PlatformConnection | None:
        if connection_id is None:
            return None
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.id == connection_id,
                PlatformConnection.account_id == account_id,
            )
        )
        if connection is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")
        return connection

    def _resolve_agent(self, account_id: int, agent_id: int | None) -> AIAgent | None:
        if agent_id is None:
            return None
        agent = self.db.scalar(select(AIAgent).where(AIAgent.id == agent_id, AIAgent.account_id == account_id))
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI agent not found.")
        return agent

    def _validate_workflow_shape(
        self,
        *,
        trigger_type: AutomationTriggerType,
        action_type: AutomationActionType,
        schedule_timezone: str | None,
        schedule_local_time: str | None,
    ) -> None:
        AutomationWorkflowCreateRequest(
            name="Validation",
            trigger_type=trigger_type,
            action_type=action_type,
            status=AutomationWorkflowStatus.DRAFT,
            trigger_filters=AutomationTriggerFilters(),
            action_config=AutomationActionConfig(),
            schedule_timezone=schedule_timezone,
            schedule_local_time=schedule_local_time,
        )

    def _compute_next_run_at(
        self,
        *,
        trigger_type: AutomationTriggerType,
        schedule_timezone: str | None,
        schedule_local_time: str | None,
        reference: datetime | None = None,
    ) -> datetime | None:
        if trigger_type != AutomationTriggerType.SCHEDULED_DAILY:
            return None
        if not schedule_timezone or not schedule_local_time:
            return None
        zone = self._resolve_timezone(schedule_timezone)
        hours, minutes = [int(part) for part in schedule_local_time.split(":")]
        current_reference = self._coerce_utc(reference or self._utcnow()).astimezone(zone)
        candidate = datetime.combine(current_reference.date(), time(hours, minutes), tzinfo=zone)
        if candidate <= current_reference:
            candidate = candidate + timedelta(days=1)
        return candidate.astimezone(UTC)

    @staticmethod
    def _resolve_timezone(value: str) -> ZoneInfo:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid schedule timezone.") from exc

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
