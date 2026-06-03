import { useState } from "react";
import { analysisApi, extractError } from "../../services/api";

const EXAMPLE_QUERIES = [
  "authentication logic",
  "database connection",
  "API route handlers",
  "error handling middleware",
  "JWT token validation",
  "password hashing",
];

export default function SearchPanel({ repoId }: { repoId: string }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [selectedResult, setSelectedResult] = useState<any>(null);

  const search = async (q?: string) => {
    const text = (q ?? query).trim();
    if (!text) return;
    setLoading(true); setError(""); setSearched(true);
    try {
      const data = await analysisApi.search(repoId, text);
      setResults(data.results);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex">
      {/* Left: search + results */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-4 border-b border-bg-border">
          <h2 className="font-bold mb-3">Semantic Code Search</h2>
          <div className="flex gap-2">
            <input
              className="input flex-1"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && search()}
              placeholder="Search by concept, not keyword (e.g. 'JWT authentication')"
            />
            <button onClick={() => search()} disabled={loading || !query.trim()} className="btn-primary px-4 text-sm">
              {loading ? "…" : "Search"}
            </button>
          </div>

          {/* Example queries */}
          {!searched && (
            <div className="flex flex-wrap gap-2 mt-3">
              {EXAMPLE_QUERIES.map(q => (
                <button
                  key={q}
                  onClick={() => { setQuery(q); search(q); }}
                  className="text-xs px-3 py-1 bg-bg-2 border border-bg-border hover:border-accent/40 rounded-full text-text-dim hover:text-text transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
        </div>

        {error && <div className="m-4 bg-danger/10 border border-danger/30 rounded-lg p-3 text-danger text-sm">{error}</div>}

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!loading && searched && results.length === 0 && (
            <div className="text-center py-12 text-text-dim text-sm">
              No relevant code found for this query
            </div>
          )}

          {results.map((r, i) => (
            <button
              key={i}
              onClick={() => setSelectedResult(r)}
              className={`w-full text-left card p-4 hover:border-accent/40 transition-colors ${
                selectedResult === r ? "border-accent/40" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <span className="text-sm font-mono text-accent truncate">{r.file_path}</span>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {r.chunk_type && (
                    <span className="badge bg-bg-3 text-text-dim">{r.chunk_type}</span>
                  )}
                  {r.function_name && (
                    <span className="badge bg-accent/10 text-accent font-mono">{r.function_name}</span>
                  )}
                  <span className="text-xs text-muted">{(r.score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <pre className="text-xs font-mono text-muted leading-relaxed overflow-hidden max-h-16 text-ellipsis whitespace-pre-wrap">
                {r.content.slice(0, 200)}
              </pre>
            </button>
          ))}
        </div>
      </div>

      {/* Right: code viewer */}
      {selectedResult && (
        <div className="w-[480px] border-l border-bg-border flex flex-col flex-shrink-0 bg-bg-1">
          <div className="p-3 border-b border-bg-border flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-accent">{selectedResult.file_path}</span>
              {selectedResult.function_name && (
                <span className="text-xs text-muted ml-2">→ {selectedResult.function_name}</span>
              )}
            </div>
            <button onClick={() => setSelectedResult(null)} className="text-muted hover:text-text">✕</button>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <pre className="text-xs font-mono text-text leading-relaxed whitespace-pre-wrap">
              {selectedResult.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
