import { FormEvent, useEffect, useState } from "react";

import { CustomField, CustomTextArea } from "../components/common/CustomField";
import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createFAQKnowledge, listAIAgents, listFAQKnowledge } from "../features/ai/api/aiApi";
import type { AIAgentOverview, FAQKnowledge } from "../shared/types/ai";

export function AIFAQPage() {
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [faqs, setFaqs] = useState<FAQKnowledge[]>([]);
  const [agentId, setAgentId] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [tags, setTags] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    const [agentResponse, faqResponse] = await Promise.all([
      listAIAgents(),
      listFAQKnowledge(agentId ? { ai_agent_id: Number(agentId) } : {}),
    ]);
    setAgents(agentResponse);
    setFaqs(faqResponse);
  };

  useEffect(() => {
    loadData();
  }, [agentId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await createFAQKnowledge({
      ai_agent_id: agentId ? Number(agentId) : null,
      question,
      answer,
      tags_json: tags.split(",").map((item) => item.trim()).filter(Boolean),
      is_active: true,
    });
    setMessage("FAQ entry created.");
    setQuestion("");
    setAnswer("");
    setTags("");
    await loadData();
  };

  return (
    <section>
      <PageHeader
        eyebrow="FAQ"
        title="Structured FAQs"
        description="Store high-confidence question and answer pairs separately from long-form knowledge so future AI flows can prefer direct answers."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}

      <div className="connections-page-stack">
        <form className="panel form-panel connection-form ai-faq-form" onSubmit={handleSubmit}>
          <h3 className="ai-faq-form-title">Add FAQ</h3>
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
            Question
            <CustomField value={question} onChange={(event) => setQuestion(event.target.value)} required />
          </label>
          <label className="field-full ai-faq-answer-field">
            Answer
            <CustomTextArea value={answer} rows={8} onChange={(event) => setAnswer(event.target.value)} required />
          </label>
          <label className="field-full">
            Tags
            <CustomField value={tags} onChange={(event) => setTags(event.target.value)} placeholder="shipping, returns, billing" />
          </label>
          <button type="submit" className="ai-faq-create-button">Create FAQ</button>
        </form>

        <div className="table-card">
          <div className="table-card-header">
            <h3>FAQ entries</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Question</th>
                <th>Agent</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {faqs.map((faq) => (
                <tr key={faq.id}>
                  <td>
                    <strong>{faq.question}</strong>
                    <div className="muted-copy small-copy">{faq.answer}</div>
                  </td>
                  <td>{agents.find((agent) => agent.id === faq.ai_agent_id)?.name || "Account-level"}</td>
                  <td>{faq.is_active ? "Yes" : "No"}</td>
                </tr>
              ))}
              {faqs.length === 0 ? (
                <tr>
                  <td colSpan={3}>No FAQ entries yet.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
