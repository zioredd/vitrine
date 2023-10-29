import { useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, LoadingBanner, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi, useMutation } from "../hooks/useApi";

type QueueTab = "jobs" | "schedule" | "dead-letter";

export function Queue() {
  const [tab, setTab] = useState<QueueTab>("jobs");
  const [jobId, setJobId] = useState("job-001");

  const jobs = useApi(() => apiGet<unknown>(API.QUEUE_JOBS), [tab === "jobs"]);
  const schedule = useApi(() => apiGet<unknown>(API.QUEUE_SCHEDULE), [tab === "schedule"]);
  const deadLetter = useApi(() => apiGet<unknown>(API.QUEUE_DEAD_LETTER), [tab === "dead-letter"]);

  const replay = useMutation((id: string) =>
    apiPost<unknown>(API.QUEUE_REPLAY, { job_id: id }),
  );

  const active = tab === "jobs" ? jobs : tab === "schedule" ? schedule : deadLetter;

  return (
    <PageShell
      title="Job Queue"
      subtitle="Monitor jobs, cron schedules, dead-letter queue, and replay failed work."
    >
      <div className="tabs">
        {(["jobs", "schedule", "dead-letter"] as QueueTab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "dead-letter" ? "Dead Letter" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {active.loading && <LoadingBanner />}
      {active.error && !active.loading && (
        <ErrorBanner message={active.error} onRetry={active.refetch} />
      )}
      {!active.loading && !active.error && (
        <JsonPanel title={`Queue — ${tab}`} data={active.data} />
      )}

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <h2>Replay Job</h2>
        <div className="field" style={{ maxWidth: 320 }}>
          <label htmlFor="job-id">Job ID</label>
          <input id="job-id" value={jobId} onChange={(e) => setJobId(e.target.value)} />
        </div>
        <div className="actions">
          <button
            type="button"
            className="primary"
            disabled={replay.loading}
            onClick={() => replay.mutate(jobId)}
          >
            {replay.loading ? "Replaying…" : "Replay"}
          </button>
        </div>
        {replay.error ? <ErrorBanner message={replay.error} /> : null}
        {replay.data ? <JsonPanel title="Replay Result" data={replay.data} /> : null}
      </div>
    </PageShell>
  );
}
