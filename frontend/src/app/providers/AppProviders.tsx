import { PropsWithChildren, useEffect } from "react";

import { fetchCurrentUser } from "../../features/auth/api/authApi";
import { useAuthStore } from "../../features/auth/store/authStore";

export function AppProviders({ children }: PropsWithChildren) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const hydrated = useAuthStore((state) => state.hydrated);
  const setUser = useAuthStore((state) => state.setUser);
  const clear = useAuthStore((state) => state.clear);

  useEffect(() => {
    if (!hydrated || !accessToken) {
      return;
    }

    fetchCurrentUser()
      .then((user) => {
        setUser(user);
      })
      .catch(() => {
        clear();
      });
  }, [accessToken, clear, hydrated, setUser]);

  return children;
}
