import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { ErrorBanner, LoadingBanner, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useApi } from "../hooks/useApi";

type Exhibition = Record<string, unknown>;

export function Catalog() {
  const weave = useApi(() => apiGet<Exhibition[]>(API.WEAVE));
  const tags = useApi(() => apiGet<unknown>(API.TAGS));
  const spectrum = useApi(() => apiGet<unknown>(API.FORMAT_SPECTRUM));

  const loading = weave.loading || tags.loading || spectrum.loading;
  const error = weave.error || tags.error || spectrum.error;
  const exhibitions = Array.isArray(weave.data) ? weave.data : [];

  return (
    <PageShell
      title="Exhibition Catalog"
      subtitle="Browse the exhibition weave — curated sets with tags and format spectrum."
      actions={<button type="button" onClick={() => weave.refetch()}>Refresh weave</button>}
    >
      {loading && <LoadingBanner />}
      {error && !loading && <ErrorBanner message={error} onRetry={weave.refetch} />}
      {!loading && !error && (
        <>
          <div className="card-grid" style={{ marginBottom: "1.5rem" }}>
            <div className="card">
              <h2>Tags</h2>
              <pre className="code-block">{JSON.stringify(tags.data, null, 2)}</pre>
            </div>
            <div className="card">
              <h2>Format Spectrum</h2>
              <pre className="code-block">{JSON.stringify(spectrum.data, null, 2)}</pre>
            </div>
          </div>
          <div className="card">
            <h2>Exhibition Weave ({exhibitions.length})</h2>
            {exhibitions.length === 0 ? (
              <p className="empty">No exhibitions in weave.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Score</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {exhibitions.map((ex) => {
                    const id = String(ex.id ?? ex.set_id ?? ex.exhibition_id ?? "");
                    return (
                      <tr key={id}>
                        <td><code>{id}</code></td>
                        <td>{String(ex.title ?? ex.name ?? "—")}</td>
                        <td>{String(ex.vitrine_score ?? ex.score ?? "—")}</td>
                        <td>
                          <Link to={`/exhibitions/${id}`}>View detail →</Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </PageShell>
  );
}
