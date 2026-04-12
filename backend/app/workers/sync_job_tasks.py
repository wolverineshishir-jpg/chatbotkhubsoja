from app.models.enums import SyncJobStatus, SyncJobType
from app.models.sync_job import SyncJob
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.ai.orchestration_service import AIOrchestrationService
from app.services.sync_job_service import SyncJobService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.sync_job_tasks.execute_sync_job",
)
@with_db_session
def execute_sync_job(self, sync_job_id: int, *, db) -> dict:
    job = db.get(SyncJob, sync_job_id)
    if not job:
        return {"sync_job_id": sync_job_id, "status": "missing"}
    if job.status == SyncJobStatus.COMPLETED:
        return {"sync_job_id": sync_job_id, "status": "completed"}

    service = SyncJobService(db)
    service.mark_running(job, task_id=self.request.id)
    try:
        result = _dispatch_sync_job(job, db)
        service.mark_completed(job, result_json=result)
        return result
    except Exception as exc:
        service.mark_failed(job, error_message=str(exc))
        raise


def _dispatch_sync_job(job: SyncJob, db) -> dict:
    if job.job_type == SyncJobType.AI_REPLY_GENERATION:
        return _handle_ai_reply_generation(job, db)
    if job.job_type == SyncJobType.AUTOMATION_RULE_EXECUTION:
        return _handle_automation_rule_execution(job, db)
    if job.job_type == SyncJobType.SCHEDULED_POST_PUBLISH:
        return _handle_scheduled_post_publish(job)
    if job.job_type == SyncJobType.RETRY_FAILED_SEND:
        return _handle_retry_failed_send(job)
    if job.job_type == SyncJobType.TOKEN_EXPIRATION:
        return {"sync_job_id": job.id, "status": "delegated_to_scheduler"}
    if job.job_type == SyncJobType.TOKEN_MONTHLY_CREDIT:
        return {"sync_job_id": job.id, "status": "delegated_to_scheduler"}
    return {"sync_job_id": job.id, "status": "no_handler"}


def _handle_ai_reply_generation(job: SyncJob, db) -> dict:
    payload = job.payload_json
    orchestrator = AIOrchestrationService(db)
    if payload.get("conversation_id"):
        outcome = orchestrator.auto_generate_for_message(
            account_id=job.account_id or 0,
            conversation_id=payload["conversation_id"],
        )
        return {
            "sync_job_id": job.id,
            "status": "generated",
            "conversation_id": payload["conversation_id"],
            "draft_reference_type": outcome.draft_reference_type,
            "draft_object_id": outcome.draft_object_id,
            "total_tokens": outcome.total_tokens,
        }
    if payload.get("comment_id"):
        outcome = orchestrator.auto_generate_for_comment(
            account_id=job.account_id or 0,
            comment_id=payload["comment_id"],
        )
        return {
            "sync_job_id": job.id,
            "status": "generated",
            "comment_id": payload["comment_id"],
            "draft_reference_type": outcome.draft_reference_type,
            "draft_object_id": outcome.draft_object_id,
            "total_tokens": outcome.total_tokens,
        }
    return {"sync_job_id": job.id, "status": "skipped"}


def _handle_scheduled_post_publish(job: SyncJob) -> dict:
    post_id = job.payload_json.get("post_id")
    if not post_id:
        return {"sync_job_id": job.id, "status": "skipped", "detail": "No post_id in payload."}

    publish_social_post.delay(post_id)
    return {
        "sync_job_id": job.id,
        "status": "queued_publish",
        "post_id": post_id,
        "detail": "Scheduled post publish queued.",
    }


def _handle_automation_rule_execution(job: SyncJob, db) -> dict:
    workflow_id = job.payload_json.get("workflow_id")
    if not workflow_id:
        return {"sync_job_id": job.id, "status": "skipped", "detail": "Missing workflow_id."}
    result = AutomationWorkflowService(db).execute_job(workflow_id=workflow_id, payload_json=job.payload_json)
    return {"sync_job_id": job.id, **result}


def _handle_retry_failed_send(job: SyncJob) -> dict:
    payload = job.payload_json
    if payload.get("message_id"):
        deliver_outbound_message.delay(payload["message_id"])
        return {"sync_job_id": job.id, "status": "queued_message_retry", "message_id": payload["message_id"]}
    if payload.get("reply_id"):
        deliver_comment_reply.delay(payload["reply_id"])
        return {"sync_job_id": job.id, "status": "queued_comment_retry", "reply_id": payload["reply_id"]}
    if payload.get("post_id"):
        publish_social_post.delay(payload["post_id"])
        return {"sync_job_id": job.id, "status": "queued_post_retry", "post_id": payload["post_id"]}
    return {"sync_job_id": job.id, "status": "skipped"}


from app.workers.comment_tasks import deliver_comment_reply
from app.workers.inbox_tasks import deliver_outbound_message
from app.workers.post_tasks import publish_social_post
