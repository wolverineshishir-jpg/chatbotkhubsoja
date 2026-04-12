from decimal import Decimal

from app.models.social_post import SocialPost
from app.models.enums import ActionUsageType, PostStatus, SyncJobType
from app.services.observability_service import ObservabilityService
from app.services.post_publisher_service import SocialPostPublisherService
from app.services.post_service import PostService
from app.services.sync_job_service import SyncJobService
from app.workers.base import LoggedTask, with_db_session
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, base=LoggedTask, name="app.workers.post_tasks.publish_social_post")
@with_db_session
def publish_social_post(self, post_id: int, *, db) -> None:
    post = db.get(SocialPost, post_id)
    if not post:
        return
    if post.status == PostStatus.PUBLISHED:
        return
    result = SocialPostPublisherService().publish_now(post=post, connection=post.platform_connection)
    PostService(db).apply_publish_result(
        post_id=post_id,
        status_value=result.status,
        external_post_id=result.external_post_id,
        error_message=result.error_message,
    )
    ObservabilityService(db).record_action_usage(
        account_id=post.account_id,
        actor_user_id=post.created_by_user_id,
        platform_connection_id=post.platform_connection_id,
        platform_type=post.platform_type,
        action_type=ActionUsageType.POST_PUBLISH,
        reference_type="social_post",
        reference_id=str(post.id),
        quantity=1,
        tokens_consumed=max(len(post.content.split()), 1),
        estimated_cost=Decimal("0"),
        metadata_json={"publish_status": result.status.value},
    )
    if result.status == PostStatus.FAILED:
        SyncJobService(db).create_job(
            job_type=SyncJobType.RETRY_FAILED_SEND,
            account_id=post.account_id,
            platform_connection_id=post.platform_connection_id,
            dedupe_key=f"retry-post:{post.id}",
            payload_json={"post_id": post.id},
        )
