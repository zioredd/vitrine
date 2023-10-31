import { useState } from "react";
import { apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useMutation } from "../hooks/useApi";

export function SyncRebalance() {
  const [remote, setRemote] = useState('{"version": 1}');
  const [routeBody, setRouteBody] = useState(
    '{"source": "a", "target": "b", "graph": {}}',
  );

  const reconcile = useMutation(() => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(remote);
    } catch {
      throw new Error("Remote state must be valid JSON");
    }
    return apiPost<unknown>(API.SYNC_RECONCILE, { remote: parsed });
  });

  const rebalance = useMutation(() => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(routeBody);
    } catch {
      throw new Error("Route body must be valid JSON");
    }
    return apiPost<unknown>(API.REBALANCE_ROUTE, parsed);
  });

  return (
    <PageShell
      title="Sync & Rebalance"
      subtitle="Merkle reconciliation for distributed state and min-fee route rebalancing."
    >
      <div className="card-grid">
        <div className="card">
          <h2>Reconcile</h2>
          <div className="field">
            <label htmlFor="remote">Remote state (JSON)</label>
            <textarea
              id="remote"
              rows={5}
              value={remote}
              onChange={(e) => setRemote(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="primary"
            disabled={reconcile.loading}
            onClick={() => reconcile.mutate()}
          >
            {reconcile.loading ? "Reconciling…" : "POST /sync/reconcile"}
          </button>
          {reconcile.error ? <ErrorBanner message={reconcile.error} /> : null}
          {reconcile.data ? <JsonPanel data={reconcile.data} /> : null}
        </div>

        <div className="card">
          <h2>Rebalance Route</h2>
          <div className="field">
            <label htmlFor="route">Route request (JSON)</label>
            <textarea
              id="route"
              rows={5}
              value={routeBody}
              onChange={(e) => setRouteBody(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="primary"
            disabled={rebalance.loading}
            onClick={() => rebalance.mutate()}
          >
            {rebalance.loading ? "Routing…" : "POST /rebalance/route"}
          </button>
          {rebalance.error ? <ErrorBanner message={rebalance.error} /> : null}
          {rebalance.data ? <JsonPanel data={rebalance.data} /> : null}
        </div>
      </div>
    </PageShell>
  );
}
