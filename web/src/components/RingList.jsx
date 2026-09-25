import { useEffect, useState } from "react";
import { api } from "../api";

const METHODS = ["cycles_time_amount", "cycles_temporal", "cycles_basic", "fan_out_daily", "fan_in_daily"];
const SORTS = [["avgRisk", "Avg risk"], ["maxRisk", "Max risk"], ["size", "Size"]];
const PAGE = 25;

export default function RingList({ selectedId, onSelect }) {
  const [method, setMethod] = useState(METHODS[0]);
  // Default 3: two-account "rings" are mostly back-and-forth payments between
  // busy legitimate accounts and would otherwise fill the top of the list.
  const [minSize, setMinSize] = useState(3);
  const [matchedOnly, setMatchedOnly] = useState(false);
  const [sortBy, setSortBy] = useState("avgRisk");
  const [page, setPage] = useState(0);
  const [rings, setRings] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let ignore = false; // stops a stale request overwriting a newer one
    setLoading(true);
    setError(null);
    api.rings({ method, min_size: minSize, matched_only: matchedOnly, sort_by: sortBy,
                limit: PAGE, skip: page * PAGE })
      .then((d) => !ignore && setRings(d.rings))
      .catch((e) => !ignore && setError(e.message))
      .finally(() => !ignore && setLoading(false));
    return () => { ignore = true; };
  }, [method, minSize, matchedOnly, sortBy, page]);

  // Any filter change starts again from the first page.
  const change = (setter) => (value) => { setter(value); setPage(0); };

  return (
    <section className="panel">
      <h2>Detected rings</h2>
      <select value={method} onChange={(e) => change(setMethod)(e.target.value)}>
        {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>

      <div className="filters">
        <label>
          Min size{" "}
          <select value={minSize} onChange={(e) => change(setMinSize)(Number(e.target.value))}>
            {[2, 3, 4, 5, 8].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <label>
          Sort{" "}
          <select value={sortBy} onChange={(e) => change(setSortBy)(e.target.value)}>
            {SORTS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
        </label>
        <label>
          <input type="checkbox" checked={matchedOnly}
                 onChange={(e) => change(setMatchedOnly)(e.target.checked)} /> Matched only
        </label>
      </div>

      {error && <p className="error">{error}</p>}
      {!loading && !error && rings.length === 0 && <p className="hint small">No rings match these filters.</p>}

      <table>
        <thead>
          <tr><th>ID</th><th>Size</th><th>Avg risk</th><th>Max risk</th><th>Matched</th></tr>
        </thead>
        <tbody>
          {rings.map((r) => (
            <tr key={r.detectionId}
                className={r.detectionId === selectedId ? "selected" : ""}
                onClick={() => onSelect(r.detectionId)}>
              <td>{r.detectionId}</td>
              <td>{r.size}</td>
              <td>{r.avgRisk?.toFixed(1)}</td>
              <td>{r.maxRisk?.toFixed(1)}</td>
              <td>{r.bestJaccard >= 0.5 ? "✓" : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pager">
        <button disabled={page === 0 || loading} onClick={() => setPage((p) => p - 1)}>Prev</button>
        <span>Page {page + 1}</span>
        <button disabled={rings.length < PAGE || loading} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </section>
  );
}
