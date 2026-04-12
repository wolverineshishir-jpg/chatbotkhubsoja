import { apiClient } from "../../../lib/api/client";
import type {
  ConnectionStatus,
  FacebookOAuthCompleteResponse,
  FacebookOAuthStartResponse,
  PlatformConnection,
  PlatformConnectionList,
  PlatformType,
} from "../../../shared/types/platformConnection";

export type PlatformConnectionPayload = {
  platform_type: PlatformType;
  name: string;
  external_id?: string;
  external_name?: string;
  access_token?: string;
  refresh_token?: string;
  webhook?: {
    webhook_url?: string;
    webhook_secret?: string;
    webhook_verify_token?: string;
    webhook_active: boolean;
  };
  metadata_json?: Record<string, unknown>;
  settings_json?: Record<string, unknown>;
  last_error?: string;
};

export async function listPlatformConnections(): Promise<PlatformConnectionList> {
  const response = await apiClient.get<PlatformConnectionList>("/platform-connections");
  return response.data;
}

export async function getPlatformConnection(connectionId: number): Promise<PlatformConnection> {
  const response = await apiClient.get<PlatformConnection>(`/platform-connections/${connectionId}`);
  return response.data;
}

export async function createPlatformConnection(payload: PlatformConnectionPayload): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>("/platform-connections", payload);
  return response.data;
}

export async function updatePlatformConnection(
  connectionId: number,
  payload: Omit<PlatformConnectionPayload, "platform_type"> & { platform_type?: PlatformType },
): Promise<PlatformConnection> {
  const response = await apiClient.put<PlatformConnection>(`/platform-connections/${connectionId}`, payload);
  return response.data;
}

export async function disconnectPlatformConnection(connectionId: number): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>(`/platform-connections/${connectionId}/disconnect`);
  return response.data;
}

export async function deletePlatformConnection(connectionId: number): Promise<void> {
  await apiClient.delete(`/platform-connections/${connectionId}`);
}

export async function updatePlatformConnectionStatus(
  connectionId: number,
  payload: { status: ConnectionStatus; last_error?: string },
): Promise<PlatformConnection> {
  const response = await apiClient.patch<PlatformConnection>(`/platform-connections/${connectionId}/status`, payload);
  return response.data;
}

export async function startFacebookOAuth(): Promise<FacebookOAuthStartResponse> {
  const response = await apiClient.post<FacebookOAuthStartResponse>("/platform-connections/facebook/oauth/start");
  return response.data;
}

export async function completeFacebookOAuth(payload: { state: string; code: string }): Promise<FacebookOAuthCompleteResponse> {
  const response = await apiClient.post<FacebookOAuthCompleteResponse>("/platform-connections/facebook/oauth/complete", payload);
  return response.data;
}

export async function connectFacebookOAuthPage(payload: {
  state: string;
  page_id: string;
  connection_name?: string;
  webhook_verify_token?: string;
  webhook_secret?: string;
}): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>("/platform-connections/facebook/oauth/connect", payload);
  return response.data;
}

export async function connectFacebookManualPage(payload: {
  page_id: string;
  page_access_token: string;
  connection_name?: string;
  user_access_token?: string;
  webhook_verify_token?: string;
  webhook_secret?: string;
}): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>("/platform-connections/facebook/manual-connect", payload);
  return response.data;
}

export async function connectWhatsAppManual(payload: {
  phone_number_id: string;
  access_token: string;
  connection_name?: string;
  business_account_id?: string;
  display_phone_number?: string;
  webhook_verify_token?: string;
  webhook_secret?: string;
}): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>("/platform-connections/whatsapp/manual-connect", payload);
  return response.data;
}

export async function syncFacebookConnection(connectionId: number): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>(`/platform-connections/${connectionId}/facebook/sync`);
  return response.data;
}

export async function subscribeFacebookConnectionWebhooks(connectionId: number): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>(`/platform-connections/${connectionId}/facebook/subscribe-webhooks`);
  return response.data;
}

export async function syncWhatsAppConnection(connectionId: number): Promise<PlatformConnection> {
  const response = await apiClient.post<PlatformConnection>(`/platform-connections/${connectionId}/whatsapp/sync`);
  return response.data;
}
