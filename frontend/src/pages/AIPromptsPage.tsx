import { FormEvent, useEffect, useMemo, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createAIPrompt, listAIAgents, listAIPrompts, resolvePrompts } from "../features/ai/api/aiApi";
import { listPlatformConnections } from "../features/platformConnections/api/platformConnectionApi";
import type { AIAgentOverview, AIPrompt, PromptResolution, PromptType } from "../shared/types/ai";
import type { PlatformConnection } from "../shared/types/platformConnection";

const promptTypes: Array<{ value: PromptType; label: string }> = [
  { value: "system_instruction", label: "System instruction" },
  { value: "inbox_reply", label: "Inbox reply" },
  { value: "comment_reply", label: "Comment reply" },
  { value: "post_generation", label: "Post generation" },
];

export function AIPromptsPage() {
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [resolved, setResolved] = useState<PromptResolution[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedConnectionId, setSelectedConnectionId] = useState("");
  const [selectedType, setSelectedType] = useState<PromptType>("system_instruction");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    const [agentResponse, connectionResponse] = await Promise.all([listAIAgents(), listPlatformConnections()]);
    setAgents(agentResponse);
    setConnections(connectionResponse.items);
  };

  useEffect(() => {
    loadData().catch(() => setError("Unable to load prompt dependencies."));
  }, []);

  useEffect(() => {
    const params = {
      ai_agent_id: selectedAgentId ? Number(selectedAgentId) : undefined,
      platform_connection_id: selectedConnectionId ? Number(selectedConnectionId) : undefined,
    };
    listAIPrompts(params).then(setPrompts);
    resolvePrompts(params).then(setResolved);
  }, [selectedAgentId, selectedConnectionId]);

  const filteredPrompts = useMemo(
    () => prompts.filter((prompt) => prompt.prompt_type === selectedType),
    [prompts, selectedType],
  );

  const resolvedPrompt = resolved.find((item) => item.prompt_type === selectedType)?.prompt;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const created = await createAIPrompt({
        title,
        content,
        notes: notes || undefined,
        prompt_type: selectedType,
        ai_agent_id: selectedAgentId ? Number(selectedAgentId) : null,
        platform_connection_id: selectedConnectionId ? Number(selectedConnectionId) : null,
        is_active: true,
      });
      setMessage(`Saved prompt version ${created.version}.`);
      setTitle("");
      setContent("");
      setNotes("");
      const params = {
        ai_agent_id: selectedAgentId ? Number(selectedAgentId) : undefined,
        platform_connection_id: selectedConnectionId ? Number(selectedConnectionId) : undefined,
      };
      setPrompts(await listAIPrompts(params));
      setResolved(await resolvePrompts(params));
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to save prompt.");
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="Prompts"
        title="Prompt management"
        description="Manage versioned prompts for system behavior, inbox replies, comment replies, and post generation with account, connection, and agent scopes."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      <div className="dashboard-grid connections-layout ai-prompts-layout">
        <div className="panel form-panel ai-prompts-scope-panel">
          <h3>Scope</h3>
          <label>
            Agent
            <CustomSelect
              value={selectedAgentId}
              onChange={setSelectedAgentId}
              options={[
                { value: "", label: "No agent" },
                ...agents.map((agent) => ({ value: String(agent.id), label: agent.name })),
              ]}
            />
          </label>
          <label>
            Connection
            <CustomSelect
              value={selectedConnectionId}
              onChange={setSelectedConnectionId}
              options={[
                { value: "", label: "No connection" },
                ...connections.map((connection) => ({ value: String(connection.id), label: connection.name })),
              ]}
            />
          </label>
          <label>
            Prompt type
            <CustomSelect
              value={selectedType}
              onChange={(value) => setSelectedType(value as PromptType)}
              options={promptTypes}
            />
          </label>
          <div className="panel subtle-panel">
            <strong>Active resolution</strong>
            <p className="muted-copy">
              {resolvedPrompt ? `${resolvedPrompt.title} (v${resolvedPrompt.version})` : "No active prompt resolved yet."}
            </p>
          </div>
          <div className="table-card">
            <div className="connections-table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Title</th>
                    <th>Active</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPrompts.map((prompt) => (
                    <tr key={prompt.id}>
                      <td>{prompt.version}</td>
                      <td>{prompt.title}</td>
                      <td>{prompt.is_active ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                  {filteredPrompts.length === 0 ? (
                    <tr>
                      <td colSpan={3}>No prompts for this scope yet.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <form className="panel form-panel ai-prompts-form" onSubmit={handleSubmit}>
          <h3>Create new version</h3>
          <label>
            Title
            <CustomField value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label>
            Prompt content
            <CustomTextArea value={content} rows={12} onChange={(event) => setContent(event.target.value)} required />
          </label>
          <label>
            Notes
            <CustomTextArea value={notes} rows={4} onChange={(event) => setNotes(event.target.value)} />
          </label>
          <button type="submit">Save as new active version</button>
        </form>
      </div>
    </section>
  );
}
