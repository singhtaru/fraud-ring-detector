"""
Phase 6 - interpretable composite risk score.

score = 100 * sum(weight_i * minmax(signal_i)), with every component stored,
so any score decomposes into named parts (NFR 7) and every run is logged (NFR 11).

Standard library + the neo4j driver only (no pandas).
Usage:  python risk_score.py            (reads risk_config.json and .env)
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

from neo4j import GraphDatabase

SIGNALS = ["cycle", "cross_community", "pagerank", "velocity"]
SIG_PROP = {"cycle": "sigCycle", "cross_community": "sigCrossCommunity",
            "pagerank": "sigPageRank", "velocity": "sigVelocity"}
RISK_PROP = {"cycle": "riskCycle", "cross_community": "riskCrossCommunity",
             "pagerank": "riskPageRank", "velocity": "riskVelocity"}


def read_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def step(title):
    print(f"\n== {title}")
    return time.time()


def done(t0):
    print(f"   took {time.time() - t0:.1f} s")


# ---------------------------------------------------------------- setup
with open("risk_config.json") as f:
    cfg = json.load(f)
weights = cfg["weights"]
assert set(weights) == set(SIGNALS), f"weights must have exactly {SIGNALS}"
assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1"

env = {**read_env(), **os.environ}
driver = GraphDatabase.driver(env.get("NEO4J_URI", "neo4j://127.0.0.1:7687"),
                              auth=(env.get("NEO4J_USER", "neo4j"), env["NEO4J_PASSWORD"]))
DB = env.get("NEO4J_DATABASE", "neo4j")


def cypher(query, **params):
    with driver.session(database=DB) as s:
        return [r.data() for r in s.run(query, params)]


# ---------------------------------------------------------------- 6a raw signals
t0 = step("6a  Computing raw signals per account (several minutes)")
cypher("""
MATCH (a:Account)
CALL (a) {
  OPTIONAL MATCH (a)-[r:SENT]-(b:Account) WHERE b <> a
  WITH a, count(r) AS n,
       sum(CASE WHEN b.communityId <> a.communityId THEN 1 ELSE 0 END) AS crossN,
       min(r.timestamp) AS firstTs, max(r.timestamp) AS lastTs,
       sum(r.isLaundering) AS launderingN
  SET a.sigCycle = CASE WHEN coalesce(a.inCycle, false) THEN 1.0 ELSE 0.0 END,
      a.sigPageRank = log(1.0 + coalesce(a.pageRank, 0.0)),
      a.sigCrossCommunity = toFloat(crossN) / (n + $smooth),
      a.sigVelocity = CASE WHEN n = 0 THEN 0.0
          ELSE log(1.0 + n / (duration.inSeconds(firstTs, lastTs).seconds / 86400.0 + 1.0)) END,
      a.txnCount = n,
      a.evalLaunderingInvolved = launderingN > 0
} IN TRANSACTIONS OF 5000 ROWS
""", smooth=cfg["cross_community_smoothing"])
done(t0)

# ---------------------------------------------------------------- 6b normalisation bounds
t0 = step("6b  Min/max per signal")
bounds = cypher("MATCH (a:Account) RETURN " + ", ".join(
    f"min(a.{p}) AS min_{s}, max(a.{p}) AS max_{s}" for s, p in SIG_PROP.items()))[0]
mins = {s: bounds[f"min_{s}"] for s in SIGNALS}
ranges = {s: (bounds[f"max_{s}"] - mins[s]) or 1.0 for s in SIGNALS}  # avoid divide-by-zero
for s in SIGNALS:
    print(f"   {s:16} min={mins[s]:.6f}  max={bounds[f'max_{s}']:.6f}")
done(t0)

# ---------------------------------------------------------------- 6c weighted score
run_id = int(time.time())
t0 = step(f"6c  Writing riskScore and components (run {run_id})")
set_components = ",\n      ".join(
    f"a.{RISK_PROP[s]} = round(100.0 * $w.{s} * (a.{SIG_PROP[s]} - $mn.{s}) / $rg.{s}, 3)"
    for s in SIGNALS)
cypher(f"""
MATCH (a:Account)
CALL (a) {{
  SET {set_components}
  SET a.riskScore = round(a.riskCycle + a.riskCrossCommunity + a.riskPageRank + a.riskVelocity, 3),
      a.riskRunId = $runId
}} IN TRANSACTIONS OF 10000 ROWS
""", w=weights, mn=mins, rg=ranges, runId=run_id)
done(t0)

# ---------------------------------------------------------------- 6d log run + breakdown to SQLite
t0 = step("6d  Saving run parameters and breakdowns to SQLite")
con = sqlite3.connect(cfg["sqlite_path"])
con.executescript("""
CREATE TABLE IF NOT EXISTS risk_runs (
  run_id INTEGER PRIMARY KEY, created_at TEXT, config_json TEXT, bounds_json TEXT);
