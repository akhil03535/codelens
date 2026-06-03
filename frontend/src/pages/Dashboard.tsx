import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { extractError, repoApi } from "../services/api";
import { ProcessingProgress } from "../components/ProcessingProgress";

const STATUS_COLORS: Record<string, string> = {
  ready: "bg-success/20 text-success",
  pending: "bg-warning/20 text-warning",
  cloning: "bg-accent/20 text-accent",
  parsing: "bg-accent/20 text-accent",
  embedding: "bg-accent/20 text-accent",
  graphing: "bg-accent/20 text-accent",
  failed: "bg-danger/20 text-danger",
};

const STATUS_PROGRESS: Record<string, number> = {
  pending: 5,
  cloning: 15,
  parsing: 35,
  embedding: 65,
  graphing: 85,
  ready: 100,
  failed: 0,
};

const getProcessingSteps = (status: string) => [
  { name: "Upload & Verify", status: (["cloning", "parsing", "embedding", "graphing", "ready"].includes(status) ? "complete" : status === "pending" ? "active" : "pending") },
  { name: "Clone Repository", status: (["parsing", "embedding", "graphing", "ready"].includes(status) ? "complete" : status === "cloning" ? "active" : "pending") },
  { name: "Parse Code", status: (["embedding", "graphing", "ready"].includes(status) ? "complete" : status === "parsing" ? "active" : "pending") },
  { name: "Generate Embeddings", status: (["graphing", "ready"].includes(status) ? "complete" : status === "embedding" ? "active" : "pending") },
  { name: "Build Dependency Graph", status: (status === "ready" ? "complete" : status === "graphing" ? "active" : "pending") },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadType, setUploadType] = useState<"github" | "zip">("github");
  const [githubUrl, setGithubUrl] = useState("");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [expandedRepo, setExpandedRepo] = useState<string | null>(null);
  const [uploadTimes, setUploadTimes] = useState<Record<string, number>>({});
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = async () => {
    try {
      const data = await repoApi.list();
      setRepos(data.repositories);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    pollRef.current = setInterval(load, 5000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setUploading(true);
    try {
      let repoId: string | undefined;
      if (uploadType === "github") {
        const res = await repoApi.uploadGithub(githubUrl);
        repoId = res.id;
      } else if (zipFile) {
        const res = await repoApi.uploadZip(zipFile);
        repoId = res.id;
      }
      if (repoId) {
        setUploadTimes(t => ({ ...t, [repoId]: Date.now() }));
        setExpandedRepo(repoId);
      }
      setShowUpload(false);
      setGithubUrl(""); setZipFile(null);
      await load();
    } catch (err) {
      setError(extractError(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this repository and all its data?")) return;
    try {
      await repoApi.delete(id);
      setRepos(r => r.filter(x => x.id !== id));
      setExpandedRepo(null);
    } catch (err) {
      alert(extractError(err));
    }
  };

  const processingRepos = repos.filter(r => !["ready", "failed"].includes(r.status));
  const readyRepos = repos.filter(r => r.status === "ready");
  const failedRepos = repos.filter(r => r.status === "failed");

  return (
    <div className="min-h-screen bg-bg">
      {/* Top bar */}
      <header className="border-b border-bg-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold">
          <span className="text-xl">🔭</span> CodeLens AI
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-text-dim">@{user?.username}</span>
          <button onClick={logout} className="btn-ghost text-sm">Sign out</button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-text-dim text-sm mt-1">
              {repos.length} {repos.length === 1 ? "repository" : "repositories"} indexed
            </p>
          </div>
          <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2 px-4 py-2.5">
            <span>+</span> Add Repository
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Repos", value: repos.length, color: "text-accent" },
            { label: "Ready", value: readyRepos.length, color: "text-success" },
            { label: "Processing", value: processingRepos.length, color: "text-warning" },
            { label: "Failed", value: failedRepos.length, color: "text-danger" },
          ].map(s => (
            <div key={s.label} className="card p-4">
              <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-text-dim mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Repository list */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="space-y-3 w-full">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="card p-5 h-20 animate-pulse bg-bg-2" />
              ))}
            </div>
          </div>
        ) : repos.length === 0 ? (
          <div className="card p-16 text-center">
            <div className="text-6xl mb-4">📁</div>
            <h3 className="text-lg font-semibold mb-2">No repositories yet</h3>
            <p className="text-text-dim text-sm mb-6">Add a GitHub repo or upload a ZIP to get started</p>
            <button onClick={() => setShowUpload(true)} className="btn-primary">Add your first repository</button>
          </div>
        ) : (
          <div className="space-y-3">
            {repos.map(repo => (
              <div key={repo.id}>
                <div
                 onClick={() => {
  console.log("CLICKED");
  console.log("repo =", repo);

  if (repo.status === "ready") {
    console.log("navigate:", `/workspace/${repo.id}`);
    navigate(`/workspace/${repo.id}`);
  } else if (expandedRepo === repo.id) {
    setExpandedRepo(null);
  } else {
    setExpandedRepo(repo.id);
  }
}}
                  className={`card p-5 flex items-center gap-4 transition-all ${
                    repo.status === "ready" ? "hover:border-accent/40 cursor-pointer" : ""
                  } ${expandedRepo === repo.id ? "border-accent/50" : ""}`}
                >
                  <div className="text-2xl flex-shrink-0">
                    {repo.source === "github" ? "🐙" : "📦"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-semibold truncate">{repo.name}</span>
                      <span className={`badge text-xs ${STATUS_COLORS[repo.status] || "bg-bg-3 text-text-dim"}`}>
                        {repo.status.charAt(0).toUpperCase() + repo.status.slice(1)}
                      </span>
                      {repo.primary_language && (
                        <span className="badge bg-bg-3 text-text-dim text-xs">{repo.primary_language}</span>
                      )}
                    </div>
                    {repo.status === "ready" ? (
                      <div className="flex items-center gap-4 text-xs text-text-dim">
                        <span>{repo.files_count} files</span>
                        <span>{repo.chunks_count} chunks</span>
                        <span>{repo.functions_count} functions</span>
                        {repo.architecture_type && repo.architecture_type !== "unknown" && (
                          <span className="ml-auto">{repo.architecture_type}</span>
                        )}
                      </div>
                    ) : repo.status === "failed" ? (
                      <p className="text-xs text-danger">{repo.error_message || "Processing failed"}</p>
                    ) : (
                      <div className="mt-1 h-1.5 bg-bg-3 rounded-full overflow-hidden w-32">
                        <div
                          className="h-full bg-gradient-to-r from-accent to-accent/70 rounded-full transition-all duration-300"
                          style={{ width: `${STATUS_PROGRESS[repo.status] || 0}%` }}
                        />
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {repo.status === "ready" && (
                      <span className="text-xs text-text-dim">Open →</span>
                    )}
                    {repo.status !== "ready" && expandedRepo === repo.id && (
                      <span className="text-xs text-text-dim">Details ↓</span>
                    )}
                    <button
                      onClick={e => handleDelete(repo.id, e)}
                      className="text-muted hover:text-danger p-1 rounded transition-colors"
                      title="Delete"
                    >
                      🗑
                    </button>
                  </div>
                </div>
                
                {/* Expanded Progress Details */}
                {expandedRepo === repo.id && repo.status !== "ready" && (
                  <div className="card mt-2 p-5 bg-bg-2/50 border-accent/20">
                    <ProcessingProgress
                      steps={getProcessingSteps(repo.status)}
                      currentProgress={STATUS_PROGRESS[repo.status] || 0}
                      stage={repo.status === "failed" ? "Processing Failed" : `${repo.status.charAt(0).toUpperCase() + repo.status.slice(1)}...`}
                      error={repo.error_message}
                      startTime={uploadTimes[repo.id]}
                      onCancel={() => setExpandedRepo(null)}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="card w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-bold text-lg">Add Repository</h2>
              <button onClick={() => setShowUpload(false)} className="text-muted hover:text-text">✕</button>
            </div>

            <div className="flex gap-2 mb-5">
              {(["github", "zip"] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setUploadType(t)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    uploadType === t ? "bg-accent text-white" : "bg-bg-2 text-text-dim hover:text-text"
                  }`}
                >
                  {t === "github" ? "🐙 GitHub URL" : "📦 ZIP Upload"}
                </button>
              ))}
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              {uploadType === "github" ? (
                <div>
                  <label className="text-sm text-text-dim block mb-1">GitHub Repository URL</label>
                  <input
                    className="input"
                    value={githubUrl}
                    onChange={e => setGithubUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo"
                    required
                  />
                  <p className="text-xs text-text-dim mt-1">Must be a public repository</p>
                </div>
              ) : (
                <div>
                  <label className="text-sm text-text-dim block mb-1">ZIP File (max 100MB)</label>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".zip"
                    onChange={e => setZipFile(e.target.files?.[0] || null)}
                    className="input py-1.5"
                    required
                  />
                  {zipFile && <p className="text-xs text-text-dim mt-1">{zipFile.name}</p>}
                </div>
              )}
              {error && <p className="text-danger text-sm bg-danger/10 px-3 py-2 rounded-lg">{error}</p>}
              <button type="submit" disabled={uploading || (uploadType === "zip" && !zipFile) || (uploadType === "github" && !githubUrl)} className="btn-primary w-full py-2.5">
                {uploading ? "Starting…" : "Start Processing"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
