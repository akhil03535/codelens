import { useState } from "react";
import { analysisApi, extractError } from "../../services/api";

const EXAMPLE_TRACE = `Traceback (most recent call last):
  File "app/api/routes.py", line 45, in create_user
    user = await user_service.create(db, request)
  File "app/services/user_service.py", line 23, in create
    result = await db.execute(stmt)
  File "sqlalchemy/ext/asyncio/session.py", line 218, in execute
    return await greenlet_spawn(...)
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: users.email`;

export default function BugPanel({ repoId }: { repoId: string }) {
  const [stackTrace, setStackTrace] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const investigate = async () => {
    if (!stackTrace.trim()) return;
    setLoading(true); setError("");
    try {
      const data = await analysisApi.investigateBug(repoId, stackTrace, context);
      setResult(data);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-5">
      <h2 className="font-bold text-lg">AI Bug Investigator</h2>
      <p className="text-text-dim text-sm">
        Paste a stack trace or error message. The AI will find related code,
        identify the root cause, and suggest fixes based on your actual codebase.
      </p>

      <div className="space-y-4">
        <div>
          <label className="text-sm text-text-dim block mb-1.5">Stack trace / Error message</label>
          <textarea
            className="input font-mono text-xs resize-none"
            rows={8}
            value={stackTrace}
            onChange={e => setStackTrace(e.target.value)}
            placeholder={EXAMPLE_TRACE}
          />
        </div>
        <div>
          <label className="text-sm text-text-dim block mb-1.5">Additional context (optional)</label>
          <textarea
            className="input text-sm resize-none"
            rows={2}
            value={context}
            onChange={e => setContext(e.target.value)}
            placeholder="What were you trying to do? What changed recently?"
          />
        </div>

        {error && <div className="bg-danger/10 border border-danger/30 rounded-lg p-3 text-danger text-sm">{error}</div>}

        <button onClick={investigate} disabled={loading || !stackTrace.trim()} className="btn-primary text-sm px-6 py-2.5">
          {loading ? "Investigating…" : "🔍 Investigate Bug"}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          {/* Probable cause */}
          <div className="card p-5 border-danger/30">
            <div className="flex items-center gap-2 mb-2">
              <span>🎯</span>
              <h3 className="font-semibold">Probable Cause</h3>
            </div>
            <p className="text-sm text-text-dim leading-relaxed">{result.probable_cause}</p>
          </div>

          {/* Root cause analysis */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-2">
              <span>🔬</span>
              <h3 className="font-semibold">Root Cause Analysis</h3>
            </div>
            <p className="text-sm text-text-dim leading-relaxed">{result.root_cause_analysis}</p>
          </div>

          {/* Suggested fixes */}
          {result.suggested_fixes?.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <span>🛠️</span>
                <h3 className="font-semibold">Suggested Fixes</h3>
              </div>
              <ol className="space-y-2">
                {result.suggested_fixes.map((fix: string, i: number) => (
                  <li key={i} className="flex gap-3 text-sm text-text-dim">
                    <span className="w-5 h-5 rounded-full bg-success/20 text-success text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-bold">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{fix}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Related files */}
          {result.related_files?.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <span>📁</span>
                <h3 className="font-semibold">Related Code ({result.related_files.length})</h3>
              </div>
              <div className="space-y-3">
                {result.related_files.map((f: any, i: number) => (
                  <div key={i} className="bg-bg-2 border border-bg-border rounded-lg overflow-hidden">
                    <div className="px-3 py-2 border-b border-bg-border flex items-center justify-between">
                      <span className="text-xs font-mono text-accent">{f.file_path}</span>
                      <span className="text-xs text-muted">{(f.score * 100).toFixed(0)}% relevance</span>
                    </div>
                    <pre className="text-xs font-mono text-muted p-3 max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                      {f.content}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
