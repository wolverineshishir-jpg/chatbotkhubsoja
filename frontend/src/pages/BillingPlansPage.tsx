import { useEffect, useState } from "react";

import { PageHeader } from "../components/common/PageHeader";
import { listBillingFeatures, listBillingPlans } from "../features/billing/api/billingApi";
import type { BillingPlan, FeatureCatalogItem } from "../shared/types/billing";

export function BillingPlansPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [features, setFeatures] = useState<FeatureCatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listBillingPlans(), listBillingFeatures()])
      .then(([planResponse, featureResponse]) => {
        setPlans(planResponse.items);
        setFeatures(featureResponse.items);
      })
      .catch(() => setError("Unable to load plans and features."));
  }, []);

  return (
    <section>
      <PageHeader eyebrow="Billing" title="Plans catalog" description="Review plan pricing, included monthly tokens, setup fees, and linked feature entitlements." />
      {error ? <div className="panel error-panel">{error}</div> : null}
      <div className="dashboard-grid reporting-overview-grid">
        {plans.map((plan) => (
          <article key={plan.code} className="panel">
            <h3>{plan.name}</h3>
            <p className="muted-copy">{plan.description}</p>
            <div className="summary-stat-list">
              <div><span>Monthly fee</span><strong>${plan.price_usd}</strong></div>
              <div><span>Setup fee</span><strong>${plan.setup_fee_usd}</strong></div>
              <div><span>Monthly tokens</span><strong>{plan.monthly_token_credit}</strong></div>
            </div>
            <div className="muted-copy small-copy">Included features</div>
            <ul>
              {plan.features.map((feature) => (
                <li key={feature.feature.code}>
                  {feature.feature.name}: {feature.included_value}{feature.feature.unit_label ? ` ${feature.feature.unit_label}` : ""}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
      <section className="table-card">
        <div className="table-card-header">
          <h3>Feature catalog</h3>
        </div>
        <table>
          <thead>
            <tr><th>Feature</th><th>Code</th><th>Type</th></tr>
          </thead>
          <tbody>
            {features.map((feature) => (
              <tr key={feature.code}>
                <td>{feature.name}</td>
                <td>{feature.code}</td>
                <td>{feature.value_type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  );
}
