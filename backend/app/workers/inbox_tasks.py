from decimal import Decimal

from app.models.message import Message
from app.models.enums import ActionUsageType, MessageDeliveryStatus, SyncJobType
from app.services.inbox_service import InboxService
from app.services.message_sender_service import MessageSenderService
from app.services.observability_service import ObservabilityService
from app.services.sync_job_service import SyncJobService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, base=LoggedTask, name="app.workers.inbox_tasks.deliver_outbound_message")
@with_db_session
def deliver_outbound_message(self, message_id: int, *, db) -> None:
    message = db.get(Message, message_id)
    if not message:
        return
    if message.delivery_status in {MessageDeliveryStatus.SENT, MessageDeliveryStatus.DELIVERED}:
        return

    conversation = message.conversation
    if conversation is None:
        return

    result = MessageSenderService().send_outbound_message(
        conversation=conversation,
        message=message,
        connection=conversation.platform_connection,
    )
    InboxService(db).update_delivery_status(
        message_id=message_id,
        delivery_status=result.delivery_status,
        external_message_id=result.external_message_id,
        error_message=result.error_message,
    )
    ObservabilityService(db).record_action_usage(
        account_id=message.account_id,
        actor_user_id=message.created_by_user_id,
        platform_connection_id=conversation.platform_connection_id,
        platform_type=conversation.platform_type,
        action_type=ActionUsageType.OUTBOUND_MESSAGE,
        reference_type="message",
        reference_id=str(message.id),
        quantity=1,
        tokens_consumed=max(len(message.content.split()), 1),
        estimated_cost=Decimal("0"),
        metadata_json={"delivery_status": result.delivery_status.value},
    )
    if result.delivery_status == MessageDeliveryStatus.FAILED:
        SyncJobService(db).create_job(
            job_type=SyncJobType.RETRY_FAILED_SEND,
            account_id=message.account_id,
            platform_connection_id=conversation.platform_connection_id,
            dedupe_key=f"retry-message:{message.id}",
            payload_json={"message_id": message.id},
        )
