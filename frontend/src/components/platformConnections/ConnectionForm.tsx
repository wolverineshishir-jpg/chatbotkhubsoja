import { FormEvent, useEffect, useState } from "react";

import { CustomField, CustomTextArea } from "../common/CustomField";
import { CustomSelect } from "../common/CustomSelect";
import type { PlatformConnection, PlatformType } from "../../shared/types/platformConnection";

type ConnectionFormProps = {
  initialValue?: PlatformConnection | null;
  submitting: boolean;
  onOpenList?: () => void;
  onSubmit: (payload: {
    platform_type: PlatformType;
    name: string;
    external_id?: string;
    external_name?: string;
    access_token?: string;
    refresh_token?: string;
    webhook?: {
      webhook_url?: string;
      webhook_secret?: string;
      webhook_verify_token?: string;
      webhook_active: boolean;
    };
    metadata_json?: Record<string, unknown>;
    settings_json?: Record<string, unknown>;
  }) => Promise<void>;
  onStartFacebookOAuth: () => Promise<void>;
  onManualFacebookConnect: (payload: {
    page_id: string;
    page_access_token: string;
    connection_name?: string;
    user_access_token?: string;
    webhook_verify_token?: string;
    webhook_secret?: string;
  }) => Promise<void>;
  onManualWhatsAppConnect: (payload: {
    phone_number_id: string;
    access_token: string;
    connection_name?: string;
    business_account_id?: string;
    display_phone_number?: string;
    webhook_verify_token?: string;
    webhook_secret?: string;
  }) => Promise<void>;
  facebookOAuthEnabled: boolean;
};

const formatJson = (value: Record<string, unknown>) => JSON.stringify(value, null, 2);

