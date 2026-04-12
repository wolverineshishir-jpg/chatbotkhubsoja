from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.ai_agent import AIAgent
from app.models.ai_prompt import AIPrompt
from app.models.enums import PlatformType, PostGeneratedBy, PostStatus, SyncJobType
from app.models.platform_connection import PlatformConnection
from app.models.social_post import SocialPost
from app.models.user import User
from app.schemas.posts import (
    PostApprovalRequest,
    PostRejectRequest,
    PostScheduleRequest,
    SocialPostCreateRequest,
    SocialPostListResponse,
    SocialPostResponse,
    SocialPostUpdateRequest,
)


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def list_posts(
        self,
        *,
        account: Account,
        status_filter: PostStatus | None,
        page: int,
        page_size: int,
    ) -> SocialPostListResponse:
        statement = select(SocialPost).where(SocialPost.account_id == account.id)
        count_statement = select(func.count(SocialPost.id)).where(SocialPost.account_id == account.id)
        if status_filter:
            statement = statement.where(SocialPost.status == status_filter)
            count_statement = count_statement.where(SocialPost.status == status_filter)

        statement = statement.order_by(SocialPost.scheduled_for.asc().nullslast(), SocialPost.updated_at.desc())
        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return SocialPostListResponse(
            items=[SocialPostResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_post(self, *, account: Account, post_id: int) -> SocialPostResponse:
        return SocialPostResponse.model_validate(self._get_post(account.id, post_id))

    def create_post(self, *, account: Account, actor: User, payload: SocialPostCreateRequest) -> SocialPostResponse:
        connection = self._validate_connection(account.id, payload.platform_connection_id)
        self._validate_ai_links(account.id, payload.ai_agent_id, payload.ai_prompt_id)
        if payload.scheduled_for is not None:
            self._ensure_future(payload.scheduled_for)

        post = SocialPost(
            account_id=account.id,
            platform_connection_id=payload.platform_connection_id,
            ai_agent_id=payload.ai_agent_id,
            ai_prompt_id=payload.ai_prompt_id,
            created_by_user_id=actor.id,
            platform_type=connection.platform_type if connection else PlatformType.FACEBOOK_PAGE,
            status=PostStatus.DRAFT,
            generated_by=payload.generated_by,
            title=payload.title,
            content=payload.content.strip(),
            media_urls=payload.media_urls,
            is_llm_generated=payload.is_llm_generated,
            requires_approval=payload.requires_approval,
            scheduled_for=payload.scheduled_for,
            metadata_json=payload.metadata_json,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return SocialPostResponse.model_validate(post)

    def update_post(
        self,
        *,
        account: Account,
        post_id: int,
        payload: SocialPostUpdateRequest,
    ) -> SocialPostResponse:
        post = self._get_post(account.id, post_id)
        if post.status not in {PostStatus.DRAFT, PostStatus.REJECTED, PostStatus.FAILED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft, rejected, or failed posts can be edited.")

        update_data = payload.model_dump(exclude_unset=True)
        if "platform_connection_id" in update_data:
            connection = self._validate_connection(account.id, payload.platform_connection_id)
            post.platform_connection_id = payload.platform_connection_id
            post.platform_type = connection.platform_type if connection else PlatformType.FACEBOOK_PAGE
        if "ai_agent_id" in update_data or "ai_prompt_id" in update_data:
            self._validate_ai_links(account.id, payload.ai_agent_id if "ai_agent_id" in update_data else post.ai_agent_id, payload.ai_prompt_id if "ai_prompt_id" in update_data else post.ai_prompt_id)
            if "ai_agent_id" in update_data:
                post.ai_agent_id = payload.ai_agent_id
            if "ai_prompt_id" in update_data:
                post.ai_prompt_id = payload.ai_prompt_id
        for field in ("title", "content", "generated_by", "is_llm_generated", "requires_approval"):
            if field in update_data:
                setattr(post, field, update_data[field])
        if "media_urls" in update_data and payload.media_urls is not None:
            post.media_urls = payload.media_urls
        if "metadata_json" in update_data and payload.metadata_json is not None:
            post.metadata_json = payload.metadata_json
        if post.generated_by == PostGeneratedBy.LLM_BOT and not post.is_llm_generated:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="LLM-generated posts must set is_llm_generated to true.")
        self.db.commit()
        self.db.refresh(post)
        return SocialPostResponse.model_validate(post)

    def delete_post(self, *, account: Account, post_id: int) -> None:
        post = self._get_post(account.id, post_id)
        if post.status in {PostStatus.PUBLISHED, PostStatus.SCHEDULED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scheduled or published posts cannot be deleted.")
        self.db.delete(post)
        self.db.commit()

    def approve_post(self, *, account: Account, actor: User, post_id: int, payload: PostApprovalRequest) -> SocialPostResponse:
        post = self._get_post(account.id, post_id)
        if post.status not in {PostStatus.DRAFT, PostStatus.REJECTED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft or rejected posts can be approved.")
        post.status = PostStatus.APPROVED
        post.approved_by_user_id = actor.id
        post.approved_at = self._utcnow()
        post.rejected_by_user_id = None
        post.rejected_at = None
        post.rejection_reason = None
        if payload.note:
            metadata = dict(post.metadata_json)
            metadata["approval_note"] = payload.note
            post.metadata_json = metadata
        self.db.commit()
        self.db.refresh(post)
        return SocialPostResponse.model_validate(post)

    def reject_post(self, *, account: Account, actor: User, post_id: int, payload: PostRejectRequest) -> SocialPostResponse:
        post = self._get_post(account.id, post_id)
        if post.status not in {PostStatus.DRAFT, PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.FAILED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post cannot be rejected from its current state.")
        post.status = PostStatus.REJECTED
        post.rejected_by_user_id = actor.id
        post.rejected_at = self._utcnow()
        post.rejection_reason = payload.reason
        post.scheduled_for = None
        self.db.commit()
        self.db.refresh(post)
        return SocialPostResponse.model_validate(post)

    def schedule_post(self, *, account: Account, post_id: int, payload: PostScheduleRequest) -> SocialPostResponse:
        post = self._get_post(account.id, post_id)
        self._ensure_publish_ready(post)
        self._ensure_future(payload.scheduled_for)
        post.status = PostStatus.SCHEDULED
        post.scheduled_for = payload.scheduled_for
        self.db.commit()
        self.db.refresh(post)
        from app.services.sync_job_service import SyncJobService

        SyncJobService(self.db).create_job(
            job_type=SyncJobType.SCHEDULED_POST_PUBLISH,
            account_id=post.account_id,
            platform_connection_id=post.platform_connection_id,
            scheduled_for=post.scheduled_for,
            dedupe_key=f"scheduled-post:{post.id}",
            payload_json={"post_id": post.id},
        )
        return SocialPostResponse.model_validate(post)

    def publish_now(self, *, account: Account, post_id: int) -> SocialPostResponse:
        post = self._get_post(account.id, post_id)
        self._ensure_publish_ready(post)
        if post.scheduled_for is not None and post.status == PostStatus.SCHEDULED:
            post.scheduled_for = None
        post.status = PostStatus.SCHEDULED
        self.db.commit()
        self.db.refresh(post)

        from app.workers.post_tasks import publish_social_post

        try:
            publish_social_post.delay(post.id)
        except Exception:
            pass
        return SocialPostResponse.model_validate(post)

    def apply_publish_result(
        self,
        *,
        post_id: int,
        status_value: PostStatus,
        external_post_id: str | None = None,
        error_message: str | None = None,
    ) -> SocialPost:
        post = self.db.get(SocialPost, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        post.status = status_value
        post.external_post_id = external_post_id
        post.last_error = error_message
        if status_value == PostStatus.PUBLISHED:
            post.published_at = self._utcnow()
            post.scheduled_for = None
        self.db.commit()
        self.db.refresh(post)
        return post

    def _get_post(self, account_id: int, post_id: int) -> SocialPost:
        post = self.db.scalar(select(SocialPost).where(SocialPost.account_id == account_id, SocialPost.id == post_id))
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        return post

    def _validate_connection(self, account_id: int, connection_id: int | None) -> PlatformConnection | None:
        if connection_id is None:
            return None
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.account_id == account_id,
                PlatformConnection.id == connection_id,
            )
        )
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")
        if connection.platform_type != PlatformType.FACEBOOK_PAGE:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only Facebook Page publishing is supported for posts.")
        return connection

    def _validate_ai_links(self, account_id: int, ai_agent_id: int | None, ai_prompt_id: int | None) -> None:
        if ai_agent_id is not None:
            agent = self.db.scalar(select(AIAgent).where(AIAgent.account_id == account_id, AIAgent.id == ai_agent_id))
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI agent not found.")
        if ai_prompt_id is not None:
            prompt = self.db.scalar(select(AIPrompt).where(AIPrompt.account_id == account_id, AIPrompt.id == ai_prompt_id))
            if not prompt:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI prompt not found.")

    def _ensure_publish_ready(self, post: SocialPost) -> None:
        if post.requires_approval and post.status != PostStatus.APPROVED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post requires approval before scheduling or publishing.")
        if not post.requires_approval and post.status not in {PostStatus.DRAFT, PostStatus.APPROVED, PostStatus.FAILED, PostStatus.REJECTED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post cannot be published from its current state.")
        if post.requires_approval and post.status == PostStatus.APPROVED:
            return

    @staticmethod
    def _ensure_future(value: datetime) -> None:
        compare = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if compare <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Scheduled publish time must be in the future.")

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
