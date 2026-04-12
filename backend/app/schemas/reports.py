from decimal import Decimal

from pydantic import BaseModel


class DashboardMetricCard(BaseModel):
    label: str
    value: int | Decimal | str
    secondary: str | None = None


class DashboardSummaryResponse(BaseModel):
    cards: list[DashboardMetricCard]
    latest_audit_events: int
    open_conversations: int
    pending_comments: int
    scheduled_posts: int
    current_token_balance: int
    monthly_token_credit: int


class TokenUsageSummaryResponse(BaseModel):
    total_tokens_consumed: int
    total_estimated_cost: Decimal
    total_action_count: int
    top_actions: list[dict]
    daily_usage: list[dict]


class BillingSummaryResponse(BaseModel):
    current_token_balance: int
    monthly_token_credit: int
    active_plan_code: str | None = None
    active_plan_name: str | None = None
    subscription_status: str | None = None
    billed_tokens: int
    estimated_llm_cost: Decimal
    estimated_action_cost: Decimal
    total_estimated_cost: Decimal
    llm_usage_by_model: list[dict]


class ConversationStatsResponse(BaseModel):
    total_conversations: int
    open_conversations: int
    resolved_conversations: int
    assigned_conversations: int
    paused_conversations: int
    recent_daily_counts: list[dict]


class CommentStatsResponse(BaseModel):
    total_comments: int
    pending_comments: int
    replied_comments: int
    flagged_comments: int
    need_review_comments: int
    recent_daily_counts: list[dict]


class PostStatsResponse(BaseModel):
    total_posts: int
    draft_posts: int
    scheduled_posts: int
    published_posts: int
    failed_posts: int
    recent_daily_counts: list[dict]
