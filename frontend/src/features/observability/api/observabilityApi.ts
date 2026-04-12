import { apiClient } from "../../../lib/api/client";
import type {
  ActionUsageLogListResponse,
  AuditLogListResponse,
  LLMTokenUsageListResponse,
} from "../../../shared/types/observability";

export async function listActionUsageLogs(params?: { page?: number; page_size?: number }): Promise<ActionUsageLogListResponse> {
  const response = await apiClient.get<ActionUsageLogListResponse>("/observability/action-usage-logs", { params });
  return response.data;
}

export async function listLlmTokenUsage(params?: { page?: number; page_size?: number }): Promise<LLMTokenUsageListResponse> {
  const response = await apiClient.get<LLMTokenUsageListResponse>("/observability/llm-token-usage", { params });
  return response.data;
}

export async function listAuditLogs(params?: { page?: number; page_size?: number }): Promise<AuditLogListResponse> {
  const response = await apiClient.get<AuditLogListResponse>("/observability/audit-logs", { params });
  return response.data;
}
