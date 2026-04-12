from app.models.webhook_event import WebhookEvent
from app.services.webhook_processing_service import WebhookProcessingService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    base=LoggedTask,
    name="app.workers.webhook_tasks.process_webhook_event",
)
@with_db_session
def process_webhook_event(self, event_id: int, *, db) -> dict:
    event = db.get(WebhookEvent, event_id)
    if not event:
        return {"event_id": event_id, "status": "missing"}
    if event.status.value in {"processed", "ignored"}:
        return {"event_id": event_id, "status": event.status.value}

    service = WebhookProcessingService(db)
    service.mark_processing(event, task_id=self.request.id)
    try:
        return service.process_event(event_id)
    except Exception as exc:
        service.mark_failed(event, error_message=str(exc))
        raise
