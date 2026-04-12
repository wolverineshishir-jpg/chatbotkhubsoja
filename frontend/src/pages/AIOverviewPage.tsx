import { useEffect, useMemo, useState } from "react";

import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { listAIAgents, resolvePrompts } from "../features/ai/api/aiApi";
import type { AIAgentOverview, PromptResolution } from "../shared/types/ai";

export function AIOverviewPage() {
  const [agents, setAgents] = useState<AIAgentOverview[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | "">("");
  const [resolvedPrompts, setResolvedPrompts] = useState<PromptResolution[]>([]);

  useEffect(() => {
    listAIAgents().then((response) => {
      setAgents(response);
      if (response[0]) {
        setSelectedAgentId(response[0].id);
      }
    });
  }, []);

  useEffect(() => {
    resolvePrompts(selectedAgentId ? { ai_agent_id: selectedAgentId } : {}).then(setResolvedPrompts);
  }, [selectedAgentId]);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? null,
    [agents, selectedAgentId],
  );

  return (
    <section>
      <PageHeader
        eyebrow="AI"
        title="Agent overview"
        description="Review the current AI layer for the active account, including effective prompts after hierarchy resolution."
      />

      <div className="dashboard-grid wizard-layout">
        <div className="panel">
          <h3>Overview</h3>
          <label>
            Agent
            <CustomSelect
              value={selectedAgentId ? String(selectedAgentId) : ""}
              onChange={(value) => setSelectedAgentId(value ? Number(value) : "")}
              options={[
                { value: "", label: "Account defaults" },
                ...agents.map((agent) => ({ value: String(agent.id), label: agent.name })),
              ]}
            />
          </label>
          <div className="wizard-steps">
            <div className="wizard-step">
              <strong>Selected layer</strong>
              <span>{selectedAgent?.name || "Account default"}</span>
            </div>
            <div className="wizard-step">
              <strong>Business type</strong>
              <span>{selectedAgent?.business_type || "General"}</span>
            </div>
            <div className="wizard-step">
              <strong>Status</strong>
              <span>{selectedAgent?.status || "n/a"}</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Resolved prompts</h3>
          <div className="wizard-steps">
            {resolvedPrompts.map((item) => (
              <div key={item.prompt_type} className="wizard-step">
                <strong>{item.prompt_type}</strong>
                <span>{item.prompt ? item.source_scope : "No active prompt"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
