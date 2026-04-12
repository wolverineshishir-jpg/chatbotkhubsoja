import { Navigate, Outlet, useLocation } from "react-router-dom";

import { LoadingPanel } from "../common/LoadingPanel";
import { useAuthStore } from "../../features/auth/store/authStore";

export function ProtectedRoute() {
  const location = useLocation();
  const accessToken = useAuthStore((state) => state.accessToken);
  const hydrated = useAuthStore((state) => state.hydrated);

  if (!hydrated) {
    return <LoadingPanel message="Loading session..." hint="Checking your account access and token state." fullscreen />;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