export function ConnectionForm({
  initialValue,
  submitting,
  onOpenList,
  onSubmit,
  onStartFacebookOAuth,
  onManualFacebookConnect,
  onManualWhatsAppConnect,
  facebookOAuthEnabled,
}: ConnectionFormProps) {
  const [platformType, setPlatformType] = useState<PlatformType>("facebook_page");
  const [name, setName] = useState("");
  const [externalId, setExternalId] = useState("");
  const [externalName, setExternalName] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [webhookVerifyToken, setWebhookVerifyToken] = useState("");
  const [webhookActive, setWebhookActive] = useState(false);
  const [metadataText, setMetadataText] = useState("{}");
  const [settingsText, setSettingsText] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [facebookPageAccessToken, setFacebookPageAccessToken] = useState("");
  const [facebookUserAccessToken, setFacebookUserAccessToken] = useState("");
  const [whatsappAccessToken, setWhatsappAccessToken] = useState("");
  const [whatsappBusinessAccountId, setWhatsappBusinessAccountId] = useState("");
  const [whatsappDisplayPhoneNumber, setWhatsappDisplayPhoneNumber] = useState("");

  useEffect(() => {
    if (!initialValue) {
      setPlatformType("facebook_page");
      setName("");
      setExternalId("");
      setExternalName("");
      setAccessToken("");
      setRefreshToken("");
      setWebhookUrl("");
      setWebhookSecret("");
      setWebhookVerifyToken("");
      setWebhookActive(false);
      setMetadataText("{}");
      setSettingsText("{}");
      setFacebookPageAccessToken("");
      setFacebookUserAccessToken("");
      setWhatsappAccessToken("");
      setWhatsappBusinessAccountId("");
      setWhatsappDisplayPhoneNumber("");
      return;
    }
    setPlatformType(initialValue.platform_type);
    setName(initialValue.name);
    setExternalId(initialValue.external_id ?? "");
    setExternalName(initialValue.external_name ?? "");
    setWebhookUrl(initialValue.webhook.webhook_url ?? "");
    setWebhookActive(initialValue.webhook.webhook_active);
    setMetadataText(formatJson(initialValue.metadata_json));
    setSettingsText(formatJson(initialValue.settings_json));
    setFacebookPageAccessToken("");
    setFacebookUserAccessToken("");
    setWhatsappAccessToken("");
    setWhatsappBusinessAccountId("");
    setWhatsappDisplayPhoneNumber("");
  }, [initialValue]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        platform_type: platformType,
        name,
        external_id: externalId || undefined,
        external_name: externalName || undefined,
        access_token: accessToken || undefined,
        refresh_token: refreshToken || undefined,
        webhook:
          webhookUrl || webhookSecret || webhookVerifyToken || webhookActive
            ? {
                webhook_url: webhookUrl || undefined,
                webhook_secret: webhookSecret || undefined,
                webhook_verify_token: webhookVerifyToken || undefined,
                webhook_active: webhookActive,
              }
            : undefined,
        metadata_json: JSON.parse(metadataText),
        settings_json: JSON.parse(settingsText),
      });
    } catch (err: any) {
      setError(err.message ?? "Unable to save platform connection.");
    }
  };

  const handleWhatsAppManualConnect = async () => {
    setError(null);
    try {
      await onManualWhatsAppConnect({
        phone_number_id: externalId,
        access_token: whatsappAccessToken,
        connection_name: name || undefined,
        business_account_id: whatsappBusinessAccountId || undefined,
        display_phone_number: whatsappDisplayPhoneNumber || undefined,
        webhook_verify_token: webhookVerifyToken || undefined,
        webhook_secret: webhookSecret || undefined,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? "Unable to connect WhatsApp number.");
    }
  };

  const handleFacebookManualConnect = async () => {
    setError(null);
    try {
      await onManualFacebookConnect({
        page_id: externalId,
        page_access_token: facebookPageAccessToken,
        connection_name: name || undefined,
        user_access_token: facebookUserAccessToken || undefined,
        webhook_verify_token: webhookVerifyToken || undefined,
        webhook_secret: webhookSecret || undefined,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? "Unable to connect Facebook Page.");
    }
  };

  return (
    <form className="panel form-panel connection-form" onSubmit={handleSubmit}>
      <div className="connection-form-head">
        <h3>{initialValue ? "Edit connection" : "Add connection"}</h3>
        {onOpenList ? (
          <button
            type="button"
            className="ghost-button connection-list-icon-button"
            aria-label="Open connected channels list"
            title="Open list"
            onClick={onOpenList}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" className="connection-list-icon">
              <path d="M4 6h16" />
              <path d="M4 12h16" />
              <path d="M4 18h16" />
            </svg>
          </button>
        ) : null}
      </div>
      {!initialValue && platformType === "facebook_page" ? (
        <div className="connection-helper-card">
          <h4>Facebook Page connection</h4>
          <p className="muted-copy">
            Use OAuth for the cleanest admin flow, or connect manually with a Page access token if your app is still being configured.
          </p>
          <div className="connection-helper-actions">
            <button type="button" className="ghost-button" onClick={() => void onStartFacebookOAuth()} disabled={!facebookOAuthEnabled || submitting}>
              Connect with Facebook OAuth
            </button>
          </div>
          {!facebookOAuthEnabled ? <p className="form-hint">Set `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` on the backend to enable OAuth.</p> : null}
        </div>
      ) : null}
      {!initialValue && platformType === "whatsapp" ? (
        <div className="connection-helper-card">
          <h4>WhatsApp Business setup</h4>
          <p className="muted-copy">
            Connect a WhatsApp phone number with a Cloud API access token, then enable webhook verification for inbound messages.
          </p>
          <p className="form-hint">
            Use `phone_number_id` as External ID. Keep webhook verify token aligned with your Meta webhook configuration.
          </p>
        </div>
      ) : null}
      <label>
        Platform type
        <CustomSelect
          value={platformType}
          onChange={(value) => setPlatformType(value as PlatformType)}
          options={[
            { value: "facebook_page", label: "Facebook Page" },
            { value: "whatsapp", label: "WhatsApp" },
          ]}
        />
      </label>
      <label>
        Display name
        <CustomField value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      <label>
        External ID
        <CustomField value={externalId} onChange={(event) => setExternalId(event.target.value)} placeholder={platformType === "facebook_page" ? "Facebook Page ID" : "Optional page or phone ID"} />
      </label>
      <label>
        External name
        <CustomField value={externalName} onChange={(event) => setExternalName(event.target.value)} placeholder="Optional upstream label" />
      </label>
      <label>
        Access token
        <CustomField
          type="password"
          value={accessToken}
          onChange={(event) => setAccessToken(event.target.value)}
          placeholder={initialValue?.token_hint ? `Stored token ${initialValue.token_hint}` : "Optional during draft setup"}
        />
      </label>
      <label>
        Refresh token
        <CustomField type="password" value={refreshToken} onChange={(event) => setRefreshToken(event.target.value)} />
      </label>
      <label className="field-full">
        Webhook URL
        <CustomField value={webhookUrl} onChange={(event) => setWebhookUrl(event.target.value)} placeholder="https://example.com/webhooks/platform" />
      </label>
      <label>
        Webhook secret
        <CustomField value={webhookSecret} onChange={(event) => setWebhookSecret(event.target.value)} />
      </label>
      <label>
        Webhook verify token
        <CustomField value={webhookVerifyToken} onChange={(event) => setWebhookVerifyToken(event.target.value)} />
      </label>
      {!initialValue && platformType === "facebook_page" ? (
        <>
          <label>
            Facebook Page access token
            <CustomField
              type="password"
              value={facebookPageAccessToken}
              onChange={(event) => setFacebookPageAccessToken(event.target.value)}
              placeholder="Required for manual Facebook connection"
            />
          </label>
          <label>
            Facebook user access token
            <CustomField
              type="password"
              value={facebookUserAccessToken}
              onChange={(event) => setFacebookUserAccessToken(event.target.value)}
              placeholder="Optional long-lived user token"
            />
          </label>
          <button
            type="button"
            className="secondary-action connection-facebook-manual-button"
            onClick={() => void handleFacebookManualConnect()}
            disabled={submitting || !externalId || !facebookPageAccessToken}
          >
            Connect Facebook manually
          </button>
          <label className="connection-webhook-toggle">
            <input
              type="checkbox"
              className="connection-webhook-checkbox"
              checked={webhookActive}
              onChange={(event) => setWebhookActive(event.target.checked)}
            />
            <span className="connection-webhook-inline-text">Webhook active</span>
          </label>
        </>
      ) : null}
      {!initialValue && platformType === "whatsapp" ? (
        <>
          <label>
            WhatsApp access token
            <CustomField
              type="password"
              value={whatsappAccessToken}
              onChange={(event) => setWhatsappAccessToken(event.target.value)}
              placeholder="Required for WhatsApp Cloud API"
            />
          </label>
          <label>
            Business account ID
            <CustomField
              value={whatsappBusinessAccountId}
              onChange={(event) => setWhatsappBusinessAccountId(event.target.value)}
              placeholder="Optional WABA ID"
            />
          </label>
          <label>
            Display phone number
            <CustomField
              value={whatsappDisplayPhoneNumber}
              onChange={(event) => setWhatsappDisplayPhoneNumber(event.target.value)}
              placeholder="Optional display number"
            />
          </label>
          <button
            type="button"
            className="secondary-action"
            onClick={() => void handleWhatsAppManualConnect()}
            disabled={submitting || !externalId || !whatsappAccessToken}
          >
            Connect WhatsApp manually
          </button>
        </>
      ) : null}
      {!(!initialValue && platformType === "facebook_page") ? (
        <label className="connection-webhook-toggle field-full">
          <input
            type="checkbox"
            className="connection-webhook-checkbox"
            checked={webhookActive}
            onChange={(event) => setWebhookActive(event.target.checked)}
          />
          <span className="connection-webhook-copy">
            <strong>Webhook active</strong>
            <small>Enable only after webhook URL and verify token are configured correctly.</small>
          </span>
        </label>
      ) : null}
      <label className="field-full">
        Metadata JSON
        <CustomTextArea value={metadataText} onChange={(event) => setMetadataText(event.target.value)} rows={5} />
      </label>
      <label className="field-full">
        Settings JSON
        <CustomTextArea value={settingsText} onChange={(event) => setSettingsText(event.target.value)} rows={5} />
      </label>
      {error ? <p className="form-error">{error}</p> : null}
      {initialValue?.integration_summary ? (
        <div className="connection-summary">
          <div><strong>Sync:</strong> {initialValue.integration_summary.sync_state || "pending"}</div>
          <div><strong>Token:</strong> {initialValue.integration_summary.token_status || "unknown"}</div>
          <div><strong>Webhook:</strong> {initialValue.integration_summary.webhook_subscription_state || "pending"}</div>
        </div>
      ) : null}
      <button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : initialValue ? "Save changes" : "Create connection"}
      </button>
    </form>
  );
}
