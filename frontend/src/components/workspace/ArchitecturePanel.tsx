import { useState } from "react";
import { analysisApi, extractError } from "../../services/api";

export default function ArchitecturePanel({ repoId }: { repoId: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [flowFeature, setFlowFeature] = useState("");
  const [flowData, setFlowData] = useState<any>(null);
  const [flowLoading, setFlowLoading] = useState(false);

  const analyze = async () => {
    setLoading(true); setError("");
    try {
      const res = await analysisApi.architecture(repoId);
      setData(res);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  const traceFlow = async () => {
    if (!flowFeature.trim()) return;
    setFlowLoading(true);
    try {
      const res = await analysisApi.traceFlow(repoId, flowFeature);
      setFlowData(res);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setFlowLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Architecture Analysis</h2>
        <button onClick={analyze} disabled={loading} className="btn-primary text-sm">
          {loading ? "Analyzing…" : "Analyze Architecture"}
        </button>
      </div>

      {error && <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 text-danger text-sm">{error}</div>}

      {data && (
        <div className="space-y-5">
          <div className="card p-5">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">🏗️</span>
              <div>
                <div className="font-bold text-base">{data.architecture_type}</div>
                <div className="text-xs text-muted">Architecture Type</div>
              </div>
            </div>
            <p className="text-sm text-text-dim leading-relaxed">{data.summary}</p>
          </div>

          {data.patterns?.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold mb-3 text-sm">Design Patterns Detected</h3>
              <div className="flex flex-wrap gap-2">
                {data.patterns.map((p: string) => (
                  <span key={p} className="badge bg-accent/15 text-accent">{p}</span>
                ))}
              </div>
            </div>
          )}

          {data.layers?.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold mb-3 text-sm">Layers</h3>
              <div className="space-y-3">
                {data.layers.map((l: any, i: number) => (
                  <div key={i} className="border-l-2 border-accent pl-4">
                    <div className="font-medium text-sm">{l.name}</div>
                    <div className="text-xs text-text-dim mt-0.5">{l.description}</div>
                    {l.files?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {l.files.slice(0, 5).map((f: string) => (
                          <span key={f} className="text-xs font-mono text-muted bg-bg-2 px-2 py-0.5 rounded">{f}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.entry_points?.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold mb-3 text-sm">Entry Points</h3>
              <div className="space-y-1">
                {data.entry_points.map((ep: string) => (
                  <div key={ep} className="text-sm font-mono text-accent">{ep}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Flow tracer */}
      <div className="card p-5">
        <h3 className="font-bold mb-3">Flow Tracer</h3>
        <p className="text-sm text-text-dim mb-3">Trace how a feature works through the entire codebase</p>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            value={flowFeature}
            onChange={e => setFlowFeature(e.target.value)}
            onKeyDown={e => e.key === "Enter" && traceFlow()}
            placeholder='e.g. "how does user authentication work?"'
          />
          <button onClick={traceFlow} disabled={flowLoading || !flowFeature.trim()} className="btn-primary text-sm px-4">
            {flowLoading ? "Tracing…" : "Trace"}
          </button>
        </div>

        {flowData && (
          <div className="mt-5 space-y-3">
            <p className="text-sm text-text-dim">{flowData.summary}</p>
            <div className="space-y-2">
              {flowData.steps?.map((step: any) => (
                <div key={step.step} className="flex gap-4 bg-bg-2 rounded-lg p-4">
                  <div className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-bold flex-shrink-0">
                    {step.step}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{step.description}</div>
                    {step.file && <div className="text-xs font-mono text-accent mt-1">{step.file}</div>}
                    {step.function && <div className="text-xs text-muted mt-0.5">Function: {step.function}</div>}
                    {step.details && <div className="text-xs text-text-dim mt-1">{step.details}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
