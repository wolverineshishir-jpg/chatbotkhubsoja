import { useEffect, useState } from "react";

import { LoadingPanel } from "../components/common/LoadingPanel";
import { PageHeader } from "../components/common/PageHeader";
import { listAuditLogs } from "../features/observability/api/observabilityApi";
import type { AuditLog } from "../shared/types/observability";

export function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const response = await listAuditLogs({ page, page_size: 20 });
        setLogs(response.items);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Unable to load audit logs.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [page]);

  return (
    <section>
      <PageHeader
        eyebrow="Audit"
        title="Audit log"
        description="Review important account-scoped admin actions, when they happened, and which resources they affected."
      />

      {error ? <div className="panel error-panel">{error}</div> : null}
      {loading ? <LoadingPanel message="Loading audit logs..." hint="Fetching recent account activity." /> : null}

      <div className="table-card">
        <div className="table-card-header">
          <h3>Audit events</h3>
          <span className="muted-copy small-copy">Page {page}</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Description</th>
              <th>Action</th>
              <th>Resource</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((item) => (
              <tr key={item.id}>
                <td>{new Date(item.occurred_at).toLocaleString()}</td>
                <td>{item.description}</td>
                <td>{item.action_type}</td>
                <td>{item.resource_type}{item.resource_id ? ` #${item.resource_id}` : ""}</td>
                <td>{item.ip_address ?? "-"}</td>
              </tr>
            ))}
            {logs.length === 0 ? <tr><td colSpan={5}>No audit logs recorded yet.</td></tr> : null}
          </tbody>
        </table>
      </div>

      <div className="pagination-row">
        <button type="button" className="secondary-action" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
        <button type="button" className="secondary-action" onClick={() => setPage((current) => current + 1)}>Next</button>
      </div>
    </section>
  );
}
