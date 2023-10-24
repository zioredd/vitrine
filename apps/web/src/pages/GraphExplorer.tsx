import { useState } from "react";
import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API, DEFAULT_SET_ID } from "../constants/api";
import { useApi } from "../hooks/useApi";

type GraphTab = "path" | "traverse" | "residency";

export function GraphExplorer() {
  const [setId, setSetId] = useState(DEFAULT_SET_ID);
  const [tab, setTab] = useState<GraphTab>("path");

  const path = useApi(() => apiGet<unknown>(API.GRAPH_PATH(setId)), [setId, tab === "path"]);
  const traverse = useApi(
    () => apiGet<unknown>(API.GRAPH_TRAVERSE(setId)),
    [setId, tab === "traverse"],
  );
  const residency = useApi(
    () => apiGet<unknown>(API.GRAPH_RESIDENCY_TREE),
    [tab === "residency"],
  );

  const active = tab === "path" ? path : tab === "traverse" ? traverse : residency;

  return (
    <PageShell
      title="Graph Explorer"
      subtitle="Path finding, BFS traversal, and residency tree across artwork relationship graphs."
    >
      {tab !== "residency" && (
        <div className="field" style={{ maxWidth: 280 }}>
          <label htmlFor="graph-set-id">Set ID</label>
          <input
            id="graph-set-id"
            value={setId}
            onChange={(e) => setSetId(e.target.value)}
          />
        </div>
      )}

      <div className="tabs">
        {(["path", "traverse", "residency"] as GraphTab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "residency" ? "Residency Tree" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {active.loading && <LoadingBanner />}
      {active.error && !active.loading && (
        <ErrorBanner message={active.error} onRetry={active.refetch} />
      )}
      {!active.loading && !active.error && <JsonPanel data={active.data} />}
    </PageShell>
  );
}
