from datetime import UTC, datetime

from sqlalchemy import select

from app.models.enums import PostStatus, SyncJobType
from app.models.social_post import SocialPost
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.sync_job_service import SyncJobService
from app.services.token_maintenance_service import TokenMaintenanceService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app
from app.workers.sync_job_tasks import execute_sync_job


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.maintenance_tasks.scan_due_scheduled_posts",
)
@with_db_session
def scan_due_scheduled_posts(self, *, db) -> dict:
    service = SyncJobService(db)
    posts = db.scalars(
        select(SocialPost).where(
            SocialPost.status == PostStatus.SCHEDULED,
            SocialPost.scheduled_for.is_not(None),
            SocialPost.scheduled_for <= datetime.now(UTC),
        )
    ).all()
    created = 0
    for post in posts:
        job = service.create_job(
            job_type=SyncJobType.SCHEDULED_POST_PUBLISH,
            account_id=post.account_id,
            platform_connection_id=post.platform_connection_id,
            scheduled_for=post.scheduled_for or datetime.now(UTC),
            dedupe_key=f"scheduled-post:{post.id}",
            payload_json={"post_id": post.id},
        )
        if job.created_at == job.updated_at and job.attempts == 0:
            created += 1
    return {"created_jobs": created, "matched_posts": len(posts)}


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.maintenance_tasks.dispatch_due_sync_jobs",
)
@with_db_session
def dispatch_due_sync_jobs(self, *, db) -> dict:
    jobs = SyncJobService(db).list_due_jobs(limit=100)
    for job in jobs:
        execute_sync_job.delay(job.id)
    return {"dispatched": len(jobs)}


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.maintenance_tasks.scan_due_automation_workflows",
)
@with_db_session
def scan_due_automation_workflows(self, *, db) -> dict:
    created = AutomationWorkflowService(db).queue_due_scheduled_workflows()
    return {"created_jobs": created}


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.maintenance_tasks.issue_monthly_token_credits",
)
@with_db_session
def issue_monthly_token_credits(self, *, db) -> dict:
    updated_accounts = TokenMaintenanceService(db).apply_monthly_credits()
    return {"updated_accounts": updated_accounts}


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.maintenance_tasks.expire_tokens",
)
@with_db_session
def expire_tokens(self, *, db) -> dict:
    return TokenMaintenanceService(db).expire_tokens()
