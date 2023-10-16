import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/catalog", label: "Catalog" },
  { to: "/exhibitions/ex-001", label: "Exhibition Detail" },
  { to: "/crowd-intel", label: "Crowd Intel" },
  { to: "/queue", label: "Queue" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/enterprise", label: "Enterprise" },
  { to: "/graph", label: "Graph Explorer" },
  { to: "/parser", label: "Parser Console" },
  { to: "/ingest", label: "Ingest" },
  { to: "/rules", label: "Rules Report" },
  { to: "/sync-rebalance", label: "Sync / Rebalance" },
  { to: "/editorial", label: "Editorial" },
  { to: "/ai", label: "AI Recommender" },
];

export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <div>
            <strong>Vitrine</strong>
            <span className="brand-tagline">Exhibition curation intelligence</span>
          </div>
        </div>
        <nav className="nav">
          {NAV_ITEMS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main-wrap">
        <main className="main">
          <Outlet />
        </main>
      </div>
      <style>{`
        .layout {
          display: flex;
          min-height: 100vh;
          position: relative;
          z-index: 1;
        }
        .sidebar {
          width: var(--nav-width);
          flex-shrink: 0;
          background: rgba(20, 22, 24, 0.92);
          border-right: 1px solid var(--color-border);
          padding: 1.5rem 0;
          display: flex;
          flex-direction: column;
          position: sticky;
          top: 0;
          height: 100vh;
          overflow-y: auto;
        }
        .brand {
          display: flex;
          align-items: flex-start;
          gap: 0.65rem;
          padding: 0 1.25rem 1.5rem;
          border-bottom: 1px solid var(--color-border);
          margin-bottom: 1rem;
        }
        .brand-mark {
          font-size: 1.4rem;
          color: var(--color-gold);
          line-height: 1;
        }
        .brand strong {
          display: block;
          font-family: var(--font-display);
          font-size: 1.35rem;
          color: var(--color-cream);
        }
        .brand-tagline {
          display: block;
          font-size: 0.72rem;
          color: var(--color-text-muted);
          margin-top: 0.15rem;
          line-height: 1.3;
        }
        .nav {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
          padding: 0 0.65rem;
        }
        .nav-link {
          display: block;
          padding: 0.5rem 0.75rem;
          border-radius: var(--radius);
          color: var(--color-text-muted);
          font-size: 0.88rem;
          text-decoration: none;
          transition: background 0.12s, color 0.12s;
        }
        .nav-link:hover {
          color: var(--color-text);
          background: rgba(184, 149, 106, 0.06);
          text-decoration: none;
        }
        .nav-link.active {
          color: var(--color-cream);
          background: var(--color-gold-soft);
          border: 1px solid rgba(184, 149, 106, 0.25);
        }
        .main-wrap {
          flex: 1;
          min-width: 0;
        }
        .main {
          padding: clamp(1rem, 3vw, 2rem);
          max-width: 1200px;
        }
        @media (max-width: 768px) {
          .layout {
            flex-direction: column;
          }
          .sidebar {
            width: 100%;
            height: auto;
            position: relative;
            padding: 1rem 0;
          }
          .nav {
            flex-direction: row;
            flex-wrap: wrap;
            padding: 0 0.75rem;
          }
          .nav-link {
            font-size: 0.8rem;
            padding: 0.4rem 0.6rem;
          }
        }
      `}</style>
    </div>
  );
}
