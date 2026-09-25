import { useEffect, useState } from "react";
import { api } from "./api";
import RingList from "./components/RingList";
import RingGraph from "./components/RingGraph";
import AccountPanel from "./components/AccountPanel";
import Dashboard from "./components/Dashboard";

// Optional deep links for demos: #dashboard, or #ring=13629&account=01362_8003A56A0
const initial = new URLSearchParams(window.location.hash.slice(1));

export default function App() {
  const [tab, setTab] = useState(initial.has("dashboard") ? "dashboard" : "rings");
  const [ringId, setRingId] = useState(initial.get("ring") ? Number(initial.get("ring")) : null);
  const [ring, setRing] = useState(null);
  const [accountId, setAccountId] = useState(initial.get("account"));
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (ringId == null) return;
    let ignore = false;
    setError(null);
    api.ring(ringId)
      .then((r) => !ignore && setRing(r))
      .catch((e) => !ignore && setError(e.message));
    return () => { ignore = true; };
  }, [ringId]);

  function openRing(id) {
    setTab("rings");
    setRingId(id);
  }

  return (
    <div className="app">
      <header>
        <h1>Fraud Ring Detection</h1>
        <nav>
          <button className={tab === "rings" ? "active" : ""} onClick={() => setTab("rings")}>Rings</button>
          <button className={tab === "dashboard" ? "active" : ""} onClick={() => setTab("dashboard")}>Dashboard</button>
        </nav>
        <form onSubmit={(e) => { e.preventDefault(); if (search.trim()) { setAccountId(search.trim()); setTab("rings"); } }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Find account, e.g. 01362_8003A56A0" />
          <button type="submit">Search</button>
        </form>
      </header>

      {tab === "dashboard" ? (
        <Dashboard />
      ) : (
        <main className="layout">
          <RingList selectedId={ringId} onSelect={setRingId} />

          <section className="panel center">
            {error && <p className="error">{error}</p>}
            {ring && (
              <div className="ring-info">
                <strong>Ring #{ring.detectionId}</strong> · {ring.method} · {ring.size} accounts ·
                avg risk {ring.avgRisk?.toFixed(1)}
                {ring.matchedPatterns?.length > 0 && (
                  <span className="match">
                    {" "}· matches {ring.matchedPatterns.map((p) => `${p.type} #${p.patternId} (J=${p.jaccard.toFixed(2)})`).join(", ")}
                  </span>
                )}
              </div>
            )}
            <RingGraph graph={ring?.graph} selectedAccount={accountId} onNodeClick={setAccountId} />
          </section>

          <AccountPanel accountId={accountId} onSelectRing={openRing} />
        </main>
      )}
    </div>
  );
}
