from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.account import Account
from app.models.ai_agent import AIAgent
from app.models.conversation import Conversation
from app.models.enums import (
    ActionUsageType,
    CommentReplyStatus,
    CommentStatus,
    MessageDeliveryStatus,
    MessageDirection,
    PlatformType,
    PostGeneratedBy,
    PostStatus,
    PromptType,
    SenderType,
)
from app.models.facebook_comment import FacebookComment
from app.models.facebook_comment_reply import FacebookCommentReply
from app.models.message import Message
from app.models.platform_connection import PlatformConnection
from app.models.social_post import SocialPost
from app.models.user import User
from app.services.ai.knowledge_context_service import KnowledgeContextService
from app.services.ai.prompt_resolution_service import PromptResolutionService
from app.services.ai.provider_registry import LLMProviderRegistry
from app.services.ai.reply_routing_service import ReplyRoutingService
from app.services.ai_configuration_service import AIConfigurationService
from app.services.billing_service import BillingService
from app.services.observability_service import ObservabilityService


@dataclass(slots=True)
class GenerationOutcome:
    content: str
    requires_approval: bool
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_id: int | None
    prompt_scope: str
    ai_agent_id: int | None
    platform_connection_id: int | None
    draft_object_id: int | None = None
    draft_reference_type: str | None = None


