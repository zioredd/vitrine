import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell, StatCard } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi } from "../hooks/useApi";

export function Dashboard() {
  const intelligence = useApi(() => apiGet<Record<string, unknown>>(API.INTELLIGENCE));
  const command = useApi(() => apiGet<Record<string, unknown>>(API.COMMAND_CENTER));
  const editorial = useApi(() => apiGet<Record<string, unknown>>(API.EDITORIAL_DECISION_REPORT));

  const loading = intelligence.loading || command.loading || editorial.loading;
  const error = intelligence.error || command.error || editorial.error;

  return (
    <PageShell
      title="Command Center"
      subtitle="Intelligence overview across exhibitions, editorial signals, and operational health."
      actions={
        <button type="button" onClick={() => {
          intelligence.refetch();
          command.refetch();
          editorial.refetch();
        }}>
          Refresh all
        </button>
      }
    >
      {loading && <LoadingBanner />}
      {error && !loading && (
        <ErrorBanner
          message={error}
          onRetry={() => {
            intelligence.refetch();
            command.refetch();
            editorial.refetch();
          }}
        />
      )}
      {!loading && !error && (
        <>
          <div className="card-grid" style={{ marginBottom: "1.5rem" }}>
            <StatCard label="Intelligence keys" value={Object.keys(intelligence.data ?? {}).length} />
            <StatCard label="Command metrics" value={Object.keys(command.data ?? {}).length} />
            <StatCard label="Editorial factors" value={Object.keys(editorial.data ?? {}).length} />
          </div>
          <div className="card-grid">
            <JsonPanel title="Intelligence Report" data={intelligence.data} />
            <JsonPanel title="Command Center" data={command.data} />
            <JsonPanel title="Editorial Decision Report" data={editorial.data} />
          </div>
        </>
      )}
    </PageShell>
  );
}
