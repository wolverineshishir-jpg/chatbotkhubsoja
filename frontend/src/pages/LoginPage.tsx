import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { CustomField } from "../components/common/CustomField";
import { login } from "../features/auth/api/authApi";
import { useAuthStore } from "../features/auth/store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const session = await login({ email, password });
      setSession(session);
      navigate(location.state?.from || "/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Login failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label>
        Email
        <CustomField
          type="email"
          name="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="owner@example.com"
          required
        />
      </label>
      <label>
        Password
        <CustomField
          type="password"
          name="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          minLength={8}
          required
        />
      </label>
      {error ? <p className="form-error">{error}</p> : null}
      <button type="submit" disabled={submitting}>
        {submitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
