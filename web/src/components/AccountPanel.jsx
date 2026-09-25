import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { api } from "../api";

const PARTS = [
  ["cycle", "Cycle", "#d62728"],
  ["crossCommunity", "Cross-community", "#ff7f0e"],
  ["pageRank", "PageRank", "#1f77b4"],
  ["velocity", "Velocity", "#2ca02c"],
];

export default function AccountPanel({ accountId, onSelectRing }) {
  const [acc, setAcc] = useState(null);
  const [rings, setRings] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!accountId) return;
    let ignore = false;
    setError(null);
    setAcc(null);
    Promise.all([api.account(accountId), api.accountRings(accountId)])
      .then(([a, r]) => { if (!ignore) { setAcc(a); setRings(r.rings); } })
      .catch((e) => !ignore && setError(e.message));
    return () => { ignore = true; };
  }, [accountId]);

  if (!accountId) return <section className="panel"><p className="hint">Click an account in the graph</p></section>;
  if (error) return <section className="panel"><p className="error">{error}</p></section>;
  if (!acc) return <section className="panel"><p>Loading…</p></section>;

  const risk = acc.risk ?? {};
  const bar = [{ name: "risk", ...Object.fromEntries(PARTS.map(([k]) => [k, risk[k] ?? 0])) }];

  return (
    <section className="panel">
      <h2>{acc.accountId}</h2>

      <p className="score">{risk.score?.toFixed(1) ?? "–"} <small>/ 100</small></p>
      <p className="formula">
        = {PARTS.map(([k, label]) => `${(risk[k] ?? 0).toFixed(1)} ${label.toLowerCase()}`).join(" + ")}
      </p>

      <ResponsiveContainer width="100%" height={90}>
        <BarChart data={bar} layout="vertical" margin={{ left: 0, right: 10 }}>
          <XAxis type="number" domain={[0, 100]} />
          <YAxis type="category" dataKey="name" hide />
          <Tooltip formatter={(v) => v.toFixed(1)} />
          <Legend />
          {PARTS.map(([k, label, color]) => (
            <Bar key={k} isAnimationActive={false} dataKey={k} name={label} stackId="risk" fill={color} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <dl>
        <dt>PageRank</dt><dd>{acc.graph?.pageRank?.toFixed(4)}</dd>
        <dt>Community</dt><dd>{acc.graph?.communityId}</dd>
        <dt>In a cycle</dt><dd>{acc.graph?.inCycle ? "Yes" : "No"}</dd>
        <dt>Sent / received</dt><dd>{acc.sentCount} / {acc.receivedCount}</dd>
        <dt>Review status</dt><dd>{acc.reviewStatus}</dd>
      </dl>

      <h3>Rings containing this account ({rings.length})</h3>
      <ul className="ring-links">
        {rings.map((r) => (
          <li key={r.detectionId}>
            <button onClick={() => onSelectRing(r.detectionId)}>
              #{r.detectionId} · {r.method} · {r.size} accounts
            </button>
          </li>
        ))}
      </ul>

      {/* Kept visually separate: the dataset's labels, which a real investigator would not have. */}
      {acc.label && (
        <p className="ground-truth">
          Ground truth (evaluation only): {acc.label.launderingInvolved ? "involved in laundering" : "no laundering"}
          {acc.label.patternTypes?.length ? ` · patterns: ${acc.label.patternTypes.join(", ")}` : ""}
        </p>
      )}
    </section>
  );
}
