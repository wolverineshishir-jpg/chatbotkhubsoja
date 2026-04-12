import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../features/auth/store/authStore";
import { logout } from "../features/auth/api/authApi";
import { getBillingSummary } from "../features/reports/api/reportApi";
import { useResponsiveTables } from "../hooks/useResponsiveTables";

type NavItem = {
  to: string;
  label: string;
  featurePermission?: string;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const NAV_SECTIONS = [
  {
    title: "Overview",
    items: [{ to: "/", label: "Dashboard" }],
  },
  {
    title: "Operations",
    items: [
      { to: "/inbox/whatsapp", label: "WhatsApp Inbox", featurePermission: "feature:whatsapp_inbox" },
      { to: "/inbox/facebook", label: "Facebook Inbox", featurePermission: "feature:facebook_inbox" },
      { to: "/comments", label: "Facebook Comments", featurePermission: "feature:facebook_comments" },
      { to: "/posts", label: "Facebook Posts", featurePermission: "feature:facebook_posts" },
      { to: "/automation", label: "Automation" },
      { to: "/connections", label: "Channels" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { to: "/ai", label: "AI Overview" },
      { to: "/ai/agents", label: "AI Agents" },
      { to: "/ai/prompts", label: "Prompts" },
      { to: "/ai/knowledge", label: "Knowledge" },
      { to: "/ai/faq", label: "FAQs" },
    ],
  },
  {
    title: "Revenue",
    items: [
      { to: "/billing", label: "Billing" },
      { to: "/wallet", label: "Wallet" },
      { to: "/usage", label: "Usage" },
      { to: "/audit-logs", label: "Audit Logs" },
    ],
  },
  {
    title: "Account",
    items: [
      { to: "/setup", label: "Setup" },
      { to: "/team", label: "Users" },
      { to: "/security/password", label: "Change Password" },
    ],
  },
] satisfies NavSection[];

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const activeAccountId = useAuthStore((state) => state.activeAccountId);
  const clear = useAuthStore((state) => state.clear);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [usedTokenPercent, setUsedTokenPercent] = useState<number | null>(null);
  useResponsiveTables(location.pathname);

  const visibleSections = useMemo(() => {
    if (!user || user.user_role !== "superAdmin") {
      return NAV_SECTIONS;
    }

    const selectedFeatures = new Set(
      (user.permissions ?? []).filter((permission) => permission.startsWith("feature:")),
    );
    const hasFeatureSelection = selectedFeatures.size > 0;

    return NAV_SECTIONS.map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (!item.featurePermission) {
          return true;
        }
        if (!hasFeatureSelection) {
          return true;
        }
        return selectedFeatures.has(item.featurePermission);
      }),
    })).filter((section) => section.items.length > 0);
  }, [user]);

  const currentPage = useMemo(() => {
    const allItems = visibleSections.flatMap((section) => section.items);
    const matchedItems = allItems.filter((item) => {
      if (item.to === "/") {
        return location.pathname === "/";
      }
      return location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
    });

    return matchedItems.sort((left, right) => right.to.length - left.to.length)[0];
  }, [location.pathname, visibleSections]);

  const currentPageTitle = useMemo(() => {
    if (currentPage && currentPage.to.startsWith("/ai/") && currentPage.to !== "/ai") {
      return `AI Overview (${currentPage.label})`;
    }
    return currentPage?.label ?? "Workspace";
  }, [currentPage]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    let cancelled = false;

    async function loadTokenUsagePercent() {
      if (!activeAccountId) {
        setUsedTokenPercent(null);
        return;
      }

      try {
        const summary = await getBillingSummary();
        const monthlyCredit = Math.max(summary.monthly_token_credit ?? 0, 0);
        if (monthlyCredit === 0) {
          if (!cancelled) setUsedTokenPercent(0);
          return;
        }

        const raw = (summary.billed_tokens / monthlyCredit) * 100;
        const percent = Math.max(0, Math.min(100, Math.round(raw)));
        if (!cancelled) setUsedTokenPercent(percent);
      } catch {
        if (!cancelled) setUsedTokenPercent(null);
      }
    }

    loadTokenUsagePercent();
    return () => {
      cancelled = true;
    };
  }, [activeAccountId]);

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await logout(refreshToken);
      }
    } finally {
      clear();
      navigate("/login");
    }
  };

  return (
    <div className={`shell ${sidebarOpen ? "nav-open" : ""}`}>
      <button
        aria-hidden={!sidebarOpen}
        aria-label="Close navigation"
        className="sidebar-backdrop"
        tabIndex={sidebarOpen ? 0 : -1}
        type="button"
        onClick={() => setSidebarOpen(false)}
      />

      <aside className="sidebar">
        <div className="sidebar-inner">
          <div className="sidebar-header">
            <div className="sidebar-brand">
              <div className="brand-mark" aria-hidden="true">
                SC
              </div>
              <div>
                <h1>Navigation</h1>
              </div>
            </div>
            <button
              aria-label="Close navigation"
              className="sidebar-close"
              type="button"
              onClick={() => setSidebarOpen(false)}
            >
              Close
            </button>
          </div>

          <nav className="nav" aria-label="Primary navigation">
            {visibleSections.map((section) => (
              <div className="nav-section" key={section.title}>
                <p className="nav-section-title">{section.title}</p>
                <div className="nav-links">
                  {section.items.map((item) => (
                    <NavLink key={item.to} to={item.to}>
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>

        </div>
      </aside>

      <div className="app-stage">
        <header className="topbar">
          <div className="topbar-main">
            <button
              aria-expanded={sidebarOpen}
              aria-label="Toggle navigation"
              className="menu-button"
              type="button"
              onClick={() => setSidebarOpen((current) => !current)}
            >
              <span className="menu-button-lines" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
              <span>Menu</span>
            </button>
            <div className="topbar-copy">
              <h2>{currentPageTitle}</h2>
            </div>
          </div>

          <div className="topbar-right">
            <div className="topbar-meta">
              <div className="topbar-chip topbar-chip-inline">
                <strong>{`Token used: ${usedTokenPercent ?? "--"}%`}</strong>
              </div>
            </div>
            <button className="ghost-button topbar-signout" type="button" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
