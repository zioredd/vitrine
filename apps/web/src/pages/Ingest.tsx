import { useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API, DEFAULT_SET_ID } from "../constants/api";
import { useApi, useMutation } from "../hooks/useApi";

export function Ingest() {
  const [snapshot, setSnapshot] = useState('{"items": []}');
  const [ids, setIds] = useState(DEFAULT_SET_ID);

  const batchScore = useApi(() => apiGet<unknown>(API.CONCURRENCY_BATCH_SCORE));
  const concurrencyIngest = useApi(() => apiGet<unknown>(API.CONCURRENCY_INGEST));

  const snapshotIngest = useMutation(() => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(snapshot);
    } catch {
      throw new Error("Snapshot must be valid JSON");
    }
    return apiPost<unknown>(API.INGEST_SNAPSHOT, { snapshot: parsed });
  });

  const batchPost = useMutation(() =>
    apiPost<unknown>(API.CONCURRENCY_BATCH_SCORE, {
      ids: ids.split(",").map((s) => s.trim()).filter(Boolean),
    }),
  );

  const concurrencyPost = useMutation(() =>
    apiPost<unknown>(API.CONCURRENCY_INGEST, { source: "snapshot" }),
  );

  return (
    <PageShell
      title="Ingest"
      subtitle="Snapshot ingest, concurrent batch scoring, and concurrency ingest pipelines."
    >
      <div className="card-grid">
        <div className="card">
          <h2>Snapshot Ingest</h2>
          <div className="field">
            <label htmlFor="snapshot">Snapshot JSON</label>
            <textarea
              id="snapshot"
              rows={5}
              value={snapshot}
              onChange={(e) => setSnapshot(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="primary"
            disabled={snapshotIngest.loading}
            onClick={() => snapshotIngest.mutate()}
          >
            {snapshotIngest.loading ? "Ingesting…" : "POST /ingest/snapshot"}
          </button>
          {snapshotIngest.error ? <ErrorBanner message={snapshotIngest.error} /> : null}
          {snapshotIngest.data ? <JsonPanel data={snapshotIngest.data} /> : null}
        </div>

        <div className="card">
          <h2>Batch Score</h2>
          {batchScore.loading && <LoadingBanner />}
          {batchScore.error && <ErrorBanner message={batchScore.error} onRetry={batchScore.refetch} />}
          {!batchScore.loading && batchScore.data ? (
            <JsonPanel title="GET batch-score" data={batchScore.data} />
          ) : null}
          <div className="field">
            <label htmlFor="ids">Set IDs (comma-separated)</label>
            <input id="ids" value={ids} onChange={(e) => setIds(e.target.value)} />
          </div>
          <button
            type="button"
            disabled={batchPost.loading}
            onClick={() => batchPost.mutate()}
          >
            POST batch-score
          </button>
          {batchPost.data ? <JsonPanel data={batchPost.data} /> : null}
        </div>

        <div className="card">
          <h2>Concurrency Ingest</h2>
          {concurrencyIngest.loading && <LoadingBanner />}
          {concurrencyIngest.error && (
            <ErrorBanner message={concurrencyIngest.error} onRetry={concurrencyIngest.refetch} />
          )}
          {!concurrencyIngest.loading && concurrencyIngest.data ? (
            <JsonPanel title="GET ingest" data={concurrencyIngest.data} />
          ) : null}
          <button
            type="button"
            disabled={concurrencyPost.loading}
            onClick={() => concurrencyPost.mutate()}
          >
            POST concurrency ingest
          </button>
          {concurrencyPost.data ? <JsonPanel data={concurrencyPost.data} /> : null}
        </div>
      </div>
    </PageShell>
  );
}
