import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { LoadingPanel } from "../components/common/LoadingPanel";
import { ConnectionForm } from "../components/platformConnections/ConnectionForm";
import { useAuthStore } from "../features/auth/store/authStore";
import {
  connectWhatsAppManual,
  connectFacebookManualPage,
  createPlatformConnection,
  disconnectPlatformConnection,
  listPlatformConnections,
  startFacebookOAuth,
  subscribeFacebookConnectionWebhooks,
  syncFacebookConnection,
  syncWhatsAppConnection,
  updatePlatformConnection,
} from "../features/platformConnections/api/platformConnectionApi";
import type { PlatformConnection } from "../shared/types/platformConnection";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  connected: "Connected",
  action_required: "Action required",
  disconnected: "Disconnected",
  error: "Error",
};

export function ConnectionsPage() {
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const location = useLocation();
  const navigate = useNavigate();
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [selected, setSelected] = useState<PlatformConnection | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [showConnectionsList, setShowConnectionsList] = useState(false);
  const facebookOAuthEnabled = (import.meta.env.VITE_FACEBOOK_OAUTH_ENABLED ?? "true") !== "false";

  const loadConnections = async () => {
    setLoading(true);
    try {
      const response = await listPlatformConnections();
      setConnections(response.items);
      setError(null);
      if (selected) {
        setSelected(response.items.find((item) => item.id === selected.id) ?? null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load platform connections.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, [activeAccountId]);

  useEffect(() => {
    const message = (location.state as { message?: string } | null)?.message;
    if (message) {
      setActionMessage(message);
      navigate(location.pathname, { replace: true });
    }
  }, [location.pathname, location.state, navigate]);

  const handleSubmit = async (payload: any) => {
    setSaving(true);
    try {
      if (selected) {
        await updatePlatformConnection(selected.id, payload);
      } else {
        await createPlatformConnection(payload);
      }
      await loadConnections();
      setSelected(null);
      setActionMessage("Connection saved.");
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async (connectionId: number) => {
    await disconnectPlatformConnection(connectionId);
    await loadConnections();
    setActionMessage("Connection disconnected.");
  };

  const handleFacebookOAuthStart = async () => {
    try {
      const response = await startFacebookOAuth();
      window.location.href = response.auth_url;
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to start Facebook OAuth.");
    }
  };

  const handleFacebookManualConnect = async (payload: {
    page_id: string;
    page_access_token: string;
    connection_name?: string;
    user_access_token?: string;
    webhook_verify_token?: string;
    webhook_secret?: string;
  }) => {
    setSaving(true);
    try {
      await connectFacebookManualPage(payload);
      await loadConnections();
      setSelected(null);
      setActionMessage("Facebook Page connected.");
    } finally {
      setSaving(false);
    }
  };

  const handleSyncFacebook = async (connectionId: number) => {
    setSaving(true);
    try {
      await syncFacebookConnection(connectionId);
      await loadConnections();
      setActionMessage("Facebook connection synced.");
    } finally {
      setSaving(false);
    }
  };

  const handleSyncWhatsApp = async (connectionId: number) => {
    setSaving(true);
    try {
      await syncWhatsAppConnection(connectionId);
      await loadConnections();
      setActionMessage("WhatsApp connection synced.");
    } finally {
      setSaving(false);
    }
  };

  const handleSubscribeFacebook = async (connectionId: number) => {
    setSaving(true);
    try {
      await subscribeFacebookConnectionWebhooks(connectionId);
      await loadConnections();
      setActionMessage("Facebook webhooks subscribed.");
    } finally {
      setSaving(false);
    }
  };

  const handleWhatsAppManualConnect = async (payload: {
    phone_number_id: string;
    access_token: string;
    connection_name?: string;
    business_account_id?: string;
    display_phone_number?: string;
    webhook_verify_token?: string;
    webhook_secret?: string;
  }) => {
    setSaving(true);
    try {
      await connectWhatsAppManual(payload);
      await loadConnections();
      setSelected(null);
      setActionMessage("WhatsApp number connected.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section>
      {error ? <div className="panel error-panel">{error}</div> : null}
      {actionMessage ? <div className="panel success-panel">{actionMessage}</div> : null}

      <div className="connections-page-stack">
        {showConnectionsList ? (
          <div className="table-card connections-table-card">
            <div className="table-card-header">
              <h3>Connected channels</h3>
              <button
                type="button"
                className="ghost-button compact-button"
                onClick={() => {
                  setSelected(null);
                  setShowConnectionsList(false);
                }}
              >
                Add connection
              </button>
            </div>
            {loading ? (
              <LoadingPanel message="Loading platform connections..." hint="Refreshing channel sync and webhook status." compact />
            ) : (
              <div className="connections-table-scroll">
                <table className="connections-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Platform</th>
                      <th>Status</th>
                      <th>Webhook</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {connections.map((connection) => (
                      <tr key={connection.id}>
                        <td>
                          <strong>{connection.name}</strong>
                          <div className="muted-copy small-copy">{connection.external_name || connection.external_id || "No external mapping yet"}</div>
                          {connection.integration_summary?.token_status === "action_required" ? (
                            <div className="form-error small-copy">Token or permission attention needed.</div>
                          ) : null}
                          {connection.last_error ? <div className="form-error small-copy">{connection.last_error}</div> : null}
                        </td>
                        <td>{connection.platform_type === "facebook_page" ? "Facebook Page" : "WhatsApp"}</td>
                        <td>
                          <span className={`status-pill status-${connection.status}`}>{STATUS_LABELS[connection.status]}</span>
                          {connection.integration_summary ? (
                            <div className="muted-copy small-copy">
                              {connection.integration_summary.sync_state || "pending"} / {connection.integration_summary.token_status || "unknown"}
                            </div>
                          ) : null}
                          {connection.platform_type === "whatsapp" && !connection.webhook.webhook_active ? (
                            <div className="muted-copy small-copy">Webhook is inactive. Inbound messages will not be received.</div>
                          ) : null}
                        </td>
                        <td>
                          {connection.webhook.webhook_active ? "Active" : "Inactive"}
                          {connection.integration_summary?.webhook_subscription_state ? (
                            <div className="muted-copy small-copy">{connection.integration_summary.webhook_subscription_state}</div>
                          ) : null}
                        </td>
                        <td className="table-actions">
                          <button
                            type="button"
                            className="link-button"
                            onClick={() => {
                              setSelected(connection);
                              setShowConnectionsList(false);
                            }}
                          >
                            Edit
                          </button>
                          {connection.platform_type === "facebook_page" ? (
                            <>
                              <button type="button" className="link-button" onClick={() => void handleSyncFacebook(connection.id)}>
                                Sync
                              </button>
                              <button type="button" className="link-button" onClick={() => void handleSubscribeFacebook(connection.id)}>
                                Subscribe
                              </button>
                            </>
                          ) : null}
                          {connection.platform_type === "whatsapp" ? (
                            <button type="button" className="link-button" onClick={() => void handleSyncWhatsApp(connection.id)}>
                              Sync
                            </button>
                          ) : null}
                          <button type="button" className="link-button danger-link" onClick={() => handleDisconnect(connection.id)}>
                            Disconnect
                          </button>
                        </td>
                      </tr>
                    ))}
                    {connections.length === 0 ? (
                      <tr>
                        <td colSpan={5}>No platform connections yet.</td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <ConnectionForm
            initialValue={selected}
            submitting={saving}
            onOpenList={() => setShowConnectionsList(true)}
            onSubmit={handleSubmit}
            onStartFacebookOAuth={handleFacebookOAuthStart}
            onManualFacebookConnect={handleFacebookManualConnect}
            onManualWhatsAppConnect={handleWhatsAppManualConnect}
            facebookOAuthEnabled={facebookOAuthEnabled}
          />
        )}
      </div>
    </section>
  );
}
