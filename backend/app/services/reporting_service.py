from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_subscription import AccountSubscription
from app.models.action_usage_log import ActionUsageLog
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.enums import CommentStatus, ConversationStatus, PostStatus
from app.models.facebook_comment import FacebookComment
from app.models.llm_token_usage import LLMTokenUsage
from app.models.social_post import SocialPost
from app.services.token_wallet_service import TokenWalletService
from app.schemas.reports import (
    BillingSummaryResponse,
    CommentStatsResponse,
    ConversationStatsResponse,
    DashboardMetricCard,
    DashboardSummaryResponse,
    PostStatsResponse,
    TokenUsageSummaryResponse,
)


class ReportingService:
    def __init__(self, db: Session):
        self.db = db

    def dashboard_summary(self, *, account: Account) -> DashboardSummaryResponse:
        wallet_balance = TokenWalletService(self.db).get_wallet_balance(account=account)
        open_conversations = self._count(Conversation, account.id, Conversation.status == ConversationStatus.OPEN)
        pending_comments = self._count(FacebookComment, account.id, FacebookComment.status == CommentStatus.PENDING)
        scheduled_posts = self._count(SocialPost, account.id, SocialPost.status == PostStatus.SCHEDULED)
        latest_audit_events = self.db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.account_id == account.id,
                AuditLog.occurred_at >= self._utcnow() - timedelta(days=7),
            )
        ) or 0
        llm_tokens = self.db.scalar(
            select(func.coalesce(func.sum(LLMTokenUsage.total_tokens), 0)).where(LLMTokenUsage.account_id == account.id)
        ) or 0

        return DashboardSummaryResponse(
            cards=[
                DashboardMetricCard(label="Token balance", value=account.token_balance, secondary="Current available credits"),
                DashboardMetricCard(label="Expiring soon", value=wallet_balance.breakdown.expiring_next_tokens, secondary="Expires in 7 days"),
                DashboardMetricCard(label="Monthly credit", value=account.monthly_token_credit, secondary="Recurring token credit"),
                DashboardMetricCard(label="LLM tokens", value=int(llm_tokens), secondary="Tracked total usage"),
                DashboardMetricCard(label="Open conversations", value=open_conversations, secondary="Needs team attention"),
            ],
            latest_audit_events=latest_audit_events,
            open_conversations=open_conversations,
            pending_comments=pending_comments,
            scheduled_posts=scheduled_posts,
            current_token_balance=wallet_balance.breakdown.total_available_tokens,
            monthly_token_credit=account.monthly_token_credit,
        )

    def token_usage_summary(self, *, account: Account) -> TokenUsageSummaryResponse:
        total_tokens_consumed = self.db.scalar(
            select(func.coalesce(func.sum(ActionUsageLog.tokens_consumed), 0)).where(ActionUsageLog.account_id == account.id)
        ) or 0
        total_estimated_cost = self._decimal_sum(
            select(func.coalesce(func.sum(ActionUsageLog.estimated_cost), 0)).where(ActionUsageLog.account_id == account.id)
        )
        total_action_count = self.db.scalar(
            select(func.coalesce(func.sum(ActionUsageLog.quantity), 0)).where(ActionUsageLog.account_id == account.id)
        ) or 0

        top_actions_raw = self.db.execute(
            select(
                ActionUsageLog.action_type,
                func.coalesce(func.sum(ActionUsageLog.quantity), 0).label("quantity"),
                func.coalesce(func.sum(ActionUsageLog.tokens_consumed), 0).label("tokens"),
                func.coalesce(func.sum(ActionUsageLog.estimated_cost), 0).label("cost"),
            )
            .where(ActionUsageLog.account_id == account.id)
            .group_by(ActionUsageLog.action_type)
            .order_by(func.coalesce(func.sum(ActionUsageLog.tokens_consumed), 0).desc())
        ).all()

        daily_usage = []
        for day in self._last_n_days(7):
            day_start = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
            day_end = day_start + timedelta(days=1)
            tokens = self.db.scalar(
                select(func.coalesce(func.sum(ActionUsageLog.tokens_consumed), 0)).where(
                    ActionUsageLog.account_id == account.id,
                    ActionUsageLog.occurred_at >= day_start,
                    ActionUsageLog.occurred_at < day_end,
                )
            ) or 0
            daily_usage.append({"date": day.isoformat(), "tokens_consumed": int(tokens)})

        return TokenUsageSummaryResponse(
            total_tokens_consumed=int(total_tokens_consumed),
            total_estimated_cost=total_estimated_cost,
            total_action_count=int(total_action_count),
            top_actions=[
                {
                    "action_type": row.action_type.value,
                    "quantity": int(row.quantity or 0),
                    "tokens_consumed": int(row.tokens or 0),
                    "estimated_cost": str(Decimal(row.cost or 0)),
                }
                for row in top_actions_raw
            ],
            daily_usage=daily_usage,
        )

    def billing_summary(self, *, account: Account) -> BillingSummaryResponse:
        wallet_balance = TokenWalletService(self.db).get_wallet_balance(account=account)
        subscription = self.db.scalar(
            select(AccountSubscription)
            .where(AccountSubscription.account_id == account.id)
            .order_by(AccountSubscription.created_at.desc(), AccountSubscription.id.desc())
        )
        billed_tokens = self.db.scalar(
            select(func.coalesce(func.sum(LLMTokenUsage.total_tokens), 0)).where(LLMTokenUsage.account_id == account.id)
        ) or 0
        estimated_llm_cost = self._decimal_sum(
            select(func.coalesce(func.sum(LLMTokenUsage.estimated_cost), 0)).where(LLMTokenUsage.account_id == account.id)
        )
        estimated_action_cost = self._decimal_sum(
            select(func.coalesce(func.sum(ActionUsageLog.estimated_cost), 0)).where(ActionUsageLog.account_id == account.id)
        )
        by_model = self.db.execute(
            select(
                LLMTokenUsage.model_name,
                func.coalesce(func.sum(LLMTokenUsage.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(LLMTokenUsage.estimated_cost), 0).label("cost"),
            )
            .where(LLMTokenUsage.account_id == account.id)
            .group_by(LLMTokenUsage.model_name)
            .order_by(func.coalesce(func.sum(LLMTokenUsage.total_tokens), 0).desc())
        ).all()

        return BillingSummaryResponse(
            current_token_balance=wallet_balance.breakdown.total_available_tokens,
            monthly_token_credit=account.monthly_token_credit,
            active_plan_code=subscription.billing_plan.code if subscription and subscription.billing_plan else None,
            active_plan_name=subscription.billing_plan.name if subscription and subscription.billing_plan else None,
            subscription_status=subscription.status.value if subscription else None,
            billed_tokens=int(billed_tokens),
            estimated_llm_cost=estimated_llm_cost,
            estimated_action_cost=estimated_action_cost,
            total_estimated_cost=estimated_llm_cost + estimated_action_cost,
            llm_usage_by_model=[
                {
                    "model_name": row.model_name,
                    "total_tokens": int(row.tokens or 0),
                    "estimated_cost": str(Decimal(row.cost or 0)),
                }
                for row in by_model
            ],
        )

    def conversation_stats(self, *, account: Account) -> ConversationStatsResponse:
        return ConversationStatsResponse(
            total_conversations=self._count(Conversation, account.id),
            open_conversations=self._count(Conversation, account.id, Conversation.status == ConversationStatus.OPEN),
            resolved_conversations=self._count(Conversation, account.id, Conversation.status == ConversationStatus.RESOLVED),
            assigned_conversations=self._count(Conversation, account.id, Conversation.status == ConversationStatus.ASSIGNED),
            paused_conversations=self._count(Conversation, account.id, Conversation.status == ConversationStatus.PAUSED),
            recent_daily_counts=self._daily_counts(Conversation, account.id, Conversation.created_at),
        )

    def comment_stats(self, *, account: Account) -> CommentStatsResponse:
        return CommentStatsResponse(
            total_comments=self._count(FacebookComment, account.id),
            pending_comments=self._count(FacebookComment, account.id, FacebookComment.status == CommentStatus.PENDING),
            replied_comments=self._count(FacebookComment, account.id, FacebookComment.status == CommentStatus.REPLIED),
            flagged_comments=self._count(FacebookComment, account.id, FacebookComment.status == CommentStatus.FLAGGED),
            need_review_comments=self._count(FacebookComment, account.id, FacebookComment.status == CommentStatus.NEED_REVIEW),
            recent_daily_counts=self._daily_counts(FacebookComment, account.id, FacebookComment.created_at),
        )

    def post_stats(self, *, account: Account) -> PostStatsResponse:
        return PostStatsResponse(
            total_posts=self._count(SocialPost, account.id),
            draft_posts=self._count(SocialPost, account.id, SocialPost.status == PostStatus.DRAFT),
            scheduled_posts=self._count(SocialPost, account.id, SocialPost.status == PostStatus.SCHEDULED),
            published_posts=self._count(SocialPost, account.id, SocialPost.status == PostStatus.PUBLISHED),
            failed_posts=self._count(SocialPost, account.id, SocialPost.status == PostStatus.FAILED),
            recent_daily_counts=self._daily_counts(SocialPost, account.id, SocialPost.created_at),
        )

    def _count(self, model, account_id: int, *conditions) -> int:
        return self.db.scalar(
            select(func.count(model.id)).where(model.account_id == account_id, *conditions)
        ) or 0

    def _daily_counts(self, model, account_id: int, timestamp_field) -> list[dict]:
        items: list[dict] = []
        for day in self._last_n_days(7):
            day_start = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
            day_end = day_start + timedelta(days=1)
            count = self.db.scalar(
                select(func.count(model.id)).where(
                    model.account_id == account_id,
                    timestamp_field >= day_start,
                    timestamp_field < day_end,
                )
            ) or 0
            items.append({"date": day.isoformat(), "count": int(count)})
        return items

    def _decimal_sum(self, statement) -> Decimal:
        value = self.db.scalar(statement)
        return Decimal(str(value or 0))

    @staticmethod
    def _last_n_days(days: int) -> list[date]:
        today = datetime.now(UTC).date()
        return [today - timedelta(days=index) for index in range(days - 1, -1, -1)]

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
