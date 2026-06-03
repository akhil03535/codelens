export function RepositorySkeleton() {
  return (
    <div className="card p-5 flex items-center gap-4 animate-pulse">
      <div className="w-8 h-8 rounded bg-bg-3" />
      <div className="flex-1 min-w-0 space-y-2">
        <div className="h-4 bg-bg-3 rounded w-1/3" />
        <div className="h-3 bg-bg-3 rounded w-2/3" />
        <div className="h-2 bg-bg-3 rounded w-48" />
      </div>
      <div className="w-8 h-8 rounded bg-bg-3 flex-shrink-0" />
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <RepositorySkeleton key={i} />
      ))}
    </div>
  );
}

export function ProgressBarSkeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      <div className="h-4 bg-bg-3 rounded w-1/4" />
      <div className="h-2 bg-bg-3 rounded" />
    </div>
  );
}
