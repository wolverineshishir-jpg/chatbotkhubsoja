import { apiClient } from "../../../lib/api/client";
import type {
  BillingSummary,
  CommentStats,
  ConversationStats,
  DashboardSummary,
  PostStats,
  TokenUsageSummary,
} from "../../../shared/types/reports";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>("/reports/dashboard-summary");
  return response.data;
}

export async function getTokenUsageSummary(): Promise<TokenUsageSummary> {
  const response = await apiClient.get<TokenUsageSummary>("/reports/token-usage-summary");
  return response.data;
}

export async function getBillingSummary(): Promise<BillingSummary> {
  const response = await apiClient.get<BillingSummary>("/reports/billing-summary");
  return response.data;
}

export async function getConversationStats(): Promise<ConversationStats> {
  const response = await apiClient.get<ConversationStats>("/reports/conversation-stats");
  return response.data;
}

export async function getCommentStats(): Promise<CommentStats> {
  const response = await apiClient.get<CommentStats>("/reports/comment-stats");
  return response.data;
}

export async function getPostStats(): Promise<PostStats> {
  const response = await apiClient.get<PostStats>("/reports/post-stats");
  return response.data;
}
