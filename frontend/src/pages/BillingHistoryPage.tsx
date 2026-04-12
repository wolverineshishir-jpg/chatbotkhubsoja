import { useEffect, useState } from "react";

import { PageHeader } from "../components/common/PageHeader";
import { listBillingTransactions } from "../features/billing/api/billingApi";
import type { BillingTransaction } from "../shared/types/billing";

export function BillingHistoryPage() {
  const [transactions, setTransactions] = useState<BillingTransaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listBillingTransactions()
      .then((response) => setTransactions(response.items))
      .catch(() => setError("Unable to load billing history."));
  }, []);

  return (
    <section>
      <PageHeader eyebrow="Billing" title="Billing history" description="Review internal subscription and token purchase transactions while payment gateway integration remains abstracted." />
      {error ? <div className="panel error-panel">{error}</div> : null}
      <section className="table-card">
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Type</th>
              <th>Status</th>
              <th>Total</th>
              <th>Provider</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id}>
                <td>{new Date(transaction.occurred_at).toLocaleString()}</td>
                <td>{transaction.transaction_type}</td>
                <td>{transaction.status}</td>
                <td>{transaction.currency} {transaction.total_amount_usd}</td>
                <td>{transaction.provider_name ?? "internal"}</td>
              </tr>
            ))}
            {transactions.length === 0 ? (
              <tr><td colSpan={5}>No billing transactions yet.</td></tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </section>
  );
}
