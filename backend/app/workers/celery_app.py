from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings)

celery_app = Celery(
    "automation_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    task_routes={
        "app.workers.webhook_tasks.*": {"queue": "webhooks"},
        "app.workers.sync_job_tasks.*": {"queue": "sync"},
        "app.workers.maintenance_tasks.*": {"queue": "maintenance"},
        "app.workers.inbox_tasks.*": {"queue": "messages"},
        "app.workers.comment_tasks.*": {"queue": "comments"},
        "app.workers.post_tasks.*": {"queue": "posts"},
    },
    beat_schedule={
        "scan-due-scheduled-posts": {
            "task": "app.workers.maintenance_tasks.scan_due_scheduled_posts",
            "schedule": 60.0,
        },
        "scan-due-automation-workflows": {
            "task": "app.workers.maintenance_tasks.scan_due_automation_workflows",
            "schedule": 60.0,
        },
        "dispatch-due-sync-jobs": {
            "task": "app.workers.maintenance_tasks.dispatch_due_sync_jobs",
            "schedule": 60.0,
        },
        "issue-monthly-token-credits": {
            "task": "app.workers.maintenance_tasks.issue_monthly_token_credits",
            "schedule": crontab(minute="15", hour="0"),
        },
        "expire-tokens": {
            "task": "app.workers.maintenance_tasks.expire_tokens",
            "schedule": crontab(minute="0"),
        },
    },
)

celery_app.autodiscover_tasks(
    [
        "app.workers.comment_tasks",
        "app.workers.inbox_tasks",
        "app.workers.maintenance_tasks",
        "app.workers.post_tasks",
        "app.workers.sync_job_tasks",
        "app.workers.webhook_tasks",
    ]
)
