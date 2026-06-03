const LANG_COLORS: Record<string, string> = {
  python: "#3572A5", javascript: "#f1e05a", typescript: "#2b7489",
  java: "#b07219", unknown: "#6b7280",
};

export default function InsightsPanel({ repo }: { repo: any }) {
  const languages: Record<string, number> = repo.languages || {};
  const totalFiles = Object.values(languages).reduce((a: number, b) => a + (b as number), 0) || 1;

  const stats = [
    { label: "Files Processed", value: repo.files_count, icon: "📁" },
    { label: "Code Chunks", value: repo.chunks_count, icon: "🧩" },
    { label: "Functions", value: repo.functions_count, icon: "⚡" },
    { label: "Classes", value: repo.classes_count, icon: "🏛️" },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <h2 className="font-bold text-lg">Repository Insights</h2>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4">
        {stats.map(s => (
          <div key={s.label} className="card p-5">
            <div className="flex items-center gap-3 mb-1">
              <span className="text-xl">{s.icon}</span>
              <div>
                <div className="text-2xl font-bold text-accent">{s.value?.toLocaleString() ?? 0}</div>
                <div className="text-xs text-muted">{s.label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Architecture */}
      {repo.architecture_type && repo.architecture_type !== "unknown" && (
        <div className="card p-5">
          <h3 className="font-semibold mb-2">Architecture</h3>
          <div className="flex items-center gap-3 mb-3">
            <span className="badge bg-accent/15 text-accent text-sm">{repo.architecture_type}</span>
          </div>
          {repo.architecture_summary && (
            <p className="text-sm text-text-dim leading-relaxed">{repo.architecture_summary}</p>
          )}
        </div>
      )}

      {/* Language breakdown */}
      {Object.keys(languages).length > 0 && (
        <div className="card p-5">
          <h3 className="font-semibold mb-4">Language Distribution</h3>
          <div className="space-y-3">
            {Object.entries(languages)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([lang, count]) => {
                const pct = Math.round(((count as number) / totalFiles) * 100);
                const color = LANG_COLORS[lang] || "#6b7280";
                return (
                  <div key={lang}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm capitalize">{lang}</span>
                      <span className="text-xs text-muted">{count} files ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-bg-3 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Color bar */}
          <div className="mt-4 h-3 rounded-full overflow-hidden flex">
            {Object.entries(languages)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([lang, count]) => {
                const pct = ((count as number) / totalFiles) * 100;
                return (
                  <div
                    key={lang}
                    style={{ width: `${pct}%`, backgroundColor: LANG_COLORS[lang] || "#6b7280" }}
                    title={`${lang}: ${pct.toFixed(1)}%`}
                  />
                );
              })}
          </div>
        </div>
      )}

      {/* Repo info */}
      <div className="card p-5">
        <h3 className="font-semibold mb-3">Repository Info</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-dim">Name</span>
            <span className="font-mono">{repo.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-dim">Source</span>
            <span className="capitalize">{repo.source}</span>
          </div>
          {repo.github_url && (
            <div className="flex justify-between">
              <span className="text-text-dim">URL</span>
              <a href={repo.github_url} target="_blank" rel="noreferrer"
                className="text-accent hover:underline text-xs truncate max-w-xs">
                {repo.github_url}
              </a>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-text-dim">Primary Language</span>
            <span className="capitalize">{repo.primary_language || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-dim">Indexed</span>
            <span>{new Date(repo.created_at).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-dim">Status</span>
            <span className="badge bg-success/20 text-success">{repo.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
