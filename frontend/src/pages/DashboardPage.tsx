import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { LoadingPanel } from "../components/common/LoadingPanel";
import { PageHeader } from "../components/common/PageHeader";
import { listAuditLogs } from "../features/observability/api/observabilityApi";
import {
  getBillingSummary,
  getCommentStats,
  getConversationStats,
  getDashboardSummary,
  getPostStats,
} from "../features/reports/api/reportApi";
import { useAuthStore } from "../features/auth/store/authStore";
import type { AuditLog } from "../shared/types/observability";
import type { BillingSummary, CommentStats, ConversationStats, DashboardSummary, PostStats } from "../shared/types/reports";

export function DashboardPage() {
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const user = useAuthStore((state) => state.user);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [billing, setBilling] = useState<BillingSummary | null>(null);
  const [conversationStats, setConversationStats] = useState<ConversationStats | null>(null);
  const [commentStats, setCommentStats] = useState<CommentStats | null>(null);
  const [postStats, setPostStats] = useState<PostStats | null>(null);
  const [recentAudit, setRecentAudit] = useState<AuditLog[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);

  const activeMembership = user?.memberships.find((membership) => membership.account_id === activeAccountId) ?? null;
  const accessRole = user?.user_role ?? activeMembership?.role ?? null;
  const spotlightItems = [
    {
      label: "Workspace",
      value: activeMembership?.account_name ?? "No account",
      helper: accessRole ? `${accessRole} access` : "Create or join a workspace to continue",
    },
    {
      label: "Token balance",
      value: `${billing?.current_token_balance ?? 0}`,
      helper: `${billing?.monthly_token_credit ?? 0} monthly credit`,
    },
    {
      label: "Open workload",
      value: `${summary?.open_conversations ?? 0}`,
      helper: `${summary?.pending_comments ?? 0} comments awaiting review`,
    },
    {
      label: "Content queue",
      value: `${summary?.scheduled_posts ?? 0}`,
      helper: `${postStats?.total_posts ?? 0} total tracked posts`,
    },
  ];

  const loadReports = async () => {
    if (!activeMembership) return;
    setLoadingReports(true);
    try {
      const [dashboardData, billingData, conversationData, commentData, postData, auditData] = await Promise.all([
        getDashboardSummary(),
        getBillingSummary(),
        getConversationStats(),
        getCommentStats(),
        getPostStats(),
        listAuditLogs({ page: 1, page_size: 5 }),
      ]);
      setSummary(dashboardData);
      setBilling(billingData);
      setConversationStats(conversationData);
      setCommentStats(commentData);
      setPostStats(postData);
      setRecentAudit(auditData.items);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Unable to load dashboard reports.");
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [activeMembership?.account_id]);

  if (!activeMembership) {
    return (
      <section>
        <PageHeader
          eyebrow="Dashboard"
          title="Access is managed by role"
          description="The system owner creates super admins, and each super admin manages the admins inside their own workspace."
        />

        {error ? <div className="panel error-panel">{error}</div> : null}

        <div className="panel dashboard-onboarding-callout">
          <div>
            <p className="eyebrow">Get started</p>
            <h3>Workspace access now comes from managed user provisioning.</h3>
            <p className="muted-copy">
              Owners should open the team management screen to create super admins. Super admins can then create admins with
              custom permissions for their workspace.
            </p>
          </div>
          <div className="dashboard-hero-grid">
            <article className="hero-stat">
              <span>Channels</span>
              <strong>Inbox + comments</strong>
            </article>
            <article className="hero-stat">
              <span>Publishing</span>
              <strong>Draft to publish flow</strong>
            </article>
            <article className="hero-stat">
              <span>AI</span>
              <strong>Prompts, agents, replies</strong>
            </article>
          </div>
        </div>

        <div className="dashboard-grid">
          <section className="panel">
            <h3>Next step</h3>
            <p className="muted-copy">Open the user management workspace to provision super admins or admins.</p>
            <Link className="text-link secondary-link" to="/team">
              Open user management
            </Link>
          </section>
        </div>
      </section>
    );
  }

  return (
    <section>
      <PageHeader
        eyebrow="Dashboard"
        title="Operational visibility"
        description="Track token usage, billing estimates, workflow volume, and recent admin actions for the active account."
      />

      {error ? <div className="panel error-panel">{error}</div> : null}

      <section className="panel dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Live account status</p>
          <h3>{activeMembership.account_name} is ready for daily operations</h3>
          <p className="muted-copy">
            Keep an eye on service activity, team workload, token health, and recent admin activity without jumping between
            pages.
          </p>
          <div className="quick-links dashboard-hero-actions">
            <Link className="secondary-action" to="/inbox/whatsapp">Open inbox</Link>
            <Link className="secondary-action" to="/comments">Review comments</Link>
            <Link className="secondary-action" to="/usage">Check usage</Link>
          </div>
        </div>

        <div className="dashboard-hero-grid">
          {spotlightItems.map((item) => (
            <article className="hero-stat" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <small>{item.helper}</small>
            </article>
          ))}
        </div>
      </section>

      {loadingReports ? (
        <LoadingPanel message="Loading dashboard metrics..." hint="Pulling latest billing, activity, and usage summaries." />
      ) : null}

      <div className="metric-grid">
        {summary?.cards.map((card) => (
          <article className="card metric-card" key={card.label}>
            <p className="metric-label">{card.label}</p>
            <strong className="metric-value">{card.value}</strong>
            <span className="muted-copy">{card.secondary}</span>
          </article>
        ))}
      </div>

      <div className="dashboard-grid reporting-overview-grid">
        <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Workflow summary</h3>
              <p className="muted-copy small-copy">Current account activity snapshot.</p>
            </div>
            <Link className="secondary-action" to="/usage">Usage report</Link>
          </div>
          <div className="summary-stat-list">
            <div>
              <span>Conversations open</span>
              <strong>{summary?.open_conversations ?? 0}</strong>
            </div>
            <div>
              <span>Pending comments</span>
              <strong>{summary?.pending_comments ?? 0}</strong>
            </div>
            <div>
              <span>Scheduled posts</span>
              <strong>{summary?.scheduled_posts ?? 0}</strong>
            </div>
            <div>
              <span>Audit events last 7 days</span>
              <strong>{summary?.latest_audit_events ?? 0}</strong>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Billing snapshot</h3>
              <p className="muted-copy small-copy">Estimated usage cost and token allocation.</p>
            </div>
            <Link className="secondary-action" to="/billing">Billing</Link>
          </div>
          <div className="summary-stat-list">
            <div>
              <span>Token balance</span>
              <strong>{billing?.current_token_balance ?? 0}</strong>
            </div>
            <div>
              <span>Monthly credit</span>
              <strong>{billing?.monthly_token_credit ?? 0}</strong>
            </div>
            <div>
              <span>Billed tokens</span>
              <strong>{billing?.billed_tokens ?? 0}</strong>
            </div>
            <div>
              <span>Estimated cost</span>
              <strong>${billing?.total_estimated_cost ?? "0.00"}</strong>
            </div>
            <div>
              <span>Plan</span>
              <strong>{billing?.active_plan_name ?? "Not configured"}</strong>
            </div>
          </div>
        </section>
      </div>

      <div className="dashboard-grid reporting-overview-grid">
        <section className="panel">
          <div className="section-heading">
            <h3>Volume trends</h3>
            <p className="muted-copy small-copy">Last 7 days across core modules.</p>
          </div>
          <div className="mini-chart-stack">
            <MiniTrendChart title="Conversations" points={conversationStats?.recent_daily_counts ?? []} />
            <MiniTrendChart title="Comments" points={commentStats?.recent_daily_counts ?? []} />
            <MiniTrendChart title="Posts" points={postStats?.recent_daily_counts ?? []} />
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Recent audit activity</h3>
              <p className="muted-copy small-copy">Latest important admin actions.</p>
            </div>
            <Link className="secondary-action" to="/audit-logs">Audit log</Link>
          </div>
          <div className="activity-feed">
            {recentAudit.map((entry) => (
              <article className="activity-item" key={entry.id}>
                <div>
                  <strong>{entry.description}</strong>
                  <p className="muted-copy small-copy">
                    {entry.action_type} | {entry.resource_type}
                  </p>
                </div>
                <time className="muted-copy small-copy">{new Date(entry.occurred_at).toLocaleString()}</time>
              </article>
            ))}
            {recentAudit.length === 0 ? <p className="muted-copy">No audit events recorded yet.</p> : null}
          </div>
        </section>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <h3>User management</h3>
          <p className="muted-copy">Create and maintain admins from the dedicated user management screen.</p>
          <Link className="text-link secondary-link" to="/team">
            Open team management
          </Link>
        </section>

        <section className="panel">
          <h3>Quick links</h3>
          <div className="quick-links">
            <Link className="secondary-action" to="/inbox/whatsapp">Review inbox</Link>
            <Link className="secondary-action" to="/comments">Moderate comments</Link>
            <Link className="secondary-action" to="/posts">Manage posts</Link>
            <Link className="secondary-action" to="/usage">Open usage report</Link>
          </div>
        </section>
      </div>
    </section>
  );
}

function MiniTrendChart({ title, points }: { title: string; points: Array<{ date: string; count: number }> }) {
  const max = Math.max(...points.map((point) => point.count), 1);

  return (
    <div className="mini-chart">
      <div className="section-heading compact-heading">
        <h4>{title}</h4>
      </div>
      <div className="mini-chart-bars">
        {points.map((point) => (
          <div className="mini-bar-wrap" key={`${title}-${point.date}`}>
            <span className="mini-bar-label">{new Date(point.date).toLocaleDateString(undefined, { weekday: "short" })}</span>
            <div className="mini-bar-track">
              <span className="mini-bar-fill" style={{ width: `${(point.count / max) * 100}%` }} />
            </div>
            <strong>{point.count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
