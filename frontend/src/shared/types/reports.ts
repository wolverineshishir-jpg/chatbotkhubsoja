export type DashboardMetricCard = {
  label: string;
  value: number | string;
  secondary: string | null;
};

export type DashboardSummary = {
  cards: DashboardMetricCard[];
  latest_audit_events: number;
  open_conversations: number;
  pending_comments: number;
  scheduled_posts: number;
  current_token_balance: number;
  monthly_token_credit: number;
};

export type TokenUsageSummary = {
  total_tokens_consumed: number;
  total_estimated_cost: string;
  total_action_count: number;
  top_actions: Array<{
    action_type: string;
    quantity: number;
    tokens_consumed: number;
    estimated_cost: string;
  }>;
  daily_usage: Array<{
    date: string;
    tokens_consumed: number;
  }>;
};

export type BillingSummary = {
  current_token_balance: number;
  monthly_token_credit: number;
  active_plan_code: string | null;
  active_plan_name: string | null;
  subscription_status: string | null;
  billed_tokens: number;
  estimated_llm_cost: string;
  estimated_action_cost: string;
  total_estimated_cost: string;
  llm_usage_by_model: Array<{
    model_name: string;
    total_tokens: number;
    estimated_cost: string;
  }>;
};

export type ConversationStats = {
  total_conversations: number;
  open_conversations: number;
  resolved_conversations: number;
  assigned_conversations: number;
  paused_conversations: number;
  recent_daily_counts: Array<{ date: string; count: number }>;
};

export type CommentStats = {
  total_comments: number;
  pending_comments: number;
  replied_comments: number;
  flagged_comments: number;
  need_review_comments: number;
  recent_daily_counts: Array<{ date: string; count: number }>;
};

export type PostStats = {
  total_posts: number;
  draft_posts: number;
  scheduled_posts: number;
  published_posts: number;
  failed_posts: number;
  recent_daily_counts: Array<{ date: string; count: number }>;
};
