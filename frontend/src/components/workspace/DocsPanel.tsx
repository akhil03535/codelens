import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { analysisApi, extractError } from "../../services/api";

export default function DocsPanel({ repoId }: { repoId: string }) {
  const [tab, setTab] = useState<"readme" | "onboarding">("readme");
  const [readme, setReadme] = useState("");
  const [onboarding, setOnboarding] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateDocs = async () => {
    setLoading(true); setError("");
    try {
      if (tab === "readme") {
        const data = await analysisApi.documentation(repoId);
        setReadme(data.documentation);
      } else {
        const data = await analysisApi.onboarding(repoId);
        setOnboarding(data);
      }
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-bg-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold">Documentation Generator</h2>
          <button onClick={generateDocs} disabled={loading} className="btn-primary text-sm">
            {loading ? "Generating…" : "Generate"}
          </button>
        </div>
        <div className="flex gap-2">
          {(["readme", "onboarding"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`text-sm px-4 py-1.5 rounded-lg transition-colors ${
                tab === t ? "bg-accent text-white" : "bg-bg-2 text-text-dim hover:text-text"
              }`}
            >
              {t === "readme" ? "📄 README" : "🧭 Onboarding Guide"}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="m-4 bg-danger/10 border border-danger/30 rounded-lg p-3 text-danger text-sm">{error}</div>}

      <div className="flex-1 overflow-y-auto">
        {tab === "readme" && readme && (
          <div className="relative">
            <button
              onClick={() => copyToClipboard(readme)}
              className="absolute top-4 right-4 btn-ghost text-xs border border-bg-border"
            >
              Copy Markdown
            </button>
            <div className="p-6 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{readme}</ReactMarkdown>
            </div>
          </div>
        )}

        {tab === "onboarding" && onboarding && (
          <div className="p-6 space-y-5">
            {onboarding.overview && (
              <div className="card p-5">
                <h3 className="font-semibold mb-2">Overview</h3>
                <p className="text-sm text-text-dim leading-relaxed">{onboarding.overview}</p>
              </div>
            )}

            {onboarding.learning_roadmap?.length > 0 && (
              <div className="card p-5">
                <h3 className="font-semibold mb-4">Learning Roadmap</h3>
                <div className="space-y-4">
                  {onboarding.learning_roadmap.map((step: any) => (
                    <div key={step.step} className="flex gap-4">
                      <div className="w-8 h-8 rounded-full bg-accent/20 text-accent text-sm font-bold flex items-center justify-center flex-shrink-0">
                        {step.step}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm">{step.title}</div>
                        <p className="text-xs text-text-dim mt-1 leading-relaxed">{step.description}</p>
                        {step.files_to_read?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {step.files_to_read.map((f: string) => (
                              <span key={f} className="text-xs font-mono bg-bg-2 border border-bg-border px-2 py-0.5 rounded text-accent">{f}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {onboarding.important_files?.length > 0 && (
              <div className="card p-5">
                <h3 className="font-semibold mb-3">Important Files</h3>
                <div className="space-y-2">
                  {onboarding.important_files.map((f: any) => (
                    <div key={f.path} className="flex gap-3">
                      <span className="text-xs font-mono text-accent min-w-0 truncate flex-1">{f.path}</span>
                      <span className="text-xs text-text-dim text-right">{f.purpose}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {onboarding.architecture_walkthrough && (
              <div className="card p-5">
                <h3 className="font-semibold mb-2">Architecture Walkthrough</h3>
                <p className="text-sm text-text-dim leading-relaxed">{onboarding.architecture_walkthrough}</p>
              </div>
            )}

            {onboarding.setup_notes && (
              <div className="card p-5">
                <h3 className="font-semibold mb-2">Setup Notes</h3>
                <p className="text-sm text-text-dim leading-relaxed">{onboarding.setup_notes}</p>
              </div>
            )}
          </div>
        )}

        {!readme && !onboarding && !loading && (
          <div className="flex items-center justify-center h-full text-text-dim text-sm">
            Click "Generate" to create {tab === "readme" ? "a README" : "an onboarding guide"} from your codebase
          </div>
        )}
      </div>
    </div>
  );
}
