export type AutomationWorkflowStatus = "draft" | "active" | "paused" | "archived";
export type AutomationTriggerType = "inbox_message_received" | "facebook_comment_created" | "scheduled_daily";
export type AutomationActionType = "generate_inbox_reply" | "generate_comment_reply" | "generate_post_draft";

export type AutomationTriggerFilters = {
  include_keywords: string[];
  exclude_keywords: string[];
  customer_contains: string | null;
};

export type AutomationActionConfig = {
  instructions: string | null;
  send_now: boolean;
  title_hint: string | null;
};

export type AutomationWorkflow = {
  id: number;
  account_id: number;
  platform_connection_id: number | null;
  ai_agent_id: number | null;
  name: string;
  description: string | null;
  status: AutomationWorkflowStatus;
  trigger_type: AutomationTriggerType;
  action_type: AutomationActionType;
  delay_seconds: number;
  trigger_filters_json: AutomationTriggerFilters;
  action_config_json: AutomationActionConfig;
  schedule_timezone: string | null;
  schedule_local_time: string | null;
  next_run_at: string | null;
  last_triggered_at: string | null;
  last_result_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AutomationWorkflowListResponse = {
  items: AutomationWorkflow[];
  total: number;
};
