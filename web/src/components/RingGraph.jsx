import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { riskColor } from "../colors";

export default function RingGraph({ graph, selectedAccount, onNodeClick }) {
  const box = useRef(null);
  const fg = useRef(null);
  const [size, setSize] = useState({ width: 600, height: 500 });

  // Fit the canvas to its container
  useEffect(() => {
    const ro = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height }));
    ro.observe(box.current);
    return () => ro.disconnect();
  }, []);

  // Copy the data (the library mutates links' source/target into objects)
  // and size nodes by PageRank relative to the ring.
  const data = useMemo(() => {
    if (!graph) return { nodes: [], links: [] };
    const prs = graph.nodes.map((n) => n.pageRank ?? 0);
    const lo = Math.min(...prs), hi = Math.max(...prs);
    return {
      nodes: graph.nodes.map((n) => ({
        ...n,
        val: 1 + 8 * (hi > lo ? ((n.pageRank ?? 0) - lo) / (hi - lo) : 0.5),
      })),
      links: graph.links.map((l) => ({ ...l })),
    };
  }, [graph]);

  // Zoom to fit once the layout settles
  useEffect(() => {
    const t = setTimeout(() => fg.current?.zoomToFit(400, 40), 600);
    return () => clearTimeout(t);
  }, [data]);

  return (
    <div ref={box} className="graph">
      {!graph ? (
        <p className="hint">Select a ring to draw it</p>
      ) : (
        <ForceGraph2D
          ref={fg}
          width={size.width}
          height={size.height}
          graphData={data}
          nodeId="id"
          nodeVal="val"
          nodeColor={(n) => riskColor(n.riskScore)}
          nodeLabel={(n) => `<b>${n.id}</b><br/>risk ${n.riskScore?.toFixed(1) ?? "–"}<br/>PageRank ${n.pageRank?.toFixed(2) ?? "–"} (size is relative to this ring)`}
          linkColor={() => "#9a9a9a"}
          linkLabel={(l) => `${l.txCount} txn · $${Math.round(l.totalUsd ?? 0).toLocaleString()}`}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          nodeCanvasObjectMode={() => "after"}
          nodeCanvasObject={(n, ctx, scale) => {
            if (n.id !== selectedAccount) return;
            ctx.beginPath();
            ctx.arc(n.x, n.y, Math.sqrt(n.val) * 4 + 3, 0, 2 * Math.PI);
            ctx.strokeStyle = "#000";
            ctx.lineWidth = 2 / scale;
            ctx.stroke();
          }}
          onNodeClick={(n) => onNodeClick(n.id)}
          cooldownTicks={100}
        />
      )}
    </div>
  );
}
