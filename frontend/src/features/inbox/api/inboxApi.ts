import { apiClient } from "../../../lib/api/client";
import type {
  ConversationDetail,
  ConversationListResponse,
  ConversationStatus,
  ConversationSummary,
  InboxMessage,
  MessageListResponse,
  SenderType,
} from "../../../shared/types/inbox";
import type { PlatformType } from "../../../shared/types/platformConnection";

export async function listConversations(params?: {
  status?: ConversationStatus | "";
  platform?: PlatformType | "";
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<ConversationListResponse> {
  const sanitizedParams = Object.fromEntries(
    Object.entries(params ?? {}).filter(([, value]) => value !== "" && value !== undefined && value !== null),
  );
  const response = await apiClient.get<ConversationListResponse>("/inbox/conversations", { params: sanitizedParams });
  return response.data;
}

export async function getConversation(conversationId: number): Promise<ConversationDetail> {
  const response = await apiClient.get<ConversationDetail>(`/inbox/conversations/${conversationId}`);
  return response.data;
}

export async function listConversationMessages(
  conversationId: number,
  params?: { page?: number; page_size?: number },
): Promise<MessageListResponse> {
  const response = await apiClient.get<MessageListResponse>(`/inbox/conversations/${conversationId}/messages`, { params });
  return response.data;
}

export async function assignConversation(
  conversationId: number,
  assigneeUserId: number | null,
): Promise<ConversationSummary> {
  const response = await apiClient.post<ConversationSummary>(`/inbox/conversations/${conversationId}/assign`, {
    assignee_user_id: assigneeUserId,
  });
  return response.data;
}

export async function updateConversationStatus(
  conversationId: number,
  payload: { status: ConversationStatus; paused_until?: string | null },
): Promise<ConversationSummary> {
  const response = await apiClient.patch<ConversationSummary>(`/inbox/conversations/${conversationId}/status`, payload);
  return response.data;
}

export async function sendReply(
  conversationId: number,
  payload: { content: string; sender_type: Extract<SenderType, "human_admin" | "llm_bot"> },
): Promise<InboxMessage> {
  const response = await apiClient.post<InboxMessage>(`/inbox/conversations/${conversationId}/reply`, payload);
  return response.data;
}
