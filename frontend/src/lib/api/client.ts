import axios from "axios";

import { useAuthStore } from "../../features/auth/store/authStore";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

const authClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const { accessToken, activeAccountId } = useAuthStore.getState();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  if (activeAccountId) {
    config.headers["X-Account-ID"] = String(activeAccountId);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as { _retry?: boolean } & typeof error.config;
    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    const store = useAuthStore.getState();
    if (!store.refreshToken) {
      store.clear();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const refreshResponse = await authClient.post("/auth/refresh", {
        refresh_token: store.refreshToken,
      });
      store.setSession(refreshResponse.data);
      originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      store.clear();
      return Promise.reject(refreshError);
    }
  },
);
