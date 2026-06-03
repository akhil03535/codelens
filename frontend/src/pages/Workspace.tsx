import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { repoApi } from "../services/api";
import ChatPanel from "../components/workspace/ChatPanel";
import ArchitecturePanel from "../components/workspace/ArchitecturePanel";
import GraphPanel from "../components/workspace/GraphPanel";
import InsightsPanel from "../components/workspace/InsightsPanel";
import SearchPanel from "../components/workspace/SearchPanel";
import BugPanel from "../components/workspace/BugPanel";
import DocsPanel from "../components/workspace/DocsPanel";

type Tab = "chat" | "architecture" | "graph" | "insights" | "search" | "bug" | "docs";

const NAV: { id: Tab; icon: string; label: string }[] = [
  { id: "chat", icon: "💬", label: "Chat" },
  { id: "architecture", icon: "🏗️", label: "Architecture" },
  { id: "graph", icon: "🕸️", label: "Dependencies" },
  { id: "search", icon: "🔍", label: "Search" },
  { id: "bug", icon: "🐛", label: "Debug" },
  { id: "docs", icon: "📄", label: "Docs" },
  { id: "insights", icon: "📊", label: "Insights" },
];

export default function Workspace() {
  const { repoId } = useParams<{ repoId: string }>();
  const [repo, setRepo] = useState<any>(null);
  const [tab, setTab] = useState<Tab>("chat");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!repoId) return;
    repoApi.get(repoId).then(setRepo).finally(() => setLoading(false));
  }, [repoId]);

  if (loading) return (
    <div className="h-screen flex items-center justify-center bg-bg">
      <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!repo) return (
    <div className="h-screen flex items-center justify-center bg-bg text-text-dim">
      Repository not found. <Link to="/dashboard" className="text-accent ml-2">Go back</Link>
    </div>
  );

  return (
    <div className="h-screen bg-bg flex flex-col">
      {/* Top bar */}
      <header className="border-b border-bg-border px-4 py-3 flex items-center gap-4 flex-shrink-0">
        <Link to="/dashboard" className="text-text-dim hover:text-text text-sm">← Dashboard</Link>
        <div className="h-4 w-px bg-bg-border" />
        <div className="flex items-center gap-2">
          <span>{repo.source === "github" ? "🐙" : "📦"}</span>
          <span className="font-semibold text-sm truncate max-w-xs">{repo.name}</span>
          <span className="badge bg-success/20 text-success text-xs">ready</span>
        </div>
        <div className="ml-auto flex items-center gap-4 text-xs text-muted">
          <span>{repo.files_count} files</span>
          <span>{repo.functions_count} functions</span>
          <span>{repo.primary_language}</span>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-48 border-r border-bg-border flex flex-col flex-shrink-0 bg-bg-1">
          <nav className="p-2 space-y-0.5 flex-1">
            {NAV.map(n => (
              <button
                key={n.id}
                onClick={() => setTab(n.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors text-left ${
                  tab === n.id
                    ? "bg-accent/15 text-accent"
                    : "text-text-dim hover:text-text hover:bg-bg-2"
                }`}
              >
                <span>{n.icon}</span>
                <span>{n.label}</span>
              </button>
            ))}
          </nav>
          <div className="p-3 border-t border-bg-border">
            <Link to="/" className="flex items-center gap-2 text-xs text-muted">
              <span>🔭</span> CodeLens AI
            </Link>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 overflow-hidden">
          {tab === "chat" && <ChatPanel repoId={repoId!} />}
          {tab === "architecture" && <ArchitecturePanel repoId={repoId!} />}
          {tab === "graph" && <GraphPanel repoId={repoId!} />}
          {tab === "search" && <SearchPanel repoId={repoId!} />}
          {tab === "bug" && <BugPanel repoId={repoId!} />}
          {tab === "docs" && <DocsPanel repoId={repoId!} />}
          {tab === "insights" && <InsightsPanel repo={repo} />}
        </main>
      </div>
    </div>
  );
}