class AIOrchestrationService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.observability = ObservabilityService(db)
        self.ai_config = AIConfigurationService(db)
        self.prompt_resolver = PromptResolutionService(self.ai_config)
        self.knowledge_context = KnowledgeContextService(db)
        self.providers = LLMProviderRegistry()
        self.reply_router = ReplyRoutingService()

    def generate_inbox_reply(
        self,
        *,
        account: Account,
        conversation_id: int,
        actor: User | None,
        ai_agent_id: int | None = None,
        platform_connection_id: int | None = None,
        instructions: str | None = None,
        send_now: bool = False,
        persist_draft: bool = True,
    ) -> GenerationOutcome:
        conversation = self._get_conversation(account.id, conversation_id)
        agent = self._resolve_agent(
            account_id=account.id,
            ai_agent_id=ai_agent_id,
            platform_connection_id=platform_connection_id or conversation.platform_connection_id,
        )
        prompt, scope = self.prompt_resolver.resolve_prompt(
            account=account,
            prompt_type=PromptType.INBOX_REPLY,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=platform_connection_id or conversation.platform_connection_id,
        )
        prompt_text = prompt.content if prompt else self._default_prompt(PromptType.INBOX_REPLY)
        requires_approval = self._requires_approval(agent=agent, context_key="inbox")
        latest_inbound = self._latest_inbound_message(conversation.id)
        latest_text = latest_inbound.content if latest_inbound else ""
        knowledge_text, knowledge_meta = self.knowledge_context.build_context(account_id=account.id, ai_agent_id=agent.id if agent else None)
        system_prompt = self._compose_system_prompt(prompt_text=prompt_text, knowledge_text=knowledge_text)
        user_prompt = self._compose_user_prompt(
            subject="Generate a concise inbox reply.",
            context={
                "customer_name": conversation.customer_name,
                "customer_external_id": conversation.customer_external_id,
                "incoming_message": latest_text,
                "extra_instructions": instructions or "",
            },
        )
        routed_reply = self.reply_router.generate_reply(
            provider=self.providers.resolve(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            source_text=latest_text,
            instructions=instructions or "",
            max_output_tokens=240,
            max_reply_chars=480,
        )
        generation = routed_reply.generation
        requires_approval = requires_approval or routed_reply.requires_human_review
        draft_message_id = None
        if persist_draft:
            draft_message_id = self._persist_inbox_generation(
                account=account,
                actor=actor,
                conversation=conversation,
                content=generation.content,
                requires_approval=requires_approval,
                send_now=send_now,
            )
        self._record_and_debit_usage(
            account=account,
            actor=actor,
            platform_connection_id=conversation.platform_connection_id,
            platform_type=conversation.platform_type,
            reference_type="conversation",
            reference_id=str(conversation.id),
            feature_name="inbox_reply_generation",
            prompt_scope=scope,
            generation=generation,
            metadata_json={
                "knowledge": knowledge_meta,
                "draft_message_id": draft_message_id,
                "routing": routed_reply.metadata,
            },
        )
        return GenerationOutcome(
            content=generation.content,
            requires_approval=requires_approval,
            provider=generation.provider,
            model_name=generation.model_name,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
            total_tokens=generation.total_tokens,
            prompt_id=prompt.id if prompt else None,
            prompt_scope=scope,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=conversation.platform_connection_id,
            draft_object_id=draft_message_id,
            draft_reference_type="message" if draft_message_id else None,
        )

    def generate_comment_reply(
        self,
        *,
        account: Account,
        comment_id: int,
        actor: User | None,
        ai_agent_id: int | None = None,
        instructions: str | None = None,
        send_now: bool = False,
        persist_draft: bool = True,
    ) -> GenerationOutcome:
        comment = self._get_comment(account.id, comment_id)
        agent = self._resolve_agent(
            account_id=account.id,
            ai_agent_id=ai_agent_id,
            platform_connection_id=comment.platform_connection_id,
        )
        prompt, scope = self.prompt_resolver.resolve_prompt(
            account=account,
            prompt_type=PromptType.COMMENT_REPLY,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=comment.platform_connection_id,
        )
        prompt_text = prompt.content if prompt else self._default_prompt(PromptType.COMMENT_REPLY)
        requires_approval = self._requires_approval(agent=agent, context_key="comment")
        knowledge_text, knowledge_meta = self.knowledge_context.build_context(account_id=account.id, ai_agent_id=agent.id if agent else None)
        system_prompt = self._compose_system_prompt(prompt_text=prompt_text, knowledge_text=knowledge_text)
        user_prompt = self._compose_user_prompt(
            subject="Generate a public-facing comment reply.",
            context={
                "post_title": comment.post_title,
                "commenter_name": comment.commenter_name,
                "incoming_comment": comment.comment_text,
                "extra_instructions": instructions or "",
            },
        )
        routed_reply = self.reply_router.generate_reply(
            provider=self.providers.resolve(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            source_text=comment.comment_text,
            instructions=instructions or "",
            max_output_tokens=180,
            max_reply_chars=320,
        )
        generation = routed_reply.generation
        requires_approval = requires_approval or routed_reply.requires_human_review
        draft_reply_id = None
        if persist_draft:
            draft_reply_id = self._persist_comment_generation(
                account=account,
                actor=actor,
                comment=comment,
                content=generation.content,
                requires_approval=requires_approval,
                send_now=send_now,
            )
        self._record_and_debit_usage(
            account=account,
            actor=actor,
            platform_connection_id=comment.platform_connection_id,
            platform_type=comment.platform_type,
            reference_type="facebook_comment",
            reference_id=str(comment.id),
            feature_name="comment_reply_generation",
            prompt_scope=scope,
            generation=generation,
            metadata_json={
                "knowledge": knowledge_meta,
                "draft_reply_id": draft_reply_id,
                "routing": routed_reply.metadata,
            },
        )
        return GenerationOutcome(
            content=generation.content,
            requires_approval=requires_approval,
            provider=generation.provider,
            model_name=generation.model_name,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
            total_tokens=generation.total_tokens,
            prompt_id=prompt.id if prompt else None,
            prompt_scope=scope,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=comment.platform_connection_id,
            draft_object_id=draft_reply_id,
            draft_reference_type="facebook_comment_reply" if draft_reply_id else None,
        )

    def generate_post(
        self,
        *,
        account: Account,
        actor: User | None,
        platform_connection_id: int | None,
        ai_agent_id: int | None = None,
        post_id: int | None = None,
        title_hint: str | None = None,
        instructions: str | None = None,
        persist_draft: bool = True,
    ) -> GenerationOutcome:
        connection = self._get_connection(account.id, platform_connection_id) if platform_connection_id else None
        if connection and connection.platform_type != PlatformType.FACEBOOK_PAGE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Post generation currently supports Facebook Page publishing only.",
            )
        agent = self._resolve_agent(
            account_id=account.id,
            ai_agent_id=ai_agent_id,
            platform_connection_id=platform_connection_id,
        )
        prompt, scope = self.prompt_resolver.resolve_prompt(
            account=account,
            prompt_type=PromptType.POST_GENERATION,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=platform_connection_id,
        )
        prompt_text = prompt.content if prompt else self._default_prompt(PromptType.POST_GENERATION)
        requires_approval = self._requires_approval(agent=agent, context_key="post")
        knowledge_text, knowledge_meta = self.knowledge_context.build_context(account_id=account.id, ai_agent_id=agent.id if agent else None)
        system_prompt = self._compose_system_prompt(prompt_text=prompt_text, knowledge_text=knowledge_text)
        user_prompt = self._compose_user_prompt(
            subject="Generate a social post draft.",
            context={
                "title_hint": title_hint or "",
                "extra_instructions": instructions or "",
            },
        )
        generation = self.providers.resolve().generate(system_prompt=system_prompt, user_prompt=user_prompt, max_output_tokens=420)
        draft_post_id = None
        if persist_draft:
            draft_post_id = self._persist_post_generation(
                account=account,
                actor=actor,
                post_id=post_id,
                platform_connection_id=platform_connection_id,
                ai_agent_id=agent.id if agent else None,
                ai_prompt_id=prompt.id if prompt else None,
                title_hint=title_hint,
                content=generation.content,
                requires_approval=requires_approval,
            )
        self._record_and_debit_usage(
            account=account,
            actor=actor,
            platform_connection_id=platform_connection_id,
            platform_type=connection.platform_type if connection else PlatformType.FACEBOOK_PAGE,
            reference_type="social_post",
            reference_id=str(draft_post_id) if draft_post_id else None,
            feature_name="post_generation",
            prompt_scope=scope,
            generation=generation,
            metadata_json={"knowledge": knowledge_meta, "draft_post_id": draft_post_id},
        )
        return GenerationOutcome(
            content=generation.content,
            requires_approval=requires_approval,
            provider=generation.provider,
            model_name=generation.model_name,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
            total_tokens=generation.total_tokens,
            prompt_id=prompt.id if prompt else None,
            prompt_scope=scope,
            ai_agent_id=agent.id if agent else None,
            platform_connection_id=platform_connection_id,
            draft_object_id=draft_post_id,
            draft_reference_type="social_post" if draft_post_id else None,
        )

    def auto_generate_for_message(self, *, account_id: int, conversation_id: int) -> GenerationOutcome:
        account = self._get_account(account_id)
        return self.generate_inbox_reply(
            account=account,
            conversation_id=conversation_id,
            actor=None,
            send_now=True,
            persist_draft=True,
        )

    def auto_generate_for_comment(self, *, account_id: int, comment_id: int) -> GenerationOutcome:
        account = self._get_account(account_id)
        return self.generate_comment_reply(
            account=account,
            comment_id=comment_id,
            actor=None,
            send_now=True,
            persist_draft=True,
        )

    def _persist_inbox_generation(
        self,
        *,
        account: Account,
        actor: User | None,
        conversation: Conversation,
        content: str,
        requires_approval: bool,
        send_now: bool,
    ) -> int:
        should_queue_send = send_now and not requires_approval
        message = Message(
            account_id=account.id,
            conversation_id=conversation.id,
            created_by_user_id=actor.id if actor else None,
            sender_type=SenderType.LLM_BOT,
            direction=MessageDirection.OUTBOUND,
            delivery_status=MessageDeliveryStatus.QUEUED if should_queue_send else MessageDeliveryStatus.PENDING,
            sender_name="AI Assistant",
            content=content.strip(),
            metadata_json={
                "ai_generated": True,
                "requires_approval": requires_approval,
                "auto_send_requested": send_now,
            },
        )
        self.db.add(message)
        if should_queue_send:
            conversation.latest_message_preview = self._preview_text(content)
            conversation.latest_message_at = self._utcnow()
        self.db.commit()
        self.db.refresh(message)
        if should_queue_send:
            from app.workers.inbox_tasks import deliver_outbound_message

            try:
                deliver_outbound_message.delay(message.id)
            except Exception:
                pass
        return message.id

    def _persist_comment_generation(
        self,
        *,
        account: Account,
        actor: User | None,
        comment: FacebookComment,
        content: str,
        requires_approval: bool,
        send_now: bool,
    ) -> int:
        should_queue_send = send_now and not requires_approval
        reply = FacebookCommentReply(
            account_id=account.id,
            comment_id=comment.id,
            created_by_user_id=actor.id if actor else None,
            sender_type=SenderType.LLM_BOT,
            reply_status=CommentReplyStatus.QUEUED if should_queue_send else CommentReplyStatus.DRAFT,
            content=content.strip(),
            metadata_json={
                "ai_generated": True,
                "requires_approval": requires_approval,
                "auto_send_requested": send_now,
            },
        )
        self.db.add(reply)
        comment.ai_draft_reply = content.strip()
        if not should_queue_send and comment.status == CommentStatus.PENDING:
            comment.status = CommentStatus.NEED_REVIEW
        self.db.commit()
        self.db.refresh(reply)
        if should_queue_send:
            from app.workers.comment_tasks import deliver_comment_reply

            try:
                deliver_comment_reply.delay(reply.id)
            except Exception:
                pass
        return reply.id

    def _persist_post_generation(
        self,
        *,
        account: Account,
        actor: User | None,
        post_id: int | None,
        platform_connection_id: int | None,
        ai_agent_id: int | None,
        ai_prompt_id: int | None,
        title_hint: str | None,
        content: str,
        requires_approval: bool,
    ) -> int:
        if post_id is not None:
            post = self.db.scalar(select(SocialPost).where(SocialPost.account_id == account.id, SocialPost.id == post_id))
            if not post:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
            post.title = post.title or title_hint
            post.content = content.strip()
            post.generated_by = PostGeneratedBy.LLM_BOT
            post.is_llm_generated = True
            post.requires_approval = requires_approval
            post.ai_agent_id = ai_agent_id
            post.ai_prompt_id = ai_prompt_id
            post.status = PostStatus.DRAFT
            post.last_error = None
            self.db.commit()
            self.db.refresh(post)
            return post.id

        post = SocialPost(
            account_id=account.id,
            platform_connection_id=platform_connection_id,
            ai_agent_id=ai_agent_id,
            ai_prompt_id=ai_prompt_id,
            created_by_user_id=actor.id if actor else None,
            platform_type=PlatformType.FACEBOOK_PAGE,
            status=PostStatus.DRAFT,
            generated_by=PostGeneratedBy.LLM_BOT,
            title=title_hint,
            content=content.strip(),
            media_urls=[],
            is_llm_generated=True,
            requires_approval=requires_approval,
            metadata_json={"ai_generated": True},
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post.id

    def _record_and_debit_usage(
        self,
        *,
        account: Account,
        actor: User | None,
        platform_connection_id: int | None,
        platform_type: PlatformType,
        reference_type: str,
        reference_id: str | None,
        feature_name: str,
        prompt_scope: str,
        generation,
        metadata_json: dict[str, Any],
    ) -> None:
        self.observability.record_llm_token_usage(
            account_id=account.id,
            actor_user_id=actor.id if actor else None,
            platform_connection_id=platform_connection_id,
            provider=generation.provider,
            model_name=generation.model_name,
            feature_name=feature_name,
            reference_type=reference_type,
            reference_id=reference_id,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
            total_tokens=generation.total_tokens,
            estimated_cost=Decimal("0"),
            metadata_json={**metadata_json, "prompt_scope": prompt_scope},
        )
        self.observability.record_action_usage(
            account_id=account.id,
            actor_user_id=actor.id if actor else None,
            platform_connection_id=platform_connection_id,
            platform_type=platform_type,
            action_type=ActionUsageType.AI_REPLY_GENERATION,
            reference_type=reference_type,
            reference_id=reference_id,
            quantity=1,
            tokens_consumed=generation.total_tokens,
            estimated_cost=Decimal("0"),
            metadata_json={**metadata_json, "prompt_scope": prompt_scope, "provider": generation.provider},
        )
        if self.settings.ai_token_debit_enabled:
            BillingService(self.db).debit_tokens(
                account=account,
                amount=generation.total_tokens,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=f"AI token debit for {feature_name}.",
                metadata_json={"feature_name": feature_name, "provider": generation.provider},
            )
            self.db.commit()

    def _resolve_agent(self, *, account_id: int, ai_agent_id: int | None, platform_connection_id: int | None) -> AIAgent | None:
        if ai_agent_id is not None:
            agent = self.db.scalar(select(AIAgent).where(AIAgent.account_id == account_id, AIAgent.id == ai_agent_id))
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI agent not found.")
            return agent
        if platform_connection_id is None:
            return None
        return self.db.scalar(
            select(AIAgent)
            .where(AIAgent.account_id == account_id, AIAgent.platform_connection_id == platform_connection_id)
            .order_by(AIAgent.updated_at.desc())
        )

    def _latest_inbound_message(self, conversation_id: int) -> Message | None:
        return self.db.scalar(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.direction == MessageDirection.INBOUND)
            .order_by(Message.created_at.desc(), Message.id.desc())
        )

    def _requires_approval(self, *, agent: AIAgent | None, context_key: str) -> bool:
        if not agent:
            return False
        settings_json = agent.settings_json or {}
        if f"{context_key}_requires_human_approval" in settings_json:
            return bool(settings_json[f"{context_key}_requires_human_approval"])
        return bool(settings_json.get("require_human_approval", False))

    def _get_account(self, account_id: int) -> Account:
        account = self.db.get(Account, account_id)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
        return account

    def _get_conversation(self, account_id: int, conversation_id: int) -> Conversation:
        conversation = self.db.scalar(
            select(Conversation).where(Conversation.account_id == account_id, Conversation.id == conversation_id)
        )
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        return conversation

    def _get_comment(self, account_id: int, comment_id: int) -> FacebookComment:
        comment = self.db.scalar(select(FacebookComment).where(FacebookComment.account_id == account_id, FacebookComment.id == comment_id))
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facebook comment not found.")
        return comment

    def _get_connection(self, account_id: int, connection_id: int) -> PlatformConnection:
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.account_id == account_id,
                PlatformConnection.id == connection_id,
            )
        )
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")
        return connection

    @staticmethod
    def _compose_system_prompt(*, prompt_text: str, knowledge_text: str) -> str:
        if not knowledge_text:
            return prompt_text
        return f"{prompt_text}\n\nUse this context when relevant:\n{knowledge_text}"

    @staticmethod
    def _compose_user_prompt(*, subject: str, context: dict[str, Any]) -> str:
        lines = [subject]
        for key, value in context.items():
            if value:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    @staticmethod
    def _default_prompt(prompt_type: PromptType) -> str:
        if prompt_type == PromptType.INBOX_REPLY:
            return "Write a short, helpful customer support response. Be empathetic and actionable."
        if prompt_type == PromptType.COMMENT_REPLY:
            return "Write a polite public reply that addresses the comment and reflects a helpful brand tone."
        return "Write an engaging social post for the brand with a clear call to action."

    @staticmethod
    def _preview_text(content: str) -> str:
        trimmed = " ".join(content.split())
        return trimmed[:197] + "..." if len(trimmed) > 200 else trimmed

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
