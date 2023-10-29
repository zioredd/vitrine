import { useState } from "react";
import { apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useMutation } from "../hooks/useApi";

export function Pipeline() {
  const [stages, setStages] = useState("normalize,diff");
  const [payload, setPayload] = useState('{"items": []}');

  const run = useMutation(() => {
    let parsed: unknown = {};
    try {
      parsed = JSON.parse(payload);
    } catch {
      throw new Error("Payload must be valid JSON");
    }
    return apiPost<unknown>(API.PIPELINE_RUN, {
      stages: stages.split(",").map((s) => s.trim()).filter(Boolean),
      payload: parsed,
    });
  });

  return (
    <PageShell
      title="Pipeline Runner"
      subtitle="Execute multi-stage decode, normalize, and diff pipelines against exhibition payloads."
    >
      <div className="card">
        <div className="field">
          <label htmlFor="stages">Stages (comma-separated)</label>
          <input id="stages" value={stages} onChange={(e) => setStages(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="payload">Payload (JSON)</label>
          <textarea
            id="payload"
            rows={6}
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
          />
        </div>
        <div className="actions">
          <button type="button" className="primary" disabled={run.loading} onClick={() => run.mutate()}>
            {run.loading ? "Running…" : "Run Pipeline"}
          </button>
        </div>
        {run.error ? <ErrorBanner message={run.error} /> : null}
        {run.data ? <JsonPanel title="Pipeline Result" data={run.data} /> : null}
      </div>
    </PageShell>
  );
}
