import type { ReactNode } from "react";

interface PageShellProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export function PageShell({ title, subtitle, children, actions }: PageShellProps) {
  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          {subtitle && <p className="subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="header-actions">{actions}</div>}
      </header>
      {children}
      <style>{`
        .page-header {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid var(--color-border);
        }
        .subtitle {
          margin: 0.35rem 0 0;
          color: var(--color-text-muted);
          font-size: 0.95rem;
          max-width: 52ch;
        }
        .header-actions {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .empty {
          color: var(--color-text-muted);
          font-style: italic;
        }
        .data-list {
          list-style: none;
          margin: 0;
          padding: 0;
        }
        .data-list li {
          padding: 0.65rem 0;
          border-bottom: 1px solid var(--color-border);
        }
      `}</style>
    </div>
  );
}

export function LoadingBanner() {
  return <div className="status-banner loading">Loading exhibition data…</div>;
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="status-banner error">
      <strong>Unable to load data.</strong> {message}
      {onRetry && (
        <div className="actions">
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

export function JsonPanel({ data, title }: { data: unknown; title?: string }) {
  return (
    <div className="card">
      {title && <h2>{title}</h2>}
      <pre className="code-block">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}
