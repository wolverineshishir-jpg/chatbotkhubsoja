import { FormEvent, useEffect, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createAIAgent, listAIAgents, updateAIAgent } from "../features/ai/api/aiApi";
import { listPlatformConnections } from "../features/platformConnections/api/platformConnectionApi";
import type { AIAgentOverview, AIAgentStatus } from "../shared/types/ai";
import type { PlatformConnection } from "../shared/types/platformConnection";

export function AIAgentsPage() {
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [selected, setSelected] = useState<AIAgentOverview | null>(null);
  const [form, setForm] = useState({
    name: "",
    business_type: "",
    status: "draft" as AIAgentStatus,
    platform_connection_id: "",
    behavior_json: '{\n  "tone": "helpful"\n}',
    settings_json: '{\n  "reply_length": "balanced"\n}',
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    const [agentResponse, connectionResponse] = await Promise.all([listAIAgents(), listPlatformConnections()]);
    setAgents(agentResponse);
    setConnections(connectionResponse.items);
  };

  useEffect(() => {
    loadData().catch(() => setError("Unable to load AI agents."));
  }, []);

  useEffect(() => {
    if (!selected) {
      setForm({
        name: "",
        business_type: "",
        status: "draft",
        platform_connection_id: "",
        behavior_json: '{\n  "tone": "helpful"\n}',
        settings_json: '{\n  "reply_length": "balanced"\n}',
      });
      return;
    }
    setForm({
      name: selected.name,
      business_type: selected.business_type ?? "",
      status: selected.status,
      platform_connection_id: selected.platform_connection_id ? String(selected.platform_connection_id) : "",
      behavior_json: JSON.stringify(selected.behavior_json, null, 2),
      settings_json: JSON.stringify(selected.settings_json, null, 2),
    });
  }, [selected]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        name: form.name,
        business_type: form.business_type || undefined,
        status: form.status,
        platform_connection_id: form.platform_connection_id ? Number(form.platform_connection_id) : null,
        behavior_json: JSON.parse(form.behavior_json),
        settings_json: JSON.parse(form.settings_json),
      };
      if (selected) {
        await updateAIAgent(selected.id, payload);
        setMessage("AI agent updated.");
      } else {
        await createAIAgent(payload);
        setMessage("AI agent created.");
      }
      setSelected(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? "Unable to save AI agent.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="AI Agents"
        title="Agent settings"
        description="Create and tune account-level or channel-linked AI agents that later power inbox, comments, and content automation."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      <div className="connections-page-stack">
        <form className="panel form-panel connection-form ai-agents-form" onSubmit={handleSubmit}>
          <h3 className="ai-agents-form-title">{selected ? "Edit agent" : "Create AI agent"}</h3>
          <label>
            Name
            <CustomField value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
          </label>
          <label>
            Business type
            <CustomField
              value={form.business_type}
              onChange={(event) => setForm((current) => ({ ...current, business_type: event.target.value }))}
              placeholder="ecommerce, clinic, real-estate, restaurant"
            />
          </label>
          <label>
            Status
            <CustomSelect
              value={form.status}
              onChange={(value) => setForm((current) => ({ ...current, status: value as AIAgentStatus }))}
              options={[
                { value: "draft", label: "Draft" },
                { value: "active", label: "Active" },
                { value: "paused", label: "Paused" },
                { value: "archived", label: "Archived" },
              ]}
            />
          </label>
          <label>
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
          <label className="field-full ai-agents-json-field">
            Behavior JSON
            <CustomTextArea value={form.behavior_json} rows={6} onChange={(event) => setForm((current) => ({ ...current, behavior_json: event.target.value }))} />
          </label>
          <label className="field-full ai-agents-json-field">
            Settings JSON
            <CustomTextArea value={form.settings_json} rows={6} onChange={(event) => setForm((current) => ({ ...current, settings_json: event.target.value }))} />
          </label>
          <button type="submit" className="ai-agents-create-button" disabled={submitting}>{submitting ? "Saving..." : selected ? "Save agent" : "Create agent"}</button>
        </form>

        <div className="table-card">
          <div className="table-card-header">
            <h3>Agents</h3>
            <button type="button" className="ghost-button compact-button" onClick={() => setSelected(null)}>
              New agent
            </button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Business</th>
                <th>Connected channel</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <strong>{agent.name}</strong>
                    <div className="muted-copy small-copy">
                      {agent.prompt_count} prompts · {agent.knowledge_source_count} sources · {agent.faq_count} FAQs
                    </div>
                  </td>
                  <td><span className={`status-pill status-${agent.status}`}>{agent.status}</span></td>
                  <td>{agent.business_type || "General"}</td>
                  <td>{connections.find((item) => item.id === agent.platform_connection_id)?.name || "Account-level"}</td>
                  <td className="table-actions">
                    <button type="button" className="link-button" onClick={() => setSelected(agent)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
              {agents.length === 0 ? (
                <tr>
                  <td colSpan={5}>No AI agents yet.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
