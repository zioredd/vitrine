import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi } from "../hooks/useApi";

export function Editorial() {
  const risks = useApi(() => apiGet<unknown>(API.RISKS));
  const windows = useApi(() => apiGet<unknown>(API.PUBLICATION_WINDOWS));
  const signals = useApi(() => apiGet<unknown>(API.EDITORIAL_SIGNALS));

  const loading = risks.loading || windows.loading || signals.loading;
  const error = risks.error || windows.error || signals.error;

  return (
    <PageShell
      title="Editorial"
      subtitle="Publication risks, release windows, and editorial signal telemetry for curators."
      actions={
        <button
          type="button"
          onClick={() => {
            risks.refetch();
            windows.refetch();
            signals.refetch();
          }}
        >
          Refresh
        </button>
      }
    >
      {loading && <LoadingBanner />}
      {error && !loading && (
        <ErrorBanner
          message={error}
          onRetry={() => {
            risks.refetch();
            windows.refetch();
            signals.refetch();
          }}
        />
      )}
      {!loading && !error && (
        <div className="card-grid">
          <JsonPanel title="Risks" data={risks.data} />
          <JsonPanel title="Publication Windows" data={windows.data} />
          <JsonPanel title="Editorial Signals" data={signals.data} />
        </div>
      )}
    </PageShell>
  );
}
