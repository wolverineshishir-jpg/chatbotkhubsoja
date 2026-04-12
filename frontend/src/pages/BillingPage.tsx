import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { CustomSelect } from "../components/common/CustomSelect";
import { PageHeader } from "../components/common/PageHeader";
import { createAccountSubscription, getAccountSubscription, getWalletBalance, listBillingPlans } from "../features/billing/api/billingApi";
import type { AccountSubscription, BillingPlan, WalletBalance } from "../shared/types/billing";

export function BillingPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [subscription, setSubscription] = useState<AccountSubscription | null>(null);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [selectedPlanCode, setSelectedPlanCode] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    const [planResponse, subscriptionResponse, walletResponse] = await Promise.all([
      listBillingPlans(),
      getAccountSubscription(),
      getWalletBalance(),
    ]);
    setPlans(planResponse.items);
    setSubscription(subscriptionResponse);
    setWallet(walletResponse);
    setSelectedPlanCode(subscriptionResponse?.plan.code ?? planResponse.items[0]?.code ?? "");
  };

  useEffect(() => {
    load().catch(() => setError("Unable to load billing workspace."));
  }, []);

  const handleSubscribe = async () => {
    if (!selectedPlanCode) return;
    setSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await createAccountSubscription({ billing_plan_code: selectedPlanCode, status: "active" });
      setSubscription(updated);
      await load();
      setMessage(`Subscription updated to ${updated.plan.name}.`);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to update subscription.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section>
      <PageHeader
        eyebrow="Billing"
        title="Subscription overview"
        description="Manage the active plan, review token wallet health, and navigate billing history and package purchases."
      />

      {message ? <div className="panel success-panel">{message}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      <div className="metric-grid">
        <article className="card metric-card"><p className="metric-label">Active tokens</p><strong className="metric-value">{wallet?.breakdown.total_available_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Monthly free</p><strong className="metric-value">{wallet?.breakdown.available_monthly_free_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Purchased tokens</p><strong className="metric-value">{wallet?.breakdown.available_purchased_tokens ?? 0}</strong></article>
        <article className="card metric-card"><p className="metric-label">Expiring in 7 days</p><strong className="metric-value">{wallet?.breakdown.expiring_next_tokens ?? 0}</strong></article>
      </div>

      <div className="dashboard-grid reporting-overview-grid">
        <section className="panel form-panel">
          <h3>Current subscription</h3>
          <div className="summary-stat-list">
            <div><span>Plan</span><strong>{subscription?.plan.name ?? "No active subscription"}</strong></div>
            <div><span>Status</span><strong>{subscription?.status ?? "not_configured"}</strong></div>
            <div><span>Monthly fee</span><strong>${subscription?.plan.price_usd ?? "0"}</strong></div>
            <div><span>Setup fee</span><strong>${subscription?.plan.setup_fee_usd ?? "0"}</strong></div>
            <div><span>Renews at</span><strong>{subscription?.renews_at ? new Date(subscription.renews_at).toLocaleDateString() : "N/A"}</strong></div>
          </div>
          <label>
            Choose plan
            <CustomSelect
              value={selectedPlanCode}
              onChange={setSelectedPlanCode}
              options={plans.map((plan) => ({
                value: plan.code,
                label: `${plan.name} | $${plan.price_usd}/${plan.billing_interval}`,
                helper: `${plan.monthly_token_credit} monthly tokens`,
              }))}
            />
          </label>
          <button type="button" onClick={handleSubscribe} disabled={!selectedPlanCode || submitting}>
            {submitting ? "Updating..." : "Create or update subscription"}
          </button>
        </section>

        <section className="panel">
          <h3>Billing navigation</h3>
          <div className="summary-stat-list">
            <div><span>Plans</span><strong><Link to="/billing/plans">Open plans catalog</Link></strong></div>
            <div><span>Wallet</span><strong><Link to="/wallet">Open token wallet</Link></strong></div>
            <div><span>History</span><strong><Link to="/billing/history">Open billing history</Link></strong></div>
            <div><span>Packages</span><strong><Link to="/billing/packages">Open token packages</Link></strong></div>
          </div>
        </section>
      </div>
    </section>
  );
}
