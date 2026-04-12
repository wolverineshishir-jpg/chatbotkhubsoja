from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.integrations.facebook.parsers import FacebookWebhookParser
from app.integrations.whatsapp.parsers import WhatsAppWebhookParser
from app.models.conversation import Conversation
from app.models.enums import (
    ActionUsageType,
    AutomationTriggerType,
    CommentStatus,
    ConversationStatus,
    MessageDeliveryStatus,
    MessageDirection,
    PlatformType,
    SenderType,
    SyncJobType,
    WebhookEventStatus,
)
from app.models.facebook_comment import FacebookComment
from app.models.message import Message
from app.models.social_post import SocialPost
from app.models.webhook_event import WebhookEvent
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.content_moderation_service import ContentModerationService
from app.services.observability_service import ObservabilityService
from app.services.sync_job_service import SyncJobService

logger = get_logger(__name__)


class WebhookProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.sync_jobs = SyncJobService(db)
        self.automation = AutomationWorkflowService(db)
        self.observability = ObservabilityService(db)
        self.moderation = ContentModerationService()
        self.facebook_parser = FacebookWebhookParser()
        self.whatsapp_parser = WhatsAppWebhookParser()

    def mark_processing(self, event: WebhookEvent, *, task_id: str | None = None) -> WebhookEvent:
        if event.status == WebhookEventStatus.PROCESSED:
            return event
        event.status = WebhookEventStatus.PROCESSING
        event.processing_started_at = self._utcnow()
        event.last_task_id = task_id
        event.attempts += 1
        event.error_message = None
        self.db.commit()
        self.db.refresh(event)
        return event

    def mark_processed(self, event: WebhookEvent, *, metadata: dict | None = None) -> WebhookEvent:
        event.status = WebhookEventStatus.PROCESSED
        event.processed_at = self._utcnow()
        if metadata:
            event.metadata_json = {**event.metadata_json, **metadata}
        self.db.commit()
        self.db.refresh(event)
        return event

    def mark_ignored(self, event: WebhookEvent, *, reason: str) -> WebhookEvent:
        event.status = WebhookEventStatus.IGNORED
        event.processed_at = self._utcnow()
        event.error_message = reason[:500]
        self.db.commit()
        self.db.refresh(event)
        return event

    def mark_failed(self, event: WebhookEvent, *, error_message: str) -> WebhookEvent:
        event.status = WebhookEventStatus.FAILED
        event.error_message = error_message[:500]
        self.db.commit()
        self.db.refresh(event)
        return event

    def process_event(self, event_id: int) -> dict:
        event = self.db.get(WebhookEvent, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook event not found.")
        if event.status == WebhookEventStatus.PROCESSED:
            logger.info("Webhook event already processed", extra={"event_id": event_id})
            return {"event_id": event.id, "status": "already_processed"}
        if event.account_id is None:
            self.mark_ignored(event, reason="Webhook event could not be matched to an active platform connection.")
            logger.warning("Webhook event ignored because connection could not be resolved", extra={"event_id": event.id})
            return {"event_id": event.id, "status": "ignored"}

        payload = event.payload_json
        logger.info(
            "Processing webhook event",
            extra={
                "event_id": event.id,
                "platform_type": event.platform_type.value,
                "event_type": event.event_type,
            },
        )
        if event.platform_type == PlatformType.FACEBOOK_PAGE:
            return self._process_facebook_event(event, payload)
        if event.platform_type == PlatformType.WHATSAPP:
            return self._process_whatsapp_event(event, payload)
        return {"event_id": event.id, "status": "unsupported_platform"}

    def create_scheduled_post_publish_job(self, post_id: int):
        post = self.db.get(SocialPost, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        return self.sync_jobs.create_job(
            job_type=SyncJobType.SCHEDULED_POST_PUBLISH,
            account_id=post.account_id,
            platform_connection_id=post.platform_connection_id,
            scheduled_for=post.scheduled_for or self._utcnow(),
            dedupe_key=f"scheduled-post:{post.id}",
            payload_json={"post_id": post.id},
        )

    def _process_facebook_event(self, event: WebhookEvent, payload: dict) -> dict:
        parsed = self.facebook_parser.parse(payload)
        handled = 0
        for message_event in parsed.messages:
            normalized = {
                "message": {
                    "mid": message_event.message_id,
                    "text": message_event.text,
                    "created_time": message_event.created_time,
                },
                "sender": {"id": message_event.sender_id},
                "recipient": {"id": message_event.recipient_id or message_event.page_id},
                "raw_payload": message_event.raw_payload,
            }
            if self._handle_inbound_message_event(event, normalized, platform_type=PlatformType.FACEBOOK_PAGE):
                handled += 1

        for comment_event in parsed.comments:
            normalized_comment = {
                "comment_id": comment_event.comment_id,
                "post_id": comment_event.post_id,
                "parent_id": comment_event.parent_id,
                "from": {
                    "id": comment_event.commenter_id,
                    "name": comment_event.commenter_name,
                },
                "message": comment_event.message,
                "created_time": comment_event.created_time,
                "post": {
                    "permalink_url": None,
                    "title": None,
                },
                "raw_payload": comment_event.raw_payload,
            }
            if self._handle_inbound_comment_event(event, normalized_comment):
                handled += 1

        if handled == 0:
            self.mark_ignored(event, reason="No supported Facebook event payload found.")
            logger.info("Facebook webhook event ignored because no supported items were parsed", extra={"event_id": event.id})
            return {"event_id": event.id, "status": "ignored"}

        self.mark_processed(event, metadata={"handled_count": handled})
        logger.info("Facebook webhook event processed", extra={"event_id": event.id, "handled_count": handled})
        return {"event_id": event.id, "status": "processed", "handled_count": handled}

    def _process_whatsapp_event(self, event: WebhookEvent, payload: dict) -> dict:
        handled = 0
        parsed = self.whatsapp_parser.parse(payload)
        for message_event in parsed.messages:
            normalized = {
                "message": {
                    "mid": message_event.message_id,
                    "text": message_event.text,
                    "created_time": message_event.created_time,
                },
                "sender": {"id": message_event.sender_id},
                "recipient": {"id": message_event.phone_number_id},
                "contacts": [{"profile": {"name": message_event.sender_name}, "wa_id": message_event.sender_id}],
                "raw_payload": message_event.raw_payload,
            }
            if self._handle_inbound_message_event(event, normalized, platform_type=PlatformType.WHATSAPP):
                handled += 1

        if handled == 0:
            self.mark_ignored(event, reason="No supported WhatsApp event payload found.")
            logger.info("WhatsApp webhook event ignored because no supported items were parsed", extra={"event_id": event.id})
            return {"event_id": event.id, "status": "ignored"}

        self.mark_processed(event, metadata={"handled_count": handled})
        logger.info("WhatsApp webhook event processed", extra={"event_id": event.id, "handled_count": handled})
        return {"event_id": event.id, "status": "processed", "handled_count": handled}

    def _handle_inbound_message_event(self, event: WebhookEvent, payload: dict, *, platform_type: PlatformType) -> bool:
        message_data = payload.get("message") or {}
        external_message_id = message_data.get("mid")
        if not external_message_id:
            return False

        existing_message = self.db.scalar(
            select(Message).where(
                Message.account_id == event.account_id,
                Message.external_message_id == external_message_id,
            )
        )
        if existing_message:
            logger.info(
                "Skipping duplicate inbound message",
                extra={"event_id": event.id, "external_message_id": external_message_id},
            )
            return True

        sender = payload.get("sender") or {}
        contacts = payload.get("contacts") or []
        customer_name = None
        if contacts:
            customer_name = contacts[0].get("profile", {}).get("name") or contacts[0].get("wa_id")

        customer_external_id = sender.get("id") or "unknown-customer"
        conversation = self.db.scalar(
            select(Conversation).where(
                Conversation.account_id == event.account_id,
                Conversation.platform_type == platform_type,
                Conversation.customer_external_id == customer_external_id,
            )
        )
        if conversation is None:
            conversation = Conversation(
                account_id=event.account_id or 0,
                platform_connection_id=event.platform_connection_id,
                platform_type=platform_type,
                status=ConversationStatus.OPEN,
                external_thread_id=(payload.get("recipient") or {}).get("id"),
                customer_external_id=customer_external_id,
                customer_name=customer_name,
                customer_phone=customer_external_id if platform_type == PlatformType.WHATSAPP else None,
                metadata_json={},
            )
            self.db.add(conversation)
            self.db.flush()

        text_content = message_data.get("text") or payload.get("text") or ""
        created_at = self._coerce_timestamp(message_data.get("created_time"))
        message = Message(
            account_id=event.account_id or conversation.account_id,
            conversation_id=conversation.id,
            sender_type=SenderType.CUSTOMER,
            direction=MessageDirection.INBOUND,
            delivery_status=MessageDeliveryStatus.DELIVERED,
            sender_name=customer_name,
            sender_external_id=customer_external_id,
            external_message_id=external_message_id,
            content=text_content.strip() or "[empty message]",
            metadata_json={"webhook_event_id": event.id},
        )
        self.db.add(message)

        conversation.customer_name = conversation.customer_name or customer_name
        if platform_type == PlatformType.WHATSAPP:
            conversation.customer_phone = conversation.customer_phone or customer_external_id
        conversation.latest_message_preview = self._preview_text(message.content)
        conversation.latest_message_at = created_at
        conversation.last_inbound_at = created_at
        if conversation.status in {ConversationStatus.RESOLVED, ConversationStatus.PAUSED}:
            conversation.status = ConversationStatus.OPEN
        moderation_match = self.moderation.evaluate(message.content)
        if moderation_match.is_flagged:
            conversation.status = ConversationStatus.ESCALATED
            conversation.metadata_json = {
                **(conversation.metadata_json or {}),
                "moderation": {
                    "flagged": True,
                    "reason": moderation_match.reason,
                    "matched_terms": moderation_match.matched_terms,
                    "source": "inbound_message",
                },
            }
            message.metadata_json = {
                **(message.metadata_json or {}),
                "moderation": {
                    "flagged": True,
                    "reason": moderation_match.reason,
                    "matched_terms": moderation_match.matched_terms,
                },
            }

        self.db.commit()
        self.db.refresh(conversation)

        automation_jobs: list[int] = []
        if not moderation_match.is_flagged:
            automation_jobs = self.automation.queue_matching_message_workflows(conversation=conversation, message=message)
            if not automation_jobs and not self.automation.has_active_workflows(
                account_id=conversation.account_id,
                trigger_type=AutomationTriggerType.INBOX_MESSAGE_RECEIVED,
                platform_connection_id=conversation.platform_connection_id,
            ):
                self.sync_jobs.create_job(
                    job_type=SyncJobType.AI_REPLY_GENERATION,
                    account_id=conversation.account_id,
                    platform_connection_id=conversation.platform_connection_id,
                    dedupe_key=f"ai-reply:conversation:{conversation.id}:message:{message.id}",
                    payload_json={
                        "conversation_id": conversation.id,
                        "message_id": message.id,
                        "platform_type": platform_type.value,
                    },
                )
        self.observability.record_action_usage(
            account_id=conversation.account_id,
            platform_connection_id=conversation.platform_connection_id,
            platform_type=platform_type,
            action_type=ActionUsageType.INBOUND_MESSAGE,
            reference_type="message",
            reference_id=str(message.id),
            quantity=1,
            tokens_consumed=max(len(message.content.split()), 1),
            estimated_cost=Decimal("0"),
            metadata_json={"webhook_event_id": event.id},
        )
        logger.info(
            "Inbound message stored and queued for reply generation",
            extra={
                "event_id": event.id,
                "conversation_id": conversation.id,
                "message_id": message.id,
                "moderation_flagged": moderation_match.is_flagged,
            },
        )
        return True

    def _handle_inbound_comment_event(self, event: WebhookEvent, payload: dict) -> bool:
        external_comment_id = payload.get("comment_id") or payload.get("post_id")
        if not external_comment_id:
            return False

        comment = self.db.scalar(
            select(FacebookComment).where(
                FacebookComment.account_id == event.account_id,
                FacebookComment.external_comment_id == external_comment_id,
            )
        )
        if comment is None:
            comment = FacebookComment(
                account_id=event.account_id or 0,
                platform_connection_id=event.platform_connection_id,
                platform_type=PlatformType.FACEBOOK_PAGE,
                status=CommentStatus.PENDING,
                post_external_id=payload.get("post_id") or "unknown-post",
                post_title=payload.get("post", {}).get("title"),
                post_url=payload.get("post", {}).get("permalink_url"),
                external_comment_id=external_comment_id,
                parent_external_comment_id=payload.get("parent_id"),
                commenter_external_id=payload.get("from", {}).get("id") or "unknown-commenter",
                commenter_name=payload.get("from", {}).get("name"),
                comment_text=payload.get("message") or payload.get("verb") or "[empty comment]",
                commented_at=self._coerce_timestamp(payload.get("created_time")),
                metadata_json={"webhook_event_id": event.id},
            )
            self.db.add(comment)
            self.db.flush()
        else:
            comment.comment_text = payload.get("message") or comment.comment_text
            comment.metadata_json = {**comment.metadata_json, "webhook_event_id": event.id}

        moderation_match = self.moderation.evaluate(comment.comment_text)
        if moderation_match.is_flagged:
            comment.status = CommentStatus.FLAGGED
            comment.flagged_reason = moderation_match.reason
            comment.moderation_notes = "Auto-flagged for abusive or profane language."
            comment.metadata_json = {
                **(comment.metadata_json or {}),
                "moderation": {
                    "flagged": True,
                    "reason": moderation_match.reason,
                    "matched_terms": moderation_match.matched_terms,
                    "source": "facebook_comment",
                },
            }

        self.db.commit()
        self.db.refresh(comment)

        automation_jobs: list[int] = []
        if not moderation_match.is_flagged:
            automation_jobs = self.automation.queue_matching_comment_workflows(comment=comment)
            if not automation_jobs and not self.automation.has_active_workflows(
                account_id=comment.account_id,
                trigger_type=AutomationTriggerType.FACEBOOK_COMMENT_CREATED,
                platform_connection_id=comment.platform_connection_id,
            ):
                self.sync_jobs.create_job(
                    job_type=SyncJobType.AI_REPLY_GENERATION,
                    account_id=comment.account_id,
                    platform_connection_id=comment.platform_connection_id,
                    dedupe_key=f"ai-reply:comment:{comment.id}",
                    payload_json={"comment_id": comment.id, "platform_type": PlatformType.FACEBOOK_PAGE.value},
                )
        self.observability.record_action_usage(
            account_id=comment.account_id,
            platform_connection_id=comment.platform_connection_id,
            platform_type=PlatformType.FACEBOOK_PAGE,
            action_type=ActionUsageType.INBOUND_MESSAGE,
            reference_type="facebook_comment",
            reference_id=str(comment.id),
            quantity=1,
            tokens_consumed=max(len(comment.comment_text.split()), 1),
            estimated_cost=Decimal("0"),
            metadata_json={"webhook_event_id": event.id, "ingested_as": "comment"},
        )
        logger.info(
            "Inbound comment stored and queued for reply generation",
            extra={
                "event_id": event.id,
                "comment_id": comment.id,
                "external_comment_id": external_comment_id,
                "moderation_flagged": moderation_match.is_flagged,
            },
        )
        return True

    @staticmethod
    def _coerce_timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.now(UTC)
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=UTC)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _preview_text(content: str) -> str:
        trimmed = " ".join(content.split())
        return trimmed[:197] + "..." if len(trimmed) > 200 else trimmed

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
