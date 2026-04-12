import { FormEvent, useState } from "react";

import { CustomField } from "../components/common/CustomField";
import { PageHeader } from "../components/common/PageHeader";
import { changePassword } from "../features/auth/api/authApi";
import { useAuthStore } from "../features/auth/store/authStore";

export function ChangePasswordPage() {
  const setSession = useAuthStore((state) => state.setSession);
  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (form.new_password !== form.confirm_password) {
      setError("New password and confirmation do not match.");
      return;
    }

    if (form.current_password === form.new_password) {
      setError("New password must be different from the current password.");
      return;
    }

    setSubmitting(true);

    try {
      const session = await changePassword({
        current_password: form.current_password,
        new_password: form.new_password,
      });
      setSession(session);
      setMessage("Password updated successfully. Your session has been refreshed.");
      setForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to update password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="Account Security"
        title="Change your password"
        description="Confirm your current password, then set a new one. Existing refresh sessions are rotated automatically."
      />

      <form className="panel form-panel security-form security-password-form" onSubmit={handleSubmit}>
        <h3 className="security-password-form-title">Update password</h3>
        <label>
          Current password
          <CustomField
            type="password"
            value={form.current_password}
            onChange={(event) => setForm((current) => ({ ...current, current_password: event.target.value }))}
            placeholder="Enter your current password"
            minLength={8}
            required
          />
        </label>
        <label>
          New password
          <CustomField
            type="password"
            value={form.new_password}
            onChange={(event) => setForm((current) => ({ ...current, new_password: event.target.value }))}
            placeholder="Use a new password"
            minLength={8}
            required
          />
        </label>
        <label>
          Confirm new password
          <CustomField
            type="password"
            value={form.confirm_password}
            onChange={(event) => setForm((current) => ({ ...current, confirm_password: event.target.value }))}
            placeholder="Re-enter the new password"
            minLength={8}
            required
          />
        </label>
        {error ? <p className="form-error security-password-form-note">{error}</p> : null}
        {message ? <div className="panel success-panel security-password-form-note">{message}</div> : null}
        <button type="submit" className="security-password-submit-button" disabled={submitting}>
          {submitting ? "Updating password..." : "Save new password"}
        </button>
      </form>
    </section>
  );
}
