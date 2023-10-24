import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi } from "../hooks/useApi";

export function Enterprise() {
  const program = useApi(() => apiGet<unknown>(API.ENTERPRISE_PROGRAM));
  const budget = useApi(() => apiGet<unknown>(API.ENTERPRISE_BUDGET));
  const boardPack = useApi(() => apiGet<unknown>(API.ENTERPRISE_BOARD_PACK));

  const loading = program.loading || budget.loading || boardPack.loading;
  const error = program.error || budget.error || boardPack.error;

  return (
    <PageShell
      title="Enterprise"
      subtitle="Executive program overview, budget allocation, and board pack compliance."
      actions={
        <button
          type="button"
          onClick={() => {
            program.refetch();
            budget.refetch();
            boardPack.refetch();
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
            program.refetch();
            budget.refetch();
            boardPack.refetch();
          }}
        />
      )}
      {!loading && !error && (
        <div className="card-grid">
          <JsonPanel title="Program" data={program.data} />
          <JsonPanel title="Budget" data={budget.data} />
          <JsonPanel title="Board Pack" data={boardPack.data} />
        </div>
      )}
    </PageShell>
  );
}
