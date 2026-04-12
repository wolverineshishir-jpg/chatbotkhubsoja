from decimal import Decimal

from app.models.facebook_comment_reply import FacebookCommentReply
from app.models.enums import ActionUsageType, CommentReplyStatus, SyncJobType
from app.services.comment_moderation_service import CommentModerationService
from app.services.comment_reply_sender_service import CommentReplySenderService
from app.services.observability_service import ObservabilityService
from app.services.sync_job_service import SyncJobService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, base=LoggedTask, name="app.workers.comment_tasks.deliver_comment_reply")
@with_db_session
def deliver_comment_reply(self, reply_id: int, *, db) -> None:
    reply = db.get(FacebookCommentReply, reply_id)
    if not reply:
        return
    if reply.reply_status == CommentReplyStatus.SENT:
        return

    comment = reply.comment
    if comment is None:
        return

    result = CommentReplySenderService().send_comment_reply(
        comment=comment,
        reply=reply,
        connection=comment.platform_connection,
    )
    CommentModerationService(db).update_reply_delivery(
        reply_id=reply_id,
        reply_status=result.reply_status,
        external_reply_id=result.external_reply_id,
        error_message=result.error_message,
    )
    ObservabilityService(db).record_action_usage(
        account_id=reply.account_id,
        actor_user_id=reply.created_by_user_id,
        platform_connection_id=comment.platform_connection_id,
        platform_type=comment.platform_type,
        action_type=ActionUsageType.COMMENT_REPLY,
        reference_type="facebook_comment_reply",
        reference_id=str(reply.id),
        quantity=1,
        tokens_consumed=max(len(reply.content.split()), 1),
        estimated_cost=Decimal("0"),
        metadata_json={"reply_status": result.reply_status.value},
    )
    if result.reply_status == CommentReplyStatus.FAILED:
        SyncJobService(db).create_job(
            job_type=SyncJobType.RETRY_FAILED_SEND,
            account_id=reply.account_id,
            platform_connection_id=comment.platform_connection_id,
            dedupe_key=f"retry-comment-reply:{reply.id}",
            payload_json={"reply_id": reply.id},
        )
