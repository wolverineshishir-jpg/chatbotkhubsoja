import { FormEvent, useEffect, useMemo, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { LoadingPanel } from "../components/common/LoadingPanel";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { listTeamMembers } from "../features/accounts/api/accountApi";
import { generateCommentReply } from "../features/ai/api/aiApi";
import { createCommentReply, getComment, listComments, updateCommentStatus } from "../features/comments/api/commentsApi";
import { useAuthStore } from "../features/auth/store/authStore";
import type { TeamMember } from "../shared/types/account";
import type {
  CommentReplyStatus,
  CommentStatus,
  FacebookCommentDetail,
  FacebookCommentReply,
  FacebookCommentSummary,
} from "../shared/types/comments";

const STATUS_OPTIONS: Array<{ value: CommentStatus; label: string }> = [
  { value: "pending", label: "Pending" },
  { value: "replied", label: "Replied" },
  { value: "ignored", label: "Ignored" },
  { value: "flagged", label: "Flagged" },
  { value: "need_review", label: "Needs review" },
];

const REPLY_STATUS_LABELS: Record<CommentReplyStatus, string> = {
  draft: "Draft",
  queued: "Queued",
  sent: "Sent",
  failed: "Failed",
};

export function CommentsModerationPage() {
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const currentUser = useAuthStore((state) => state.user);

  const [comments, setComments] = useState<FacebookCommentSummary[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [selectedCommentId, setSelectedCommentId] = useState<number | null>(null);
  const [detail, setDetail] = useState<FacebookCommentDetail | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [savingStatus, setSavingStatus] = useState(false);
  const [savingReply, setSavingReply] = useState(false);
  const [generatingReply, setGeneratingReply] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ status: "" as CommentStatus | "", search: "" });
  const [replyText, setReplyText] = useState("");
  const [replyMode, setReplyMode] = useState<"human_admin" | "llm_bot">("human_admin");
  const [moderationNotes, setModerationNotes] = useState("");
  const [flaggedReason, setFlaggedReason] = useState("");
  const [assigneeUserId, setAssigneeUserId] = useState("unassigned");

  const selectedComment = useMemo(
    () => comments.find((comment) => comment.id === selectedCommentId) ?? detail,
    [comments, detail, selectedCommentId],
  );

  const loadComments = async (preferredId?: number | null) => {
    setLoadingList(true);
    try {
      const response = await listComments({
        status: filters.status,
        search: filters.search || undefined,
      });
      setComments(response.items);
      setError(null);

      const nextId = preferredId ?? selectedCommentId;
      if (nextId && response.items.some((item) => item.id === nextId)) {
        setSelectedCommentId(nextId);
      } else {
        setSelectedCommentId(response.items[0]?.id ?? null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load comments.");
      setComments([]);
      setSelectedCommentId(null);
    } finally {
      setLoadingList(false);
    }
  };

  const loadDetail = async (commentId: number) => {
    setLoadingDetail(true);
    try {
      const response = await getComment(commentId);
      setDetail(response);
      setModerationNotes(response.moderation_notes || "");
      setFlaggedReason(response.flagged_reason || "");
      setAssigneeUserId(response.assigned_to?.user_id ? String(response.assigned_to.user_id) : "unassigned");
      if (response.ai_draft_reply && !replyText) {
        setReplyText(response.ai_draft_reply);
        setReplyMode("llm_bot");
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load comment.");
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    loadComments(null);
    listTeamMembers().then(setTeamMembers).catch(() => setTeamMembers([]));
  }, [activeAccountId, filters.status]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      loadComments(selectedCommentId);
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [filters.search]);

  useEffect(() => {
    if (selectedCommentId) {
      loadDetail(selectedCommentId);
    } else {
      setDetail(null);
      setReplyText("");
    }
  }, [selectedCommentId]);

  const applyCommentUpdate = (updated: FacebookCommentSummary) => {
    setComments((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    setDetail((current) => (current && current.id === updated.id ? { ...current, ...updated } : current));
  };

  const handleStatusAction = async (status: CommentStatus) => {
    if (!selectedCommentId || !selectedComment) return;
    setSavingStatus(true);
    try {
      const updated = await updateCommentStatus(selectedCommentId, {
        status,
        assignee_user_id: selectedComment.assigned_to?.user_id ?? undefined,
        flagged_reason: flaggedReason || undefined,
        moderation_notes: moderationNotes || undefined,
      });
      applyCommentUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to update comment.");
    } finally {
      setSavingStatus(false);
    }
  };

  const handleAssigneeSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedCommentId || !selectedComment) return;
    setSavingStatus(true);
    try {
      const updated = await updateCommentStatus(selectedCommentId, {
        status: selectedComment.status,
        assignee_user_id: assigneeUserId !== "unassigned" ? Number(assigneeUserId) : null,
        flagged_reason: flaggedReason || undefined,
        moderation_notes: moderationNotes || undefined,
      });
      applyCommentUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to save assignee.");
    } finally {
      setSavingStatus(false);
    }
  };

  const handleReply = async (sendNow: boolean) => {
    if (!selectedCommentId || !replyText.trim()) return;
    setSavingReply(true);
    try {
      const reply = await createCommentReply(selectedCommentId, {
        content: replyText.trim(),
        sender_type: replyMode,
        send_now: sendNow,
        metadata_json: {
          source: sendNow ? "manual_moderation" : "draft_moderation",
        },
      });
      setDetail((current) =>
        current && current.id === selectedCommentId
          ? {
              ...current,
              ai_draft_reply: !sendNow && replyMode === "llm_bot" ? reply.content : current.ai_draft_reply,
              replies: [...current.replies, reply],
            }
          : current,
      );
      if (sendNow) {
        setReplyText("");
      }
      await loadComments(selectedCommentId);
      await loadDetail(selectedCommentId);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to create reply.");
    } finally {
      setSavingReply(false);
    }
  };

  const handleGenerateReply = async () => {
    if (!selectedCommentId) return;
    setGeneratingReply(true);
    try {
      const result = await generateCommentReply({
        comment_id: selectedCommentId,
        persist_draft: false,
      });
      setReplyText(result.content);
      setReplyMode("llm_bot");
      if (result.requires_approval) {
        setError("AI draft generated and requires review before sending.");
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
        eyebrow="Comments"
        title="Facebook comment moderation"
        description="Moderate Facebook post comments with account-scoped review queues, assignment, stored AI drafts, manual replies, and reply history."
      />

      {error ? <div className="panel error-panel">{error}</div> : null}

      <div className="comments-page">
        <aside className="comments-sidebar">
          <div className="panel comments-toolbar">
            <label>
              Status
              <CustomSelect
                value={filters.status}
                onChange={(value) => setFilters((current) => ({ ...current, status: value as CommentStatus | "" }))}
                options={[{ value: "", label: "All statuses" }, ...STATUS_OPTIONS]}
              />
            </label>
            <label>
              Search
              <CustomField
                type="search"
                value={filters.search}
                onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
                placeholder="Comment text, post, or customer"
              />
            </label>
          </div>

          <div className="table-card comments-list">
            <div className="table-card-header">
              <h3>Queue</h3>
              <span className="muted-copy small-copy">{comments.length} loaded</span>
            </div>
            {loadingList ? <LoadingPanel message="Loading comments..." hint="Collecting moderation queue data." compact /> : null}
            {!loadingList && comments.length === 0 ? <div className="panel">No comments match the current filter.</div> : null}
            <div className="comment-list">
              {comments.map((comment) => (
                <button
                  key={comment.id}
                  type="button"
                  className={`comment-row ${selectedCommentId === comment.id ? "active" : ""}`}
                  onClick={() => setSelectedCommentId(comment.id)}
                >
                  <div className="comment-row-top">
                    <strong>{comment.commenter_name || comment.commenter_external_id}</strong>
                    <span className={`status-pill comment-status-${comment.status}`}>{comment.status.replace("_", " ")}</span>
                  </div>
                  <div className="muted-copy small-copy">
                    {comment.post_title || comment.post_external_id}
                    {" | "}
                    {comment.assigned_to?.full_name || comment.assigned_to?.email || "Unassigned"}
                  </div>
                  <p>{comment.comment_text}</p>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <div className="comments-main">
          {!selectedComment ? (
            <div className="panel inbox-empty">Select a comment to review details and reply history.</div>
          ) : (
            <>
              <div className="panel comments-header">
                <div>
                  <h3>{selectedComment.commenter_name || selectedComment.commenter_external_id}</h3>
                  <p className="muted-copy">
                    {selectedComment.post_title || selectedComment.post_external_id}
                    {" | "}
                    {selectedComment.commented_at ? new Date(selectedComment.commented_at).toLocaleString() : "No timestamp"}
                  </p>
                </div>
                <div className="comments-status-actions">
                  {STATUS_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={`ghost-button compact-button ${selectedComment.status === option.value ? "status-active" : ""}`}
                      onClick={() => handleStatusAction(option.value)}
                      disabled={savingStatus}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="comments-layout">
                <div className="table-card comments-thread-card">
                  <div className="thread-scroll">
                    {loadingDetail ? (
                      <LoadingPanel message="Loading comment details..." hint="Syncing comment thread and reply history." compact />
                    ) : null}
                    {!loadingDetail && (
                      <>
                        <article className="comment-original-card">
                          <div className="message-meta">
                            <strong>Original comment</strong>
                            <span>{selectedComment.external_comment_id}</span>
                          </div>
                          <p>{selectedComment.comment_text}</p>
                        </article>

                        {detail?.replies.map((reply: FacebookCommentReply) => (
                          <article key={reply.id} className={`message-bubble ${reply.sender_type === "human_admin" ? "outbound" : "inbound"}`}>
                            <div className="message-meta">
                              <strong>{reply.sender_type === "human_admin" ? currentUser?.full_name || "Admin" : "AI draft"}</strong>
                              <span>{new Date(reply.created_at).toLocaleString()}</span>
                            </div>
                            <p>{reply.content}</p>
                            <span className={`message-delivery delivery-${reply.reply_status}`}>
                              {REPLY_STATUS_LABELS[reply.reply_status]}
                            </span>
                          </article>
                        ))}
                      </>
                    )}
                  </div>

                  <div className="reply-box">
                    <div className="reply-toolbar">
                      <CustomSelect
                        value={replyMode}
                        onChange={(value) => setReplyMode(value as "human_admin" | "llm_bot")}
                        options={[
                          { value: "human_admin", label: "Human reply" },
                          { value: "llm_bot", label: "AI draft" },
                        ]}
                        variant="compact"
                      />
                      <span className="muted-copy small-copy">
                        {replyMode === "human_admin" ? "Manual moderator reply" : "Store or send AI-generated draft"}
                      </span>
                      <button
                        type="button"
                        className="secondary-action"
                        onClick={handleGenerateReply}
                        disabled={generatingReply || savingReply}
                      >
                        {generatingReply ? "Generating..." : "Generate AI reply"}
                      </button>
                    </div>
                    <CustomTextArea
                      value={replyText}
                      onChange={(event) => setReplyText(event.target.value)}
                      rows={6}
                      placeholder="Draft a reply..."
                    />
                    <div className="reply-actions">
                      <button type="button" className="secondary-action" onClick={() => handleReply(false)} disabled={savingReply || !replyText.trim()}>
                        {savingReply ? "Saving..." : "Save draft"}
                      </button>
                      <button type="button" onClick={() => handleReply(true)} disabled={savingReply || !replyText.trim()}>
                        {savingReply ? "Sending..." : "Send reply"}
                      </button>
                    </div>
                  </div>
                </div>

                <aside className="panel comments-side-panel">
                  <h3>Moderation</h3>
                  <dl className="detail-list">
                    <div>
                      <dt>Assigned to</dt>
                      <dd>{selectedComment.assigned_to?.full_name || selectedComment.assigned_to?.email || "Unassigned"}</dd>
                    </div>
                    <div>
                      <dt>Post</dt>
                      <dd>{selectedComment.post_title || selectedComment.post_external_id}</dd>
                    </div>
                    <div>
                      <dt>Flag reason</dt>
                      <dd>{selectedComment.flagged_reason || "None"}</dd>
                    </div>
                    <div>
                      <dt>AI draft</dt>
                      <dd>{selectedComment.ai_draft_reply || "No saved draft"}</dd>
                    </div>
                  </dl>

                  <form className="form-panel compact-form-panel" onSubmit={handleAssigneeSave}>
                    <label>
                      Assign moderator
                      <CustomSelect
                        value={assigneeUserId}
                        onChange={setAssigneeUserId}
                        disabled={savingStatus}
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
                    <label>
                      Flagged reason
                      <CustomField value={flaggedReason} onChange={(event) => setFlaggedReason(event.target.value)} />
                    </label>
                    <label>
                      Moderation notes
                      <CustomTextArea value={moderationNotes} rows={5} onChange={(event) => setModerationNotes(event.target.value)} />
                    </label>
                    <button type="submit" disabled={savingStatus}>
                      {savingStatus ? "Saving..." : "Save moderation"}
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
