import { useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API, DEFAULT_SET_ID } from "../constants/api";
import { useApi } from "../hooks/useApi";

type CraftTab = "detail" | "pacing" | "dialogue";

export function ExhibitionDetail() {
  const { id = DEFAULT_SET_ID } = useParams();
  const [tab, setTab] = useState<CraftTab>("detail");

  const detail = useApi(() => apiGet<Record<string, unknown>>(API.SET_DETAIL(id)), [id]);
  const pacing = useApi(
    () => apiGet<unknown>(API.CRAFT_PACING(id)),
    [id, tab === "pacing"],
  );
  const dialogue = useApi(
    () => apiGet<unknown>(API.CRAFT_DIALOGUE(id)),
    [id, tab === "dialogue"],
  );

  const active = tab === "detail" ? detail : tab === "pacing" ? pacing : dialogue;

  return (
    <PageShell
      title="Exhibition Detail"
      subtitle={`Set ${id} — craft analytics and profile metadata.`}
      actions={<button type="button" onClick={() => detail.refetch()}>Refresh</button>}
    >
      <div className="tabs">
        {(["detail", "pacing", "dialogue"] as CraftTab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "detail" ? "Profile" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {active.loading && <LoadingBanner />}
      {active.error && !active.loading && (
        <ErrorBanner message={active.error} onRetry={active.refetch} />
      )}
      {!active.loading && !active.error && (
        <JsonPanel
          title={tab === "detail" ? "Exhibition Profile" : `Craft — ${tab}`}
          data={active.data}
        />
      )}
    </PageShell>
  );
}
