import { useState } from "react";
import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API, DEFAULT_SET_ID } from "../constants/api";
import { useApi } from "../hooks/useApi";

type CrowdTab = "arc" | "web" | "clusters";

export function CrowdIntel() {
  const [setId, setSetId] = useState(DEFAULT_SET_ID);
  const [tab, setTab] = useState<CrowdTab>("arc");

  const arc = useApi(() => apiGet<unknown>(API.NARRATIVE_ARC(setId)), [setId, tab === "arc"]);
  const web = useApi(() => apiGet<unknown>(API.NARRATIVE_WEB(setId)), [setId, tab === "web"]);
  const clusters = useApi(() => apiGet<unknown>(API.THEME_CLUSTERS), [tab === "clusters"]);

  const active = tab === "arc" ? arc : tab === "web" ? web : clusters;

  return (
    <PageShell
      title="Crowd Intelligence"
      subtitle="Narrative arc, visitor web topology, and theme clusters across exhibitions."
    >
      <div className="field" style={{ maxWidth: 280 }}>
        <label htmlFor="set-id">Exhibition set ID</label>
        <input
          id="set-id"
          value={setId}
          onChange={(e) => setSetId(e.target.value)}
          placeholder="ex-001"
        />
      </div>

      <div className="tabs">
        {(["arc", "web", "clusters"] as CrowdTab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "arc" ? "Narrative Arc" : t === "web" ? "Visitor Web" : "Theme Clusters"}
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
