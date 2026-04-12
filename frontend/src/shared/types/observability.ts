export type ActionUsageLog = {
  id: number;
  account_id: number;
  platform_connection_id: number | null;
  actor_user_id: number | null;
  action_type: string;
  platform_type: string | null;
  reference_type: string | null;
  reference_id: string | null;
  quantity: number;
  tokens_consumed: number;
  estimated_cost: string;
  occurred_at: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ActionUsageLogListResponse = {
  items: ActionUsageLog[];
  total: number;
  page: number;
  page_size: number;
};

export type LLMTokenUsage = {
  id: number;
  account_id: number;
  platform_connection_id: number | null;
  actor_user_id: number | null;
  provider: string;
  model_name: string;
  feature_name: string;
  reference_type: string | null;
  reference_id: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: string;
  request_count: number;
  used_at: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type LLMTokenUsageListResponse = {
  items: LLMTokenUsage[];
  total: number;
  page: number;
  page_size: number;
};

export type AuditLog = {
  id: number;
  account_id: number;
  actor_user_id: number | null;
  action_type: string;
  resource_type: string;
  resource_id: string | null;
  description: string;
  ip_address: string | null;
  user_agent: string | null;
  occurred_at: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AuditLogListResponse = {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
};
