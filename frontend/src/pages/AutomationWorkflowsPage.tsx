import { FormEvent, useEffect, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { LoadingPanel } from "../components/common/LoadingPanel";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createAutomationWorkflow, deleteAutomationWorkflow, listAutomationWorkflows, runAutomationWorkflow, updateAutomationWorkflow } from "../features/automation/api/automationApi";
import { listAIAgents } from "../features/ai/api/aiApi";
import { listPlatformConnections } from "../features/platformConnections/api/platformConnectionApi";
import type { AIAgentOverview } from "../shared/types/ai";
import type { AutomationActionType, AutomationTriggerType, AutomationWorkflow, AutomationWorkflowStatus } from "../shared/types/automation";
import type { PlatformConnection } from "../shared/types/platformConnection";

const ACTION_BY_TRIGGER: Record<AutomationTriggerType, AutomationActionType> = {
  inbox_message_received: "generate_inbox_reply",
  facebook_comment_created: "generate_comment_reply",
  scheduled_daily: "generate_post_draft",
};

const TRIGGER_LABELS: Record<AutomationTriggerType, string> = {
  inbox_message_received: "Inbox message received",
  facebook_comment_created: "Facebook comment created",
  scheduled_daily: "Scheduled daily",
};

const ACTION_LABELS: Record<AutomationActionType, string> = {
  generate_inbox_reply: "Generate inbox reply",
  generate_comment_reply: "Generate comment reply",
  generate_post_draft: "Generate post draft",
};

const defaultForm = {
  name: "",
  description: "",
  status: "draft" as AutomationWorkflowStatus,
  trigger_type: "inbox_message_received" as AutomationTriggerType,
  action_type: "generate_inbox_reply" as AutomationActionType,
  platform_connection_id: "",
  ai_agent_id: "",
  delay_seconds: "0",
  include_keywords: "",
  exclude_keywords: "",
  customer_contains: "",
  instructions: "",
  send_now: false,
  title_hint: "",
  schedule_timezone: "UTC",
  schedule_local_time: "09:00",
};

