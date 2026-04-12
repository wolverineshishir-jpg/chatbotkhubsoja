import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { CustomField } from "../components/common/CustomField";
import { LoadingPanel } from "../components/common/LoadingPanel";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import {
  completeFacebookOAuth,
  connectFacebookOAuthPage,
} from "../features/platformConnections/api/platformConnectionApi";
import type { FacebookPageCandidate } from "../shared/types/platformConnection";

export function FacebookConnectionCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [pages, setPages] = useState<FacebookPageCandidate[]>([]);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [connectionName, setConnectionName] = useState("");
  const [webhookVerifyToken, setWebhookVerifyToken] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const completionRequestKeyRef = useRef<string | null>(null);
  const state = useMemo(() => searchParams.get("state") || "", [searchParams]);
  const code = useMemo(() => searchParams.get("code") || "", [searchParams]);
  const oauthError = useMemo(() => searchParams.get("error_description") || searchParams.get("error"), [searchParams]);

  useEffect(() => {
    if (oauthError) {
      setError(oauthError);
      setLoading(false);
      return;
    }
    if (!state || !code) {
      setError("Facebook OAuth callback is missing the required state or code.");
      setLoading(false);
      return;
    }

    const requestKey = `${state}:${code}`;
    if (completionRequestKeyRef.current === requestKey) {
      return;
    }
    completionRequestKeyRef.current = requestKey;

    const loadPages = async () => {
      setLoading(true);
      try {
        const response = await completeFacebookOAuth({ state, code });
        setPages(response.pages);
        if (response.pages.length > 0) {
          setSelectedPageId(response.pages[0].page_id);
          setConnectionName(response.pages[0].page_name);
        } else {
          setSelectedPageId("");
          setConnectionName("");
        }
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Unable to complete Facebook OAuth.");
      } finally {
        setLoading(false);
      }
    };

    void loadPages();
  }, [code, oauthError, state]);

  const handleConnect = async () => {
    setSaving(true);
    setError(null);
    try {
      await connectFacebookOAuthPage({
        state,
        page_id: selectedPageId,
        connection_name: connectionName || undefined,
        webhook_verify_token: webhookVerifyToken || undefined,
        webhook_secret: webhookSecret || undefined,
      });
      navigate("/connections", {
        replace: true,
        state: { message: "Facebook Page connected successfully." },
      });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to connect the selected Facebook Page.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="Facebook"
        title="Complete Facebook Page connection"
        description="Review the Pages returned by Facebook, then connect the one you want to use inside this account."
      />

      {loading ? <LoadingPanel message="Loading Facebook Pages..." hint="Finalizing OAuth and fetching your page list." /> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      {!loading && !error ? (
        <div className="panel form-panel connection-form facebook-page-selection-form">
          <h3 className="facebook-page-selection-form-title">Select a Facebook Page</h3>
          <p className="facebook-page-selection-form-note muted-copy">
            Choose the Page returned by Meta, confirm the connection label, then finish the channel setup for this account.
          </p>
          {pages.length === 0 ? (
            <div className="facebook-page-selection-empty-state">
              <strong>No Facebook Pages were returned by Meta.</strong>
              <p className="muted-copy">
                This usually means the signed-in Facebook account does not manage any Pages, the Page is not granted to this account,
                or the app still lacks the required Page permissions for this user.
              </p>
            </div>
          ) : null}
          <label>
            Page
            <CustomSelect
              value={selectedPageId}
              onChange={setSelectedPageId}
              options={pages.map((page) => ({
                value: page.page_id,
                label: `${page.page_name}${page.category ? ` (${page.category})` : ""}`,
              }))}
            />
          </label>
          <label>
            Connection name
            <CustomField value={connectionName} onChange={(event) => setConnectionName(event.target.value)} />
          </label>
          <label>
            Webhook verify token
            <CustomField value={webhookVerifyToken} onChange={(event) => setWebhookVerifyToken(event.target.value)} placeholder="Optional custom verify token" />
          </label>
          <label>
            Webhook app secret override
            <CustomField value={webhookSecret} onChange={(event) => setWebhookSecret(event.target.value)} placeholder="Optional connection-specific secret" />
          </label>
          <button
            type="button"
            className="facebook-page-selection-submit-button"
            onClick={() => void handleConnect()}
            disabled={saving || !selectedPageId}
          >
            {saving ? "Connecting..." : "Connect selected Page"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
