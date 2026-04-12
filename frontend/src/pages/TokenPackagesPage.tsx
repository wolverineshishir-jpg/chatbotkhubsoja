import { useEffect, useState } from "react";

import { PageHeader } from "../components/common/PageHeader";
import { listTokenPackages, purchaseTokenPackage } from "../features/billing/api/billingApi";
import type { TokenPackage } from "../shared/types/billing";

export function TokenPackagesPage() {
  const [packages, setPackages] = useState<TokenPackage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [purchasingCode, setPurchasingCode] = useState<string | null>(null);

  const load = async () => {
    const response = await listTokenPackages();
    setPackages(response.items);
  };

  useEffect(() => {
    load().catch(() => setError("Unable to load token packages."));
  }, []);

  const handlePurchase = async (packageCode: string) => {
    setPurchasingCode(packageCode);
    setError(null);
    setMessage(null);
    try {
      const transaction = await purchaseTokenPackage(packageCode);
      setMessage(`Token purchase recorded as transaction #${transaction.id}.`);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to purchase token package.");
    } finally {
      setPurchasingCode(null);
    }
  };

  return (
    <section>
      <PageHeader eyebrow="Billing" title="Token packages" description="Purchase non-expiring token packages through internal transaction records while external payment integration is still abstracted." />
      {message ? <div className="panel success-panel">{message}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}
      <div className="dashboard-grid reporting-overview-grid">
        {packages.map((item) => (
          <article key={item.code} className="panel">
            <h3>{item.name}</h3>
            <p className="muted-copy">{item.description}</p>
            <div className="summary-stat-list">
              <div><span>Tokens</span><strong>{item.token_amount}</strong></div>
              <div><span>Bonus</span><strong>{item.bonus_tokens}</strong></div>
              <div><span>Price</span><strong>{item.currency} {item.price_usd}</strong></div>
            </div>
            <button type="button" onClick={() => handlePurchase(item.code)} disabled={purchasingCode === item.code}>
              {purchasingCode === item.code ? "Purchasing..." : "Purchase package"}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
