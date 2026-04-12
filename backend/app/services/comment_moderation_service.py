from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.enums import CommentReplyStatus, CommentStatus, MembershipStatus, PlatformType, SenderType
from app.models.facebook_comment import FacebookComment
from app.models.facebook_comment_reply import FacebookCommentReply
from app.models.membership import Membership
from app.models.user import User
from app.schemas.comments import (
    CommentAssigneeResponse,
    FacebookCommentDetailResponse,
    FacebookCommentListResponse,
    FacebookCommentReplyCreateRequest,
    FacebookCommentReplyResponse,
    FacebookCommentStatusUpdateRequest,
    FacebookCommentSummaryResponse,
)


class CommentModerationService:
    def __init__(self, db: Session):
        self.db = db

    def list_comments(
        self,
        *,
        account: Account,
        status_filter: CommentStatus | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> FacebookCommentListResponse:
        statement = self._comment_query(account.id)
        count_statement = select(func.count(FacebookComment.id)).where(FacebookComment.account_id == account.id)

        if status_filter:
            statement = statement.where(FacebookComment.status == status_filter)
            count_statement = count_statement.where(FacebookComment.status == status_filter)
        if search:
            term = f"%{search.strip()}%"
            search_filter = or_(
                FacebookComment.commenter_name.ilike(term),
                FacebookComment.commenter_external_id.ilike(term),
                FacebookComment.comment_text.ilike(term),
                FacebookComment.post_title.ilike(term),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return FacebookCommentListResponse(
            items=[self._build_comment_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_comment_detail(self, *, account: Account, comment_id: int) -> FacebookCommentDetailResponse:
        comment = self._get_comment(account.id, comment_id)
        detail = self._build_comment_summary(comment)
        replies = [
            FacebookCommentReplyResponse.model_validate(reply)
            for reply in sorted(comment.replies, key=lambda item: (item.created_at, item.id))
        ]
        return FacebookCommentDetailResponse(**detail.model_dump(), replies=replies)

    def update_comment_status(
        self,
        *,
        account: Account,
        comment_id: int,
        payload: FacebookCommentStatusUpdateRequest,
    ) -> FacebookCommentSummaryResponse:
        comment = self._get_comment(account.id, comment_id)
        self._apply_assignee(comment, account.id, payload.assignee_user_id)
        comment.status = payload.status
        comment.flagged_reason = payload.flagged_reason
        comment.moderation_notes = payload.moderation_notes
        if payload.metadata_json is not None:
            comment.metadata_json = payload.metadata_json
        self.db.commit()
        self.db.refresh(comment)
        return self._build_comment_summary(comment)

    def create_reply(
        self,
        *,
        account: Account,
        actor: User,
        comment_id: int,
        payload: FacebookCommentReplyCreateRequest,
    ) -> FacebookCommentReplyResponse:
        comment = self._get_comment(account.id, comment_id)
        if payload.sender_type not in {SenderType.HUMAN_ADMIN, SenderType.LLM_BOT}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comment replies must be created by a human admin or llm bot.",
            )

        reply_status = CommentReplyStatus.QUEUED if payload.send_now else CommentReplyStatus.DRAFT
        reply = FacebookCommentReply(
            account_id=account.id,
            comment_id=comment.id,
            created_by_user_id=actor.id,
            sender_type=payload.sender_type,
            reply_status=reply_status,
            content=payload.content.strip(),
            metadata_json=payload.metadata_json,
        )
        self.db.add(reply)

        if payload.sender_type == SenderType.LLM_BOT and not payload.send_now:
            comment.ai_draft_reply = payload.content.strip()
            if comment.status == CommentStatus.PENDING:
                comment.status = CommentStatus.NEED_REVIEW

        self.db.commit()
        self.db.refresh(reply)

        if payload.send_now:
            from app.workers.comment_tasks import deliver_comment_reply

            try:
                deliver_comment_reply.delay(reply.id)
            except Exception:
                pass

        return FacebookCommentReplyResponse.model_validate(reply)

    def update_reply_delivery(
        self,
        *,
        reply_id: int,
        reply_status: CommentReplyStatus,
        external_reply_id: str | None = None,
        error_message: str | None = None,
    ) -> FacebookCommentReply:
        reply = self.db.get(FacebookCommentReply, reply_id)
        if not reply:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment reply not found.")

        reply.reply_status = reply_status
        if external_reply_id is not None:
            reply.external_reply_id = external_reply_id
        reply.error_message = error_message
        reply.sent_at = self._utcnow() if reply_status == CommentReplyStatus.SENT else None

        comment = reply.comment
        if comment and reply_status == CommentReplyStatus.SENT:
            comment.status = CommentStatus.REPLIED
            comment.last_replied_at = reply.sent_at
            if reply.sender_type == SenderType.LLM_BOT:
                comment.ai_draft_reply = reply.content

        self.db.commit()
        self.db.refresh(reply)
        return reply

    def _comment_query(self, account_id: int):
        return (
            select(FacebookComment)
            .where(FacebookComment.account_id == account_id, FacebookComment.platform_type == PlatformType.FACEBOOK_PAGE)
            .options(
                selectinload(FacebookComment.assigned_to_user),
                selectinload(FacebookComment.replies),
            )
            .order_by(FacebookComment.commented_at.desc().nullslast(), FacebookComment.updated_at.desc())
        )

    def _get_comment(self, account_id: int, comment_id: int) -> FacebookComment:
        comment = self.db.scalar(self._comment_query(account_id).where(FacebookComment.id == comment_id))
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facebook comment not found.")
        return comment

    def _apply_assignee(self, comment: FacebookComment, account_id: int, assignee_user_id: int | None) -> None:
        if assignee_user_id is None:
            comment.assigned_to_user_id = None
            return
        membership = self.db.scalar(
            select(Membership).where(
                Membership.account_id == account_id,
                Membership.user_id == assignee_user_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee is not an active member of the account.")
        comment.assigned_to_user_id = assignee_user_id

    @staticmethod
    def _build_comment_summary(comment: FacebookComment) -> FacebookCommentSummaryResponse:
        assigned_to = None
        if comment.assigned_to_user:
            assigned_to = CommentAssigneeResponse(
                user_id=comment.assigned_to_user.id,
                full_name=comment.assigned_to_user.full_name,
                email=comment.assigned_to_user.email,
            )

        return FacebookCommentSummaryResponse(
            id=comment.id,
            account_id=comment.account_id,
            platform_connection_id=comment.platform_connection_id,
            platform_type=comment.platform_type,
            status=comment.status,
            post_external_id=comment.post_external_id,
            post_title=comment.post_title,
            post_url=comment.post_url,
            external_comment_id=comment.external_comment_id,
            parent_external_comment_id=comment.parent_external_comment_id,
            commenter_external_id=comment.commenter_external_id,
            commenter_name=comment.commenter_name,
            commenter_avatar_url=comment.commenter_avatar_url,
            comment_text=comment.comment_text,
            ai_draft_reply=comment.ai_draft_reply,
            flagged_reason=comment.flagged_reason,
            moderation_notes=comment.moderation_notes,
            commented_at=comment.commented_at,
            last_replied_at=comment.last_replied_at,
            metadata_json=comment.metadata_json,
            assigned_to=assigned_to,
            reply_count=len(comment.replies),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
