import { useEffect, useState } from "react";

import { PageHeader } from "../components/common/PageHeader";
import { getWalletBalance, listTokenLedgerEntries } from "../features/billing/api/billingApi";
import type { TokenLedgerEntry, WalletBalance } from "../shared/types/billing";

export function TokenWalletPage() {
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [ledger, setLedger] = useState<TokenLedgerEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getWalletBalance(), listTokenLedgerEntries()])
      .then(([walletResponse, ledgerResponse]) => {
        setWallet(walletResponse);
        setLedger(ledgerResponse.items);
      })
      .catch(() => setError("Unable to load token wallet."));
  }, []);

  return (
    <section>
      <PageHeader eyebrow="Wallet" title="Token wallet" description="Inspect available balances and ledger history. Monthly free tokens expire after 30 days, while purchased tokens do not expire." />
      {error ? <div className="panel error-panel">{error}</div> : null}
      <div className="metric-grid">
        <article className="card metric-card"><p className="metric-label">Total available</p><strong className="metric-value">{wallet?.breakdown.total_available_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Monthly free</p><strong className="metric-value">{wallet?.breakdown.available_monthly_free_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Purchased</p><strong className="metric-value">{wallet?.breakdown.available_purchased_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Manual</p><strong className="metric-value">{wallet?.breakdown.available_manual_tokens ?? 0}</strong></article>
      </div>
      <section className="table-card">
        <div className="table-card-header">
          <h3>Ledger</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Entry</th>
              <th>Allocation</th>
              <th>Delta</th>
              <th>Remaining</th>
              <th>Expires</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.occurred_at).toLocaleString()}</td>
                <td>{entry.entry_type}</td>
                <td>{entry.allocation_type ?? "-"}</td>
                <td>{entry.delta_tokens}</td>
                <td>{entry.remaining_tokens ?? "-"}</td>
                <td>{entry.expires_at ? new Date(entry.expires_at).toLocaleDateString() : "Never"}</td>
              </tr>
            ))}
            {ledger.length === 0 ? (
              <tr><td colSpan={6}>No wallet ledger entries yet.</td></tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </section>
  );
}
