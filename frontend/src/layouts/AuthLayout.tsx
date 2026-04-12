import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <section className="auth-showcase">
          <h1>Run support, content, and AI workflows from one polished workspace.</h1>
          <p>Sign in to manage conversations, automate responses, review activity, and keep the whole team aligned.</p>
          <div className="auth-feature-list">
            <div className="auth-feature">
              <strong>Owner-managed access</strong>
              <span>System owner creates super admins, and super admins manage their admin team.</span>
            </div>
            <div className="auth-feature">
              <strong>Live operations</strong>
              <span>Inbox, comments, posts, billing, and reporting in one place.</span>
            </div>
            <div className="auth-feature">
              <strong>AI assistance</strong>
              <span>Generate drafts, manage prompts, and keep human review in the loop.</span>
            </div>
          </div>
        </section>

        <section className="auth-main">
          <div className="auth-header">
            <h2>Welcome back</h2>
            <p>Use your account credentials to enter the workspace and continue where your team left off.</p>
          </div>
          <Outlet />
        </section>
      </div>
    </div>
  );
}