export function AutomationWorkflowsPage() {
  const [workflows, setWorkflows] = useState<AutomationWorkflow[]>([]);
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [selected, setSelected] = useState<AutomationWorkflow | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [workingWorkflowId, setWorkingWorkflowId] = useState<number | null>(null);

  const loadData = async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true);
    }
    const [workflowResponse, connectionResponse, agentResponse] = await Promise.all([
      listAutomationWorkflows(),
      listPlatformConnections(),
      listAIAgents(),
    ]);
    setWorkflows(workflowResponse.items);
    setConnections(connectionResponse.items);
    setAgents(agentResponse);
    setLoading(false);
  };

  useEffect(() => {
    loadData()
      .then(() => setError(null))
      .catch(() => {
        setError("Unable to load automation workflows.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selected) {
      setForm(defaultForm);
      return;
    }
    setForm({
      name: selected.name,
      description: selected.description ?? "",
      status: selected.status,
      trigger_type: selected.trigger_type,
      action_type: selected.action_type,
      platform_connection_id: selected.platform_connection_id ? String(selected.platform_connection_id) : "",
      ai_agent_id: selected.ai_agent_id ? String(selected.ai_agent_id) : "",
      delay_seconds: String(selected.delay_seconds),
      include_keywords: selected.trigger_filters_json.include_keywords.join(", "),
      exclude_keywords: selected.trigger_filters_json.exclude_keywords.join(", "),
      customer_contains: selected.trigger_filters_json.customer_contains ?? "",
      instructions: selected.action_config_json.instructions ?? "",
      send_now: selected.action_config_json.send_now,
      title_hint: selected.action_config_json.title_hint ?? "",
      schedule_timezone: selected.schedule_timezone ?? "UTC",
      schedule_local_time: selected.schedule_local_time ?? "09:00",
    });
  }, [selected]);

  useEffect(() => {
    const expectedAction = ACTION_BY_TRIGGER[form.trigger_type];
    if (form.action_type === expectedAction) {
      return;
    }
    setForm((current) => ({ ...current, action_type: expectedAction }));
  }, [form.trigger_type]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        status: form.status,
        trigger_type: form.trigger_type,
        action_type: form.action_type,
        platform_connection_id: form.platform_connection_id ? Number(form.platform_connection_id) : null,
        ai_agent_id: form.ai_agent_id ? Number(form.ai_agent_id) : null,
        delay_seconds: Number(form.delay_seconds || "0"),
        trigger_filters: {
          include_keywords: form.include_keywords.split(",").map((item) => item.trim()).filter(Boolean),
          exclude_keywords: form.exclude_keywords.split(",").map((item) => item.trim()).filter(Boolean),
          customer_contains: form.customer_contains || null,
        },
        action_config: {
          instructions: form.instructions || null,
          send_now: form.send_now,
          title_hint: form.title_hint || null,
        },
        schedule_timezone: form.trigger_type === "scheduled_daily" ? form.schedule_timezone : null,
        schedule_local_time: form.trigger_type === "scheduled_daily" ? form.schedule_local_time : null,
      };
      if (selected) {
        await updateAutomationWorkflow(selected.id, payload);
        setMessage("Automation workflow updated.");
      } else {
        await createAutomationWorkflow(payload);
        setMessage("Automation workflow created.");
      }
      setSelected(null);
      await loadData({ silent: true });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? "Unable to save automation workflow.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRun = async (workflowId: number) => {
    setWorkingWorkflowId(workflowId);
    setError(null);
    setMessage(null);
    try {
      const response = await runAutomationWorkflow(workflowId);
      setMessage(`Queued workflow run as sync job #${response.sync_job_id}.`);
      await loadData({ silent: true });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to run workflow.");
    } finally {
      setWorkingWorkflowId(null);
    }
  };

  const handleDelete = async (workflowId: number) => {
    setWorkingWorkflowId(workflowId);
    setError(null);
    setMessage(null);
    try {
      await deleteAutomationWorkflow(workflowId);
      if (selected?.id === workflowId) {
        setSelected(null);
      }
      setMessage("Automation workflow deleted.");
      await loadData({ silent: true });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to delete workflow.");
    } finally {
      setWorkingWorkflowId(null);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="Automation"
        title="Workflow builder"
        description="Create account-scoped automation rules for inbound inbox messages, Facebook comments, and scheduled daily post drafting."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}
      {loading ? <LoadingPanel message="Loading automation workflows..." hint="Syncing workflow rules, channels, and AI agents." /> : null}

      <div className="connections-page-stack">
        <form className="panel form-panel connection-form automation-workflow-form" onSubmit={handleSubmit}>
          <h3 className="automation-form-title">{selected ? "Edit workflow" : "Create workflow"}</h3>
          <label>
            Name
            <CustomField value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
          </label>
          <label>
            Description
            <CustomField value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
          </label>
          <label>
            Status
            <CustomSelect
              value={form.status}
              onChange={(value) => setForm((current) => ({ ...current, status: value as AutomationWorkflowStatus }))}
              options={[
                { value: "draft", label: "Draft" },
                { value: "active", label: "Active" },
                { value: "paused", label: "Paused" },
                { value: "archived", label: "Archived" },
              ]}
            />
          </label>
          <label>
            Trigger
            <CustomSelect
              value={form.trigger_type}
              onChange={(value) => setForm((current) => ({ ...current, trigger_type: value as AutomationTriggerType }))}
              options={[
                { value: "inbox_message_received", label: "Inbox message received" },
                { value: "facebook_comment_created", label: "Facebook comment created" },
                { value: "scheduled_daily", label: "Scheduled daily" },
              ]}
            />
          </label>
          <label>
            Action
            <CustomSelect
              value={form.action_type}
              onChange={() => undefined}
              disabled
              options={[
                { value: "generate_inbox_reply", label: "Generate inbox reply" },
                { value: "generate_comment_reply", label: "Generate comment reply" },
                { value: "generate_post_draft", label: "Generate post draft" },
              ]}
            />
          </label>
          <label className="automation-connection-field">
            Connected channel
            <CustomSelect
              value={form.platform_connection_id}
              onChange={(value) => setForm((current) => ({ ...current, platform_connection_id: value }))}
              options={[
                { value: "", label: "Account-level default" },
                ...connections.map((connection) => ({ value: String(connection.id), label: connection.name })),
              ]}
            />
          </label>
          <label>
            AI agent
            <CustomSelect
              value={form.ai_agent_id}
              onChange={(value) => setForm((current) => ({ ...current, ai_agent_id: value }))}
              options={[
                { value: "", label: "Automatic agent resolution" },
                ...agents.map((agent) => ({ value: String(agent.id), label: agent.name })),
              ]}
            />
          </label>
          <label>
            Delay seconds
            <CustomField type="number" min="0" value={form.delay_seconds} onChange={(event) => setForm((current) => ({ ...current, delay_seconds: event.target.value }))} />
          </label>
          <label>
            Include keywords
            <CustomField value={form.include_keywords} onChange={(event) => setForm((current) => ({ ...current, include_keywords: event.target.value }))} placeholder="price, plan, delivery" />
          </label>
          <label>
            Exclude keywords
            <CustomField value={form.exclude_keywords} onChange={(event) => setForm((current) => ({ ...current, exclude_keywords: event.target.value }))} placeholder="refund, spam" />
          </label>
          <label>
            Customer contains
            <CustomField value={form.customer_contains} onChange={(event) => setForm((current) => ({ ...current, customer_contains: event.target.value }))} />
          </label>
          {form.trigger_type === "scheduled_daily" ? null : (
            <label className="automation-send-now-toggle">
              <input type="checkbox" checked={form.send_now} onChange={(event) => setForm((current) => ({ ...current, send_now: event.target.checked }))} />
              Send generated reply immediately
            </label>
          )}
          <label className="field-full">
            Instructions
            <CustomTextArea value={form.instructions} rows={5} onChange={(event) => setForm((current) => ({ ...current, instructions: event.target.value }))} />
          </label>
          {form.trigger_type === "scheduled_daily" ? (
            <>
              <label>
                Title hint
                <CustomField value={form.title_hint} onChange={(event) => setForm((current) => ({ ...current, title_hint: event.target.value }))} />
              </label>
              <label>
                Schedule timezone
                <CustomField value={form.schedule_timezone} onChange={(event) => setForm((current) => ({ ...current, schedule_timezone: event.target.value }))} />
              </label>
              <label>
                Schedule local time
                <CustomField value={form.schedule_local_time} onChange={(event) => setForm((current) => ({ ...current, schedule_local_time: event.target.value }))} placeholder="09:00" />
              </label>
            </>
          ) : null}
          <button type="submit" className="automation-create-workflow-button" disabled={submitting}>{submitting ? "Saving..." : selected ? "Save workflow" : "Create workflow"}</button>
        </form>

        <div className="table-card automation-workflows-card">
          <div className="table-card-header">
            <h3>Workflows</h3>
            <button type="button" className="ghost-button compact-button new-workflow-button" onClick={() => setSelected(null)} disabled={submitting}>
              New workflow
            </button>
          </div>
          <div className="connections-table-scroll">
            <table className="connections-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Trigger</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Next run</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {workflows.map((workflow) => {
                  const isBusy = workingWorkflowId === workflow.id;
                  return (
                    <tr key={workflow.id}>
                      <td>
                        <strong>{workflow.name}</strong>
                        <div className="muted-copy small-copy">{workflow.description || "No description"}</div>
                      </td>
                      <td>{TRIGGER_LABELS[workflow.trigger_type]}</td>
                      <td>{ACTION_LABELS[workflow.action_type]}</td>
                      <td><span className={`status-pill status-${workflow.status}`}>{workflow.status}</span></td>
                      <td>{workflow.next_run_at ? new Date(workflow.next_run_at).toLocaleString() : "Event-driven"}</td>
                      <td className="table-actions">
                        <button type="button" className="link-button" onClick={() => setSelected(workflow)} disabled={isBusy || submitting}>Edit</button>
                        <button type="button" className="link-button" onClick={() => void handleRun(workflow.id)} disabled={isBusy || submitting}>
                          {isBusy ? "Working..." : "Run now"}
                        </button>
                        <button type="button" className="link-button danger-link" onClick={() => void handleDelete(workflow.id)} disabled={isBusy || submitting}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {workflows.length === 0 ? (
                  <tr>
                    <td colSpan={6}>No automation workflows yet.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
