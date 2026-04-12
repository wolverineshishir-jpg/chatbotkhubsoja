import { FormEvent, useEffect, useMemo, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { LoadingPanel } from "../components/common/LoadingPanel";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { listTeamMembers } from "../features/accounts/api/accountApi";
import { generateInboxReply } from "../features/ai/api/aiApi";
import {
  assignConversation,
  getConversation,
  listConversations,
  sendReply,
  updateConversationStatus,
} from "../features/inbox/api/inboxApi";
import { useAuthStore } from "../features/auth/store/authStore";
import type { TeamMember } from "../shared/types/account";
import type {
  ConversationDetail,
  ConversationStatus,
  ConversationSummary,
  InboxMessage,
  SenderType,
} from "../shared/types/inbox";
import type { PlatformType } from "../shared/types/platformConnection";

const STATUS_OPTIONS: Array<{ value: ConversationStatus; label: string }> = [
  { value: "open", label: "Open" },
  { value: "assigned", label: "Assigned" },
  { value: "paused", label: "Paused" },
  { value: "resolved", label: "Resolved" },
  { value: "escalated", label: "Escalated" },
];

const PLATFORM_OPTIONS: Array<{ value: PlatformType; label: string }> = [
  { value: "facebook_page", label: "Facebook" },
  { value: "whatsapp", label: "WhatsApp" },
];

const DELIVERY_LABELS: Record<string, string> = {
  pending: "Pending",
  queued: "Queued",
  sent: "Sent",
  delivered: "Delivered",
  failed: "Failed",
};

type InboxPageProps = {
  defaultPlatform?: PlatformType;
  eyebrow?: string;
  title?: string;
  description?: string;
};

export function InboxPage({
  defaultPlatform,
  eyebrow = "Inbox",
  title = "Conversation inbox",
  description = "Review customer threads across Facebook Page and WhatsApp, coordinate assignment, and send human or AI-assisted replies inside the active account.",
}: InboxPageProps) {
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const currentUser = useAuthStore((state) => state.user);

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [sending, setSending] = useState(false);
  const [generatingReply, setGeneratingReply] = useState(false);
  const [updatingMeta, setUpdatingMeta] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [replySenderType, setReplySenderType] = useState<Extract<SenderType, "human_admin" | "llm_bot">>("human_admin");
  const [assigneeUserId, setAssigneeUserId] = useState("unassigned");
  const [filters, setFilters] = useState({
    status: "" as ConversationStatus | "",
    platform: (defaultPlatform ?? "") as PlatformType | "",
    search: "",
  });

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? detail,
    [conversations, detail, selectedConversationId],
  );

  const loadConversations = async (preferredId?: number | null) => {
    setLoadingList(true);
    try {
      const response = await listConversations({
        status: filters.status,
        platform: filters.platform,
        search: filters.search || undefined,
      });
      setConversations(response.items);
      setError(null);

      const nextSelectedId = preferredId ?? selectedConversationId;
      if (nextSelectedId && response.items.some((conversation) => conversation.id === nextSelectedId)) {
        setSelectedConversationId(nextSelectedId);
      } else {
        setSelectedConversationId(response.items[0]?.id ?? null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load conversations.");
      setConversations([]);
      setSelectedConversationId(null);
    } finally {
      setLoadingList(false);
    }
  };

  const loadConversationDetail = async (conversationId: number) => {
    setLoadingDetail(true);
    try {
      const response = await getConversation(conversationId);
      setDetail(response);
      setAssigneeUserId(response.assigned_to?.user_id ? String(response.assigned_to.user_id) : "unassigned");
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load conversation.");
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    loadConversations(null);
    listTeamMembers()
      .then(setTeamMembers)
      .catch(() => setTeamMembers([]));
  }, [activeAccountId, filters.status, filters.platform]);

  useEffect(() => {
    setFilters((current) => ({
      ...current,
      platform: (defaultPlatform ?? "") as PlatformType | "",
    }));
  }, [defaultPlatform]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      loadConversations(selectedConversationId);
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [filters.search]);

  useEffect(() => {
    if (selectedConversationId) {
      loadConversationDetail(selectedConversationId);
    } else {
      setDetail(null);
    }
  }, [selectedConversationId]);

  const applyConversationUpdate = (updated: ConversationSummary) => {
    setConversations((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    setDetail((current) =>
      current && current.id === updated.id
        ? {
            ...current,
            ...updated,
          }
        : current,
    );
  };

  const handleAssign = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedConversationId) return;
    setUpdatingMeta(true);
    try {
      const updated = await assignConversation(
        selectedConversationId,
        assigneeUserId !== "unassigned" ? Number(assigneeUserId) : null,
      );
      applyConversationUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to update assignee.");
    } finally {
      setUpdatingMeta(false);
    }
  };

  const handleStatusChange = async (status: ConversationStatus) => {
    if (!selectedConversationId) return;
    setUpdatingMeta(true);
    try {
      const updated = await updateConversationStatus(selectedConversationId, { status });
      applyConversationUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to update status.");
    } finally {
      setUpdatingMeta(false);
    }
  };

  const handleSendReply = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedConversationId || !reply.trim()) return;
    setSending(true);
    try {
      const message = await sendReply(selectedConversationId, {
        content: reply.trim(),
        sender_type: replySenderType,
      });
      setReply("");
      setDetail((current) =>
        current && current.id === selectedConversationId
          ? {
              ...current,
              latest_message_preview: message.content,
              latest_message_at: message.created_at,
              messages_total: current.messages_total + 1,
              messages: [...current.messages, message],
            }
          : current,
      );
      await loadConversations(selectedConversationId);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to send reply.");
    } finally {
      setSending(false);
    }
  };

  const handleGenerateReply = async () => {
    if (!selectedConversationId || !selectedConversation) return;
    setGeneratingReply(true);
    try {
      const result = await generateInboxReply({
        conversation_id: selectedConversationId,
        platform_connection_id: selectedConversation.platform_connection_id ?? undefined,
        persist_draft: false,
      });
      setReply(result.content);
      setReplySenderType("llm_bot");
      if (result.requires_approval) {
        setError("AI draft generated and requires human approval before sending.");
      } else {
        setError(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to generate AI reply.");
    } finally {
      setGeneratingReply(false);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
      />

      {error ? <div className="panel error-panel">{error}</div> : null}

      <div className="inbox-page">
        <aside className="inbox-sidebar">
          <div className="panel inbox-toolbar">
            <label>
              Status
              <CustomSelect
                value={filters.status}
                onChange={(value) => setFilters((current) => ({ ...current, status: value as ConversationStatus | "" }))}
                options={[{ value: "", label: "All statuses" }, ...STATUS_OPTIONS]}
              />
            </label>
            {!defaultPlatform ? (
              <label>
                Platform
                <CustomSelect
                  value={filters.platform}
                  onChange={(value) => setFilters((current) => ({ ...current, platform: value as PlatformType | "" }))}
                  options={[{ value: "", label: "All platforms" }, ...PLATFORM_OPTIONS]}
                />
              </label>
            ) : null}
            <label>
              Search
              <CustomField
                type="search"
                value={filters.search}
                onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
                placeholder="Customer name or external ID"
              />
            </label>
          </div>

          <div className="table-card inbox-list">
            <div className="table-card-header">
              <h3>Threads</h3>
              <span className="muted-copy small-copy">{conversations.length} loaded</span>
            </div>
            {loadingList ? (
              <LoadingPanel message="Loading conversations..." hint="Fetching the latest inbox threads." compact />
            ) : null}
            {!loadingList && conversations.length === 0 ? (
              <div className="panel">No conversations match the current filters.</div>
            ) : null}
            <div className="conversation-list">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`conversation-row ${selectedConversationId === conversation.id ? "active" : ""}`}
                  onClick={() => setSelectedConversationId(conversation.id)}
                >
                  <div className="conversation-row-top">
                    <strong>{conversation.customer_name || conversation.customer_external_id}</strong>
                    <span className={`status-pill status-${conversation.status}`}>{conversation.status}</span>
                  </div>
                  <div className="muted-copy small-copy">
                    {conversation.platform_type === "facebook_page" ? "Facebook Page" : "WhatsApp"}
                    {" | "}
                    {conversation.assigned_to?.full_name || conversation.assigned_to?.email || "Unassigned"}
                  </div>
                  <p>{conversation.latest_message_preview || "No messages yet."}</p>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <div className="inbox-main">
          {!selectedConversation ? (
            <div className="panel inbox-empty">Select a conversation to view the thread.</div>
          ) : (
            <>
              <div className="panel inbox-thread-header">
                <div>
                  <h3>{selectedConversation.customer_name || selectedConversation.customer_external_id}</h3>
                  <p className="muted-copy">
                    {selectedConversation.platform_type === "facebook_page" ? "Facebook Page" : "WhatsApp"}
                    {" | "}
                    {selectedConversation.external_thread_id || selectedConversation.customer_external_id}
                  </p>
                </div>
                <div className="inbox-status-actions">
                  {STATUS_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={`ghost-button compact-button ${selectedConversation.status === option.value ? "status-active" : ""}`}
                      onClick={() => handleStatusChange(option.value)}
                      disabled={updatingMeta}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="inbox-thread-layout">
                <div className="table-card inbox-thread-card">
                  <div className="thread-scroll">
                    {loadingDetail ? (
                      <LoadingPanel message="Loading thread..." hint="Syncing message history and delivery state." compact />
                    ) : null}
                    {!loadingDetail &&
                      detail?.messages.map((message) => (
                        <article
                          key={message.id}
                          className={`message-bubble ${message.direction === "outbound" ? "outbound" : "inbound"}`}
                        >
                          <div className="message-meta">
                            <strong>{message.sender_name || message.sender_type}</strong>
                            <span>{new Date(message.created_at).toLocaleString()}</span>
                          </div>
                          <p>{message.content}</p>
                          <span className={`message-delivery delivery-${message.delivery_status}`}>
                            {DELIVERY_LABELS[message.delivery_status]}
                          </span>
                        </article>
                      ))}
                  </div>

                  <form className="reply-box" onSubmit={handleSendReply}>
                    <div className="reply-toolbar">
                      <CustomSelect
                        value={replySenderType}
                        onChange={(value) => setReplySenderType(value as Extract<SenderType, "human_admin" | "llm_bot">)}
                        options={[
                          { value: "human_admin", label: "Human reply" },
                          { value: "llm_bot", label: "AI reply" },
                        ]}
                        variant="compact"
                      />
                      <span className="muted-copy small-copy">
                        Sending as {replySenderType === "human_admin" ? currentUser?.full_name || currentUser?.email : "AI Assistant"}
                      </span>
                      <button
                        type="button"
                        className="secondary-action"
                        onClick={handleGenerateReply}
                        disabled={generatingReply || sending}
                      >
                        {generatingReply ? "Generating..." : "Generate AI reply"}
                      </button>
                    </div>
                    <CustomTextArea
                      value={reply}
                      onChange={(event) => setReply(event.target.value)}
                      rows={5}
                      placeholder="Write a reply..."
                    />
                    <div className="reply-actions">
                      <span className="muted-copy small-copy">{reply.trim().length}/5000</span>
                      <button type="submit" disabled={sending || !reply.trim()}>
                        {sending ? "Sending..." : "Send reply"}
                      </button>
                    </div>
                  </form>
                </div>

                <aside className="panel inbox-customer-panel">
                  <h3>Customer</h3>
                  <dl className="detail-list">
                    <div>
                      <dt>Name</dt>
                      <dd>{selectedConversation.customer_name || "Unknown"}</dd>
                    </div>
                    <div>
                      <dt>External ID</dt>
                      <dd>{selectedConversation.customer_external_id}</dd>
                    </div>
                    <div>
                      <dt>Email</dt>
                      <dd>{selectedConversation.customer_email || "Not available"}</dd>
                    </div>
                    <div>
                      <dt>Phone</dt>
                      <dd>{selectedConversation.customer_phone || "Not available"}</dd>
                    </div>
                    <div>
                      <dt>Assigned to</dt>
                      <dd>{selectedConversation.assigned_to?.full_name || selectedConversation.assigned_to?.email || "Unassigned"}</dd>
                    </div>
                  </dl>

                  <form className="form-panel compact-form-panel" onSubmit={handleAssign}>
                    <label>
                      Assign conversation
                      <CustomSelect
                        value={assigneeUserId}
                        onChange={setAssigneeUserId}
                        disabled={updatingMeta}
                        options={[
                          { value: "unassigned", label: "Unassigned" },
                          ...teamMembers.map((member) => ({
                            value: String(member.user_id),
                            label: `${member.full_name || member.email} (${member.role})`,
                          })),
                        ]}
                        variant="compact"
                      />
                    </label>
                    <button type="submit" disabled={updatingMeta}>
                      {updatingMeta ? "Updating..." : "Save assignment"}
                    </button>
                  </form>
                </aside>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