CREATE TABLE IF NOT EXISTS account_risk (
  run_id INTEGER, account_id TEXT, score REAL,
  cycle_component REAL, cross_community_component REAL,
  pagerank_component REAL, velocity_component REAL,
  PRIMARY KEY (run_id, account_id));
""")
con.execute("INSERT INTO risk_runs VALUES (?,?,?,?)",
            (run_id, datetime.now(timezone.utc).isoformat(), json.dumps(cfg), json.dumps(bounds)))
records = cypher("""
MATCH (a:Account)
RETURN a.accountId AS id, a.riskScore AS score, a.riskCycle AS c,
       a.riskCrossCommunity AS x, a.riskPageRank AS p, a.riskVelocity AS v
""")
con.executemany("INSERT INTO account_risk VALUES (?,?,?,?,?,?,?)",
                [(run_id, r["id"], r["score"], r["c"], r["x"], r["p"], r["v"]) for r in records])
con.commit()
print(f"   {len(records):,} rows saved")
done(t0)

# ---------------------------------------------------------------- 6e quick check against labels
t0 = step("6e  How well does each ranking surface laundering accounts?")
labelled = {r["id"] for r in cypher(
    "MATCH (a:Account) WHERE a.evalLaunderingInvolved RETURN a.accountId AS id")}
baseline = len(labelled) / len(records)
try:
    members = {row[0] for row in con.execute("SELECT DISTINCT account_id FROM pattern_members")}
except sqlite3.OperationalError:
    members = set()

rankings = {"riskScore": "riskScore", "cycle only": "sigCycle",
            "cross-community only": "sigCrossCommunity", "pagerank only": "sigPageRank",
            "velocity only": "sigVelocity"}
max_k = max(cfg["top_k"])
print(f"   baseline: {baseline:.2%} of accounts touch a laundering transaction")
print(f"   {'ranking':22}" + "".join(f"  top{k:<6}" for k in cfg["top_k"]) + "  pattern recall@max")
for label, prop in rankings.items():
    top = [r["id"] for r in cypher(
        f"MATCH (a:Account) RETURN a.accountId AS id ORDER BY a.{prop} DESC, a.accountId LIMIT $k",
        k=max_k)]
    cells = "".join(f"  {sum(i in labelled for i in top[:k]) / k:>7.1%} " for k in cfg["top_k"])
    recall = (len(members & set(top)) / len(members)) if members else float("nan")
    print(f"   {label:22}{cells}  {recall:.1%}")
done(t0)

# ---------------------------------------------------------------- example decomposition
print("\n== Top 5 accounts, decomposed")
for r in cypher("""
MATCH (a:Account) RETURN a.accountId AS id, a.riskScore AS s, a.riskCycle AS c,
  a.riskCrossCommunity AS x, a.riskPageRank AS p, a.riskVelocity AS v,
  a.evalLaunderingInvolved AS lab
ORDER BY a.riskScore DESC LIMIT 5"""):
    print(f"   {r['id']:18} {r['s']:6.1f} = cycle {r['c']:.1f} + cross {r['x']:.1f}"
          f" + pagerank {r['p']:.1f} + velocity {r['v']:.1f}   (labelled: {r['lab']})")

con.close()
driver.close()
print(f"\nDone. Run id {run_id}.")
