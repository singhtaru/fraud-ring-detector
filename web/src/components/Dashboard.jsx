import { Fragment, useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from "recharts";
import { api } from "../api";

const pct = (v) => `${(v * 100).toFixed(0)}%`;
const WEIGHT_LABELS = { cycle: "Cycle", cross_community: "Cross-community", pagerank: "PageRank", velocity: "Velocity" };

export default function Dashboard() {
  const [ev, setEv] = useState(null);
  const [hist, setHist] = useState([]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.evaluation(), api.riskHistogram(), api.latestRun()])
      .then(([e, h, r]) => { setEv(e); setHist(h); setRun(r); })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!ev) return <p className="hint">Loading…</p>;

  const types = Object.entries(ev.labelledByType).map(([type, n]) => ({ type, n }));

  return (
    <div className="dashboard">
      <section className="panel">
        <h2>Precision and recall by method (Jaccard ≥ {ev.jaccardThreshold})</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={ev.methods}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="method" interval={0} angle={-15} textAnchor="end" height={60} />
            <YAxis domain={[0, 1]} tickFormatter={pct} />
            <Tooltip formatter={pct} />
            <Legend />
            <Bar isAnimationActive={false} dataKey="precision" fill="#1f77b4" />
            <Bar isAnimationActive={false} dataKey="recall" fill="#ff7f0e" />
          </BarChart>
        </ResponsiveContainer>
        <table>
          <thead>
            <tr><th>Method</th><th>Detections</th><th>Matched</th><th>Recalled</th><th>F1</th><th>Detections per pattern found</th></tr>
          </thead>
          <tbody>
            {ev.methods.map((m) => (
              <tr key={m.method}>
                <td>{m.method}</td><td>{m.detections.toLocaleString()}</td><td>{m.matched.toLocaleString()}</td>
                <td>{m.targetRecalled}/{m.targetLabelled}</td><td>{m.f1.toFixed(3)}</td>
                <td>{m.detectionsPerPatternFound?.toLocaleString() ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Risk score distribution (all accounts, log scale)</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={hist}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bandStart" />
            <YAxis scale="log" domain={[1, "auto"]} allowDataOverflow />
            <Tooltip />
            <Bar isAnimationActive={false} dataKey="accounts" fill="#7f7f7f" />
          </BarChart>
        </ResponsiveContainer>
        <p className="hint small">The second hump from 35 up is cycle membership, which adds 35 points.</p>
      </section>

      <section className="panel">
        <h2>Labelled patterns by type</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={types}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="type" interval={0} angle={-15} textAnchor="end" height={60} />
            <YAxis />
            <Tooltip />
            <Bar isAnimationActive={false} dataKey="n" name="patterns" fill="#2ca02c" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      {run && (
        <section className="panel">
          <h2>Risk score weights (run {run.runId})</h2>
          <dl>
            {Object.entries(run.weights).map(([k, w]) => (
              <Fragment key={k}><dt>{WEIGHT_LABELS[k] ?? k}</dt><dd>{w}</dd></Fragment>
            ))}
          </dl>
        </section>
      )}
    </div>
  );
}
