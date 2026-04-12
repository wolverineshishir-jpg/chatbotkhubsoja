import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthSession, AuthUser } from "../../../shared/types/auth";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  activeAccountId: number | null;
  hydrated: boolean;
  setSession: (session: AuthSession) => void;
  setUser: (user: AuthUser) => void;
  setActiveAccountId: (accountId: number | null) => void;
  setHydrated: (value: boolean) => void;
  clear: () => void;
};

const resolveDefaultAccountId = (user: AuthUser): number | null =>
  user.memberships.find((membership) => membership.status === "active")?.account_id ?? null;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      activeAccountId: null,
      hydrated: false,
      setSession: (session) =>
        set({
          accessToken: session.access_token,
          refreshToken: session.refresh_token,
          user: session.user,
          activeAccountId: resolveDefaultAccountId(session.user),
        }),
      setUser: (user) =>
        set((state) => ({
          user,
          activeAccountId:
            state.activeAccountId && user.memberships.some((membership) => membership.account_id === state.activeAccountId)
              ? state.activeAccountId
              : resolveDefaultAccountId(user),
        })),
      setActiveAccountId: (activeAccountId) => set({ activeAccountId }),
      setHydrated: (hydrated) => set({ hydrated }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null, activeAccountId: null }),
    }),
    {
      name: "automation-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        activeAccountId: state.activeAccountId,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true);
      },
    },
  ),
);
