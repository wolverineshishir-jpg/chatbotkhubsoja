import { apiClient } from "../../../lib/api/client";
import type { AutomationWorkflow, AutomationWorkflowListResponse } from "../../../shared/types/automation";

export async function listAutomationWorkflows(): Promise<AutomationWorkflowListResponse> {
  const response = await apiClient.get<AutomationWorkflowListResponse>("/automation/workflows");
  return response.data;
}

export async function createAutomationWorkflow(payload: Record<string, unknown>): Promise<AutomationWorkflow> {
  const response = await apiClient.post<AutomationWorkflow>("/automation/workflows", payload);
  return response.data;
}

export async function updateAutomationWorkflow(workflowId: number, payload: Record<string, unknown>): Promise<AutomationWorkflow> {
  const response = await apiClient.put<AutomationWorkflow>(`/automation/workflows/${workflowId}`, payload);
  return response.data;
}

export async function deleteAutomationWorkflow(workflowId: number): Promise<void> {
  await apiClient.delete(`/automation/workflows/${workflowId}`);
}

export async function runAutomationWorkflow(workflowId: number): Promise<{ workflow: AutomationWorkflow; sync_job_id: number }> {
  const response = await apiClient.post<{ workflow: AutomationWorkflow; sync_job_id: number }>(`/automation/workflows/${workflowId}/run`);
  return response.data;
}
