import { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  Background, Controls, MiniMap,
  Node, Edge, useNodesState, useEdgesState, MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { analysisApi, extractError } from "../../services/api";

const LANG_COLORS: Record<string, string> = {
  python: "#3572A5",
  javascript: "#f1e05a",
  typescript: "#2b7489",
  java: "#b07219",
  unknown: "#6b7280",
};

function buildGraph(data: any): { nodes: Node[]; edges: Edge[] } {
  const nodeMap = new Map<string, Node>();
  const edgeSet = new Set<string>();
  const edges: Edge[] = [];

  (data.nodes || []).forEach((n: any, i: number) => {
    const color = LANG_COLORS[n.language || "unknown"] || "#6b7280";
    const label = n.label || n.id.split("/").pop() || n.id;
    const x = Math.cos((i / data.nodes.length) * 2 * Math.PI) * 300 + 400;
    const y = Math.sin((i / data.nodes.length) * 2 * Math.PI) * 200 + 300;

    nodeMap.set(n.id, {
      id: n.id,
      position: { x, y },
      data: { label },
      style: {
        background: "#141c2e",
        border: `1px solid ${color}`,
        borderRadius: 8,
        color: "#e2e8f0",
        fontSize: 11,
        padding: "6px 10px",
        fontFamily: "JetBrains Mono, monospace",
        maxWidth: 160,
      },
    });
  });

  (data.edges || []).forEach((e: any, i: number) => {
    const key = `${e.source}->${e.target}`;
    if (edgeSet.has(key) || !nodeMap.has(e.source) || !nodeMap.has(e.target)) return;
    edgeSet.add(key);
    edges.push({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      label: e.relationship,
      style: { stroke: "#1e2d4a", strokeWidth: 1 },
      labelStyle: { fontSize: 9, fill: "#64748b" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#1e2d4a" },
    });
  });

  return { nodes: Array.from(nodeMap.values()), edges };
}

export default function GraphPanel({ repoId }: { repoId: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stats, setStats] = useState<{ nodes: number; edges: number } | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const data = await analysisApi.dependencyGraph(repoId);
      const { nodes: n, edges: e } = buildGraph(data);
      setNodes(n);
      setEdges(e);
      setStats({ nodes: n.length, edges: e.length });
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-bg-border flex items-center gap-4">
        <h2 className="font-bold">Dependency Graph</h2>
        {stats && (
          <span className="text-xs text-muted">{stats.nodes} files · {stats.edges} relationships</span>
        )}
        <button onClick={load} disabled={loading} className="ml-auto btn-ghost text-sm">
          {loading ? "Loading…" : "↺ Refresh"}
        </button>
      </div>

      {error && (
        <div className="m-4 bg-danger/10 border border-danger/30 rounded-lg p-3 text-danger text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            style={{ background: "#0a0e1a" }}
          >
            <Background color="#1a2540" gap={20} />
            <Controls style={{ background: "#0f1523", border: "1px solid #1e2d4a" }} />
            <MiniMap
              style={{ background: "#0f1523", border: "1px solid #1e2d4a" }}
              nodeColor="#1a2540"
            />
          </ReactFlow>
        </div>
      )}
    </div>
  );
}
