import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { LoadingPanel } from "../components/common/LoadingPanel";
import { PageHeader } from "../components/common/PageHeader";
import { getCurrentAccount } from "../features/accounts/api/accountApi";
import { useAuthStore } from "../features/auth/store/authStore";
import { listPlatformConnections } from "../features/platformConnections/api/platformConnectionApi";
import type { CurrentAccount } from "../shared/types/account";
import type { PlatformConnection } from "../shared/types/platformConnection";

export function SetupWizardPage() {
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const [account, setAccount] = useState<CurrentAccount | null>(null);
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCurrentAccount(), listPlatformConnections()])
      .then(([accountResponse, connectionResponse]) => {
        setAccount(accountResponse);
        setConnections(connectionResponse.items);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [activeAccountId]);

  const progress = useMemo(() => {
    const hasFacebook = connections.some((item) => item.platform_type === "facebook_page" && item.status === "connected");
    const hasWhatsApp = connections.some((item) => item.platform_type === "whatsapp" && item.status === "connected");
    return [
      { title: "Account selected", done: Boolean(account) },
      { title: "Facebook Page connected", done: hasFacebook },
      { title: "WhatsApp connected", done: hasWhatsApp },
      { title: "Automation-ready foundation", done: hasFacebook || hasWhatsApp },
    ];
  }, [account, connections]);

  const completed = progress.filter((step) => step.done).length;

  return (
    <section>
      <PageHeader
        eyebrow="Setup"
        title="Account setup wizard"
        description="Guide operators through channel onboarding so AI prompts, inbox automation, and post/comment automation can plug into verified account connections later."
      />

      {loading ? <LoadingPanel message="Loading setup progress..." hint="Checking connected channels and workspace readiness." /> : null}

      {!loading ? (
        <div className="dashboard-grid wizard-layout">
          <div className="panel">
            <h3>Progress</h3>
            <p className="muted-copy">
              {completed} of {progress.length} setup checkpoints completed.
            </p>
            <div className="progress-bar">
              <span style={{ width: `${(completed / progress.length) * 100}%` }} />
            </div>
            <div className="wizard-steps">
              {progress.map((step) => (
                <div key={step.title} className={`wizard-step ${step.done ? "done" : ""}`}>
                  <strong>{step.title}</strong>
                  <span>{step.done ? "Complete" : "Pending"}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>Active account</h3>
            <p className="muted-copy">{account ? `${account.name} (${account.slug})` : "No active account context."}</p>
            <p className="muted-copy">
              Connect channels from the dedicated management screen, then continue with prompts, inbox routing, and automation modules in later milestones.
            </p>
            <Link className="text-link setup-link" to="/connections">
              Manage platform connections
            </Link>
          </div>
        </div>
      ) : null}
    </section>
  );
}
