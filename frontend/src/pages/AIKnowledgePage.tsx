import { FormEvent, useEffect, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createKnowledgeSource, listAIAgents, listKnowledgeSources } from "../features/ai/api/aiApi";
import type { AIAgentOverview, KnowledgeSourceStatus, KnowledgeSourceType } from "../shared/types/ai";
import type { AIKnowledgeSource } from "../shared/types/ai";

export function AIKnowledgePage() {
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [sources, setSources] = useState<AIKnowledgeSource[]>([]);
  const [agentId, setAgentId] = useState("");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<KnowledgeSourceType>("text");
  const [status, setStatus] = useState<KnowledgeSourceStatus>("draft");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [metadata, setMetadata] = useState('{ "category": "general" }');
  const [fileName, setFileName] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    const [agentResponse, sourceResponse] = await Promise.all([
      listAIAgents(),
      listKnowledgeSources(agentId ? { ai_agent_id: Number(agentId) } : {}),
    ]);
    setAgents(agentResponse);
    setSources(sourceResponse);
  };

  useEffect(() => {
    loadData();
  }, [agentId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await createKnowledgeSource({
      ai_agent_id: agentId ? Number(agentId) : null,
      title,
      source_type: sourceType,
      status,
      description: description || undefined,
      content_text: content || undefined,
      file_metadata: fileName ? { file_name: fileName } : undefined,
      metadata_json: JSON.parse(metadata),
    });
    setMessage("Knowledge source created.");
    setTitle("");
    setDescription("");
    setContent("");
    setFileName("");
    await loadData();
  };

  return (
    <section>
      <PageHeader
        eyebrow="Knowledge"
        title="Knowledge sources"
        description="Capture file metadata, URLs, or text records now so retrieval and RAG pipelines can be added on top later."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}

      <div className="connections-page-stack">
        <form className="panel form-panel connection-form ai-knowledge-form" onSubmit={handleSubmit}>
          <h3 className="ai-knowledge-form-title">Add knowledge source</h3>
          <label>
            Agent
            <CustomSelect
              value={agentId}
              onChange={setAgentId}
              options={[
                { value: "", label: "Account-level" },
                ...agents.map((agent) => ({ value: String(agent.id), label: agent.name })),
              ]}
            />
          </label>
          <label>
            Title
            <CustomField value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label>
            Source type
            <CustomSelect
              value={sourceType}
              onChange={(value) => setSourceType(value as KnowledgeSourceType)}
              options={[
                { value: "text", label: "Text" },
                { value: "url", label: "URL" },
                { value: "file", label: "File" },
              ]}
            />
          </label>
          <label>
            Status
            <CustomSelect
              value={status}
              onChange={(value) => setStatus(value as KnowledgeSourceStatus)}
              options={[
                { value: "draft", label: "Draft" },
                { value: "ready", label: "Ready" },
                { value: "processing", label: "Processing" },
                { value: "archived", label: "Archived" },
              ]}
            />
          </label>
          <label>
            Description
            <CustomField value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label>
            File name
            <CustomField value={fileName} onChange={(event) => setFileName(event.target.value)} />
          </label>
          <label>
            Content text
            <CustomTextArea value={content} rows={8} onChange={(event) => setContent(event.target.value)} />
          </label>
          <label>
            Metadata JSON
            <CustomTextArea value={metadata} rows={8} onChange={(event) => setMetadata(event.target.value)} />
          </label>
          <button type="submit" className="ai-knowledge-create-button">Create source</button>
        </form>

        <div className="table-card">
          <div className="table-card-header">
            <h3>Sources</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Status</th>
                <th>Agent</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.id}>
                  <td>
                    <strong>{source.title}</strong>
                    <div className="muted-copy small-copy">{source.file_name || source.description || "No extra metadata"}</div>
                  </td>
                  <td>{source.source_type}</td>
                  <td>{source.status}</td>
                  <td>{agents.find((agent) => agent.id === source.ai_agent_id)?.name || "Account-level"}</td>
                </tr>
              ))}
              {sources.length === 0 ? (
                <tr>
                  <td colSpan={4}>No knowledge sources yet.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
