from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.conversation import Conversation
from app.models.enums import (
    ConversationStatus,
    MessageDeliveryStatus,
    MessageDirection,
    MembershipStatus,
    PlatformType,
    SenderType,
)
from app.models.membership import Membership
from app.models.message import Message
from app.models.user import User
from app.schemas.inbox import (
    ConversationAssignRequest,
    ConversationAssigneeResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationStatusUpdateRequest,
    ConversationSummaryResponse,
    MessageListResponse,
    MessageResponse,
    SendReplyRequest,
)


class InboxService:
    def __init__(self, db: Session):
        self.db = db

    def list_conversations(
        self,
        *,
        account: Account,
        status_filter: ConversationStatus | None,
        platform_filter: PlatformType | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> ConversationListResponse:
        statement = self._conversation_query(account.id)
        count_statement = select(func.count(Conversation.id)).where(Conversation.account_id == account.id)

        if status_filter:
            statement = statement.where(Conversation.status == status_filter)
            count_statement = count_statement.where(Conversation.status == status_filter)
        if platform_filter:
            statement = statement.where(Conversation.platform_type == platform_filter)
            count_statement = count_statement.where(Conversation.platform_type == platform_filter)
        if search:
            term = f"%{search.strip()}%"
            search_filter = or_(
                Conversation.customer_name.ilike(term),
                Conversation.customer_external_id.ilike(term),
                Conversation.external_thread_id.ilike(term),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return ConversationListResponse(
            items=[self._build_conversation_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_conversation_detail(self, *, account: Account, conversation_id: int) -> ConversationDetailResponse:
        conversation = self._get_conversation(account.id, conversation_id)
        messages = self._list_messages(conversation.id, page=1, page_size=100)
        detail = self._build_conversation_summary(conversation)
        return ConversationDetailResponse(
            **detail.model_dump(),
            messages_total=messages.total,
            messages=messages.items,
        )

    def list_messages(
        self,
        *,
        account: Account,
        conversation_id: int,
        page: int,
        page_size: int,
    ) -> MessageListResponse:
        self._get_conversation(account.id, conversation_id)
        return self._list_messages(conversation_id, page=page, page_size=page_size)

    def assign_conversation(
        self,
        *,
        account: Account,
        payload: ConversationAssignRequest,
        conversation_id: int,
    ) -> ConversationSummaryResponse:
        conversation = self._get_conversation(account.id, conversation_id)
        if payload.assignee_user_id is None:
            conversation.assigned_to_user_id = None
            if conversation.status == ConversationStatus.ASSIGNED:
                conversation.status = ConversationStatus.OPEN
        else:
            self._ensure_assignable_user(account.id, payload.assignee_user_id)
            conversation.assigned_to_user_id = payload.assignee_user_id
            if conversation.status == ConversationStatus.OPEN:
                conversation.status = ConversationStatus.ASSIGNED

        self.db.commit()
        self.db.refresh(conversation)
        return self._build_conversation_summary(conversation)

    def update_conversation_status(
        self,
        *,
        account: Account,
        conversation_id: int,
        payload: ConversationStatusUpdateRequest,
    ) -> ConversationSummaryResponse:
        conversation = self._get_conversation(account.id, conversation_id)
        conversation.status = payload.status
        conversation.paused_until = payload.paused_until if payload.status == ConversationStatus.PAUSED else None
        conversation.resolved_at = self._utcnow() if payload.status == ConversationStatus.RESOLVED else None
        self.db.commit()
        self.db.refresh(conversation)
        return self._build_conversation_summary(conversation)

    def send_reply(
        self,
        *,
        account: Account,
        actor: User,
        conversation_id: int,
        payload: SendReplyRequest,
    ) -> MessageResponse:
        conversation = self._get_conversation(account.id, conversation_id)
        if payload.sender_type not in {SenderType.HUMAN_ADMIN, SenderType.LLM_BOT}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Replies must be sent by a human admin or llm bot.",
            )

        sender_name = (actor.full_name or actor.email) if payload.sender_type == SenderType.HUMAN_ADMIN else "AI Assistant"
        message = Message(
            account_id=account.id,
            conversation_id=conversation.id,
            created_by_user_id=actor.id,
            sender_type=payload.sender_type,
            direction=MessageDirection.OUTBOUND,
            delivery_status=MessageDeliveryStatus.QUEUED,
            sender_name=sender_name,
            content=payload.content.strip(),
            metadata_json={},
        )
        self.db.add(message)

        conversation.latest_message_preview = self._preview_text(payload.content)
        conversation.latest_message_at = self._utcnow()
        if conversation.status in {ConversationStatus.RESOLVED, ConversationStatus.PAUSED}:
            conversation.status = ConversationStatus.ASSIGNED if conversation.assigned_to_user_id else ConversationStatus.OPEN
        self.db.commit()
        self.db.refresh(message)

        from app.workers.inbox_tasks import deliver_outbound_message

        try:
            deliver_outbound_message.delay(message.id)
        except Exception:
            # Keep the message queued so a worker can retry once the broker is healthy.
            pass
        return MessageResponse.model_validate(message)

    def update_delivery_status(
        self,
        *,
        message_id: int,
        delivery_status: MessageDeliveryStatus,
        external_message_id: str | None = None,
        error_message: str | None = None,
    ) -> Message:
        message = self.db.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
        message.delivery_status = delivery_status
        if external_message_id is not None:
            message.external_message_id = external_message_id
        message.error_message = error_message
        self.db.commit()
        self.db.refresh(message)
        return message

    def _conversation_query(self, account_id: int):
        return (
            select(Conversation)
            .where(Conversation.account_id == account_id)
            .options(selectinload(Conversation.assigned_to_user))
            .order_by(Conversation.latest_message_at.desc().nullslast(), Conversation.updated_at.desc())
        )

    def _get_conversation(self, account_id: int, conversation_id: int) -> Conversation:
        conversation = self.db.scalar(self._conversation_query(account_id).where(Conversation.id == conversation_id))
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        return conversation

    def _list_messages(self, conversation_id: int, *, page: int, page_size: int) -> MessageListResponse:
        total = self.db.scalar(select(func.count(Message.id)).where(Message.conversation_id == conversation_id)) or 0
        items = self.db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return MessageListResponse(
            items=[MessageResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _ensure_assignable_user(self, account_id: int, assignee_user_id: int) -> None:
        membership = self.db.scalar(
            select(Membership).where(
                Membership.account_id == account_id,
                Membership.user_id == assignee_user_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee is not an active member of the account.",
            )

    @staticmethod
    def _build_conversation_summary(conversation: Conversation) -> ConversationSummaryResponse:
        assigned_to = None
        if conversation.assigned_to_user:
            assigned_to = ConversationAssigneeResponse(
                user_id=conversation.assigned_to_user.id,
                full_name=conversation.assigned_to_user.full_name,
                email=conversation.assigned_to_user.email,
            )

        return ConversationSummaryResponse(
            id=conversation.id,
            account_id=conversation.account_id,
            platform_connection_id=conversation.platform_connection_id,
            platform_type=conversation.platform_type,
            status=conversation.status,
            external_thread_id=conversation.external_thread_id,
            customer_external_id=conversation.customer_external_id,
            customer_name=conversation.customer_name,
            customer_avatar_url=conversation.customer_avatar_url,
            customer_phone=conversation.customer_phone,
            customer_email=conversation.customer_email,
            subject=conversation.subject,
            latest_message_preview=conversation.latest_message_preview,
            latest_message_at=conversation.latest_message_at,
            paused_until=conversation.paused_until,
            resolved_at=conversation.resolved_at,
            last_inbound_at=conversation.last_inbound_at,
            assigned_to=assigned_to,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    @staticmethod
    def _preview_text(content: str) -> str:
        trimmed = " ".join(content.split())
        return trimmed[:197] + "..." if len(trimmed) > 200 else trimmed

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
