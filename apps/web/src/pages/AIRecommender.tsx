import { useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API, DEFAULT_SET_ID } from "../constants/api";
import { useApi, useMutation } from "../hooks/useApi";

type AiTab = "recommend" | "similar";

export function AIRecommender() {
  const [setId, setSetId] = useState(DEFAULT_SET_ID);
  const [tab, setTab] = useState<AiTab>("recommend");

  const recommendGet = useApi(
    () => apiGet<unknown>(`${API.AI_RECOMMEND}?set_id=${encodeURIComponent(setId)}`),
    [setId, tab === "recommend"],
  );
  const similarGet = useApi(
    () => apiGet<unknown>(`${API.AI_SIMILAR}?set_id=${encodeURIComponent(setId)}`),
    [setId, tab === "similar"],
  );

  const recommendPost = useMutation(() =>
    apiPost<unknown>(API.AI_RECOMMEND, { set_id: setId }),
  );
  const similarPost = useMutation(() =>
    apiPost<unknown>(API.AI_SIMILAR, { set_id: setId }),
  );

  const active = tab === "recommend" ? recommendGet : similarGet;
  const postMut = tab === "recommend" ? recommendPost : similarPost;

  return (
    <PageShell
      title="AI Recommender"
      subtitle="Heuristic exhibition recommendations and similar-set transitions for curation planning."
    >
      <div className="field" style={{ maxWidth: 280 }}>
        <label htmlFor="ai-set-id">Set ID</label>
        <input id="ai-set-id" value={setId} onChange={(e) => setSetId(e.target.value)} />
      </div>

      <div className="tabs">
        <button
          type="button"
          className={tab === "recommend" ? "tab active" : "tab"}
          onClick={() => setTab("recommend")}
        >
          Recommendations
        </button>
        <button
          type="button"
          className={tab === "similar" ? "tab active" : "tab"}
          onClick={() => setTab("similar")}
        >
          Similar Sets
        </button>
      </div>

      {active.loading && <LoadingBanner />}
      {active.error && !active.loading && (
        <ErrorBanner message={active.error} onRetry={active.refetch} />
      )}
      {!active.loading && !active.error && (
        <JsonPanel title={`GET ${tab}`} data={active.data} />
      )}

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <h2>POST variant</h2>
        <button
          type="button"
          className="primary"
          disabled={postMut.loading}
          onClick={() => postMut.mutate()}
        >
          {postMut.loading ? "Fetching…" : `POST /ai/${tab}`}
        </button>
        {postMut.error ? <ErrorBanner message={postMut.error} /> : null}
        {postMut.data ? <JsonPanel data={postMut.data} /> : null}
      </div>
    </PageShell>
  );
}
