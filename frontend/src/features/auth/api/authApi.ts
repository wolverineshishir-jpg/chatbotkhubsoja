import { apiClient } from "../../../lib/api/client";
import type { AuthSession, AuthUser } from "../../../shared/types/auth";

type LoginPayload = {
  email: string;
  password: string;
};

export async function login(payload: LoginPayload): Promise<AuthSession> {
  const response = await apiClient.post<AuthSession>("/auth/login", payload);
  return response.data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>("/auth/me");
  return response.data;
}

export async function logout(refreshToken: string, logoutAll = false): Promise<void> {
  await apiClient.post("/auth/logout", {
    refresh_token: refreshToken,
    logout_all: logoutAll,
  });
}

type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
};

export async function changePassword(payload: ChangePasswordPayload): Promise<AuthSession> {
  const response = await apiClient.post<AuthSession>("/auth/change-password", payload);
  return response.data;
}
