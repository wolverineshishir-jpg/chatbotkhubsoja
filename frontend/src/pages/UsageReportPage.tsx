import { useEffect, useState } from "react";

import { LoadingPanel } from "../components/common/LoadingPanel";
import { PageHeader } from "../components/common/PageHeader";
import { listActionUsageLogs, listLlmTokenUsage } from "../features/observability/api/observabilityApi";
import { getTokenUsageSummary } from "../features/reports/api/reportApi";
import type { ActionUsageLog, LLMTokenUsage } from "../shared/types/observability";
import type { TokenUsageSummary } from "../shared/types/reports";

export function UsageReportPage() {
  const [summary, setSummary] = useState<TokenUsageSummary | null>(null);
  const [actionLogs, setActionLogs] = useState<ActionUsageLog[]>([]);
  const [llmUsage, setLlmUsage] = useState<LLMTokenUsage[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [summaryData, actionData, llmData] = await Promise.all([
          getTokenUsageSummary(),
          listActionUsageLogs({ page, page_size: 10 }),
          listLlmTokenUsage({ page, page_size: 10 }),
        ]);
        setSummary(summaryData);
        setActionLogs(actionData.items);
        setLlmUsage(llmData.items);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Unable to load usage report.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [page]);

  return (
    <section>
      <PageHeader
        eyebrow="Usage"
        title="Token usage report"
        description="See what actions consumed tokens, estimated usage cost, and recorded LLM token events for the active account."
      />

      {error ? <div className="panel error-panel">{error}</div> : null}
      {loading ? <LoadingPanel message="Loading usage report..." hint="Analyzing token, action, and LLM usage." /> : null}

      {summary ? (
        <>
          <div className="metric-grid">
            <article className="card metric-card"><p className="metric-label">Tokens consumed</p><strong className="metric-value">{summary.total_tokens_consumed}</strong></article>
            <article className="card metric-card"><p className="metric-label">Estimated cost</p><strong className="metric-value">${summary.total_estimated_cost}</strong></article>
            <article className="card metric-card"><p className="metric-label">Tracked actions</p><strong className="metric-value">{summary.total_action_count}</strong></article>
          </div>

          <div className="dashboard-grid reporting-overview-grid usage-report-stack">
            <section className="panel">
              <h3>Daily token consumption</h3>
              <div className="mini-chart-bars">
                {summary.daily_usage.map((point) => {
                  const max = Math.max(...summary.daily_usage.map((item) => item.tokens_consumed), 1);
                  return (
                    <div className="mini-bar-wrap" key={point.date}>
                      <span className="mini-bar-label">{new Date(point.date).toLocaleDateString(undefined, { weekday: "short" })}</span>
                      <div className="mini-bar-track">
                        <span className="mini-bar-fill" style={{ width: `${(point.tokens_consumed / max) * 100}%` }} />
                      </div>
                      <strong>{point.tokens_consumed}</strong>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="table-card usage-top-actions-card">
              <div className="table-card-header">
                <h3>Top actions</h3>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Quantity</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.top_actions.map((action) => (
                    <tr key={action.action_type}>
                      <td>{action.action_type}</td>
                      <td>{action.quantity}</td>
                      <td>{action.tokens_consumed}</td>
                      <td>${action.estimated_cost}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>

          <div className="table-card">
            <div className="table-card-header">
              <h3>Action usage logs</h3>
              <span className="muted-copy small-copy">Page {page}</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Action</th>
                  <th>Reference</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {actionLogs.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.occurred_at).toLocaleString()}</td>
                    <td>{item.action_type}</td>
                    <td>{item.reference_type ?? "-"} {item.reference_id ?? ""}</td>
                    <td>{item.tokens_consumed}</td>
                    <td>${item.estimated_cost}</td>
                  </tr>
                ))}
                {actionLogs.length === 0 ? <tr><td colSpan={5}>No action usage logged yet.</td></tr> : null}
              </tbody>
            </table>
          </div>

          <div className="table-card">
            <div className="table-card-header">
              <h3>LLM token usage</h3>
            </div>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Feature</th>
                  <th>Total tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {llmUsage.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.used_at).toLocaleString()}</td>
                    <td>{item.provider}</td>
                    <td>{item.model_name}</td>
                    <td>{item.feature_name}</td>
                    <td>{item.total_tokens}</td>
                    <td>${item.estimated_cost}</td>
                  </tr>
                ))}
                {llmUsage.length === 0 ? <tr><td colSpan={6}>No LLM usage recorded yet.</td></tr> : null}
              </tbody>
            </table>
          </div>

          <div className="pagination-row">
            <button type="button" className="secondary-action" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
            <button type="button" className="secondary-action" onClick={() => setPage((current) => current + 1)}>Next</button>
          </div>
        </>
      ) : null}
    </section>
  );
}
