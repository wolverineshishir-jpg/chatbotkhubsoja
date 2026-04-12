export type PlatformType = "facebook_page" | "whatsapp";
export type ConnectionStatus = "pending" | "connected" | "action_required" | "disconnected" | "error";

export type WebhookConfig = {
  webhook_url: string | null;
  webhook_active: boolean;
  has_secret: boolean;
  has_verify_token: boolean;
};

export type IntegrationSummary = {
  provider: string | null;
  connected_via: string | null;
  sync_state: string | null;
  token_status: string | null;
  last_synced_at: string | null;
  webhook_subscription_state: string | null;
  page_picture_url: string | null;
  followers_count: number | null;
  required_permissions: string[];
  tasks: string[];
};

export type PlatformConnection = {
  id: number;
  account_id: number;
  platform_type: PlatformType;
  name: string;
  external_id: string | null;
  external_name: string | null;
  status: ConnectionStatus;
  token_hint: string | null;
  webhook: WebhookConfig;
  metadata_json: Record<string, unknown>;
  settings_json: Record<string, unknown>;
  last_error: string | null;
  integration_summary: IntegrationSummary | null;
  created_at: string;
  updated_at: string;
};

export type PlatformConnectionList = {
  items: PlatformConnection[];
  total: number;
};

export type FacebookOAuthStartResponse = {
  state: string;
  auth_url: string;
  redirect_uri: string;
  scopes: string[];
};

export type FacebookPageCandidate = {
  page_id: string;
  page_name: string;
  category: string | null;
  tasks: string[];
  picture_url: string | null;
};

export type FacebookOAuthCompleteResponse = {
  state: string;
  pages: FacebookPageCandidate[];
};
