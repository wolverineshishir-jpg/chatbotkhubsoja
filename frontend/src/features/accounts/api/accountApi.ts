import { apiClient } from "../../../lib/api/client";
import type { CurrentAccount, TeamMember } from "../../../shared/types/account";

export async function getCurrentAccount(): Promise<CurrentAccount> {
  const response = await apiClient.get<CurrentAccount>("/accounts/current");
  return response.data;
}

export async function listTeamMembers(): Promise<TeamMember[]> {
  const response = await apiClient.get<TeamMember[]>("/accounts/current/members");
  return response.data;
}
