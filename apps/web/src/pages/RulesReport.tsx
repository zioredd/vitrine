import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi } from "../hooks/useApi";

export function RulesReport() {
  const report = useApi(() => apiGet<unknown>(API.RULES_REPORT));

  return (
    <PageShell
      title="Rules Report"
      subtitle="Data quality rule engine results across exhibition profiles and ingest pipelines."
      actions={<button type="button" onClick={() => report.refetch()}>Refresh</button>}
    >
      {report.loading && <LoadingBanner />}
      {report.error && !report.loading && (
        <ErrorBanner message={report.error} onRetry={report.refetch} />
      )}
      {!report.loading && !report.error && (
        <JsonPanel title="Quality Rules Report" data={report.data} />
      )}
    </PageShell>
  );
}
