"""Phase 8: Cypher vs SQL benchmark - cycle detection at hop depths 2-8.

Both engines answer the same question on the same edges (FLOWS_TO in Neo4j,
the flows table in benchmark.db): how many simple cycles of exactly `depth`
hops pass through each start account. Start accounts = all 6,941 inCycle
accounts (Phase 4); a 50-account sample finished in milliseconds on this
sparse graph, too small to show how cost grows with depth. Both reject a repeated
account at every hop, so the work being compared is the traversal itself.

Per engine and depth: 1 warm-up + 3 timed runs, median kept; a run over
TIMEOUT_S is recorded as a timeout and deeper depths are skipped for that
engine. Results go to benchmark_results.csv and a correctness check prints.
Usage: python benchmark.py   (reads .env like risk_score.py)
"""
import csv
import os
import sqlite3
import statistics
import time

from neo4j import GraphDatabase, Query

DEPTHS = [2, 3, 4, 5, 6, 7, 8]
RUNS = 3
TIMEOUT_S = 300

env = dict(os.environ)
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
driver = GraphDatabase.driver(env.get("NEO4J_URI", "neo4j://127.0.0.1:7687"),
                              auth=(env.get("NEO4J_USER", "neo4j"), env["NEO4J_PASSWORD"]))
db = env.get("NEO4J_DATABASE", "neo4j")


def neo4j(query, timeout=None, **params):
    with driver.session(database=db) as s:
        return [r.data() for r in s.run(Query(query, timeout=timeout), params)]


# Fixed start accounts: every member of a temporal ring (Phase 4 inCycle).
ids = neo4j("""
MATCH (a:Account) WHERE a.inCycle
WITH a ORDER BY a.accountId
RETURN collect(a.accountId) AS ids
""")[0]["ids"]
print(f"{len(ids)} start accounts")


def cypher_for(depth):
    """Fixed-length cycle pattern: start -> n1 -> ... -> start, all distinct."""
    inner = [f"n{i}" for i in range(1, depth)]
    pattern = "(s)" + "".join(f"-[:FLOWS_TO]->({n})" for n in inner) + "-[:FLOWS_TO]->(s)"
    conds = [f"{n} <> s" + (f" AND NOT {n} IN [{', '.join(inner[:i])}]" if i else "")
             for i, n in enumerate(inner)]
    return (f"UNWIND $ids AS id MATCH (s:Account {{accountId: id}}) "
            f"MATCH {pattern} WHERE " + " AND ".join(conds) + " RETURN count(*) AS cycles")


SQL = """
WITH RECURSIVE walk(start, node, depth, path) AS (
  SELECT src, dst, 1, ',' || src || ',' || dst || ','
  FROM flows WHERE src IN (SELECT value FROM json_each(?))
  UNION ALL
  SELECT w.start, f.dst, w.depth + 1, w.path || f.dst || ','
  FROM walk w JOIN flows f ON f.src = w.node
  WHERE w.depth < ? AND w.node <> w.start
    AND (f.dst = w.start OR instr(w.path, ',' || f.dst || ',') = 0)
)
SELECT count(*) FROM walk WHERE node = start AND depth = ?
"""

con = sqlite3.connect("benchmark.db")
ids_json = "[" + ",".join(f'"{i}"' for i in ids) + "]"


def run_sql(depth):
    deadline = time.time() + TIMEOUT_S
    con.set_progress_handler(lambda: time.time() > deadline, 100_000)  # non-zero aborts
    try:
        return con.execute(SQL, (ids_json, depth, depth)).fetchone()[0]
    finally:
        con.set_progress_handler(None, 0)


def run_cypher(depth):
    return neo4j(cypher_for(depth), timeout=TIMEOUT_S, ids=ids)[0]["cycles"]


results = []
for engine, fn in [("sqlite", run_sql), ("neo4j", run_cypher)]:
    timed_out = False
    for depth in DEPTHS:
        if timed_out:
            results.append([engine, depth, "", "", "skipped"])
            continue
        times, cycles = [], None
        try:
            for i in range(RUNS + 1):  # first run is the warm-up
                t0 = time.perf_counter()
                cycles = fn(depth)
                if i:
                    times.append(time.perf_counter() - t0)
            med = statistics.median(times)
            results.append([engine, depth, f"{med:.4f}", cycles, "ok"])
            print(f"{engine:7} depth {depth}: {med:9.3f} s  ({cycles:,} cycles)")
        except Exception as e:  # SQLite interrupt or Neo4j transaction timeout
            timed_out = True
            results.append([engine, depth, "", "", "timeout"])
            print(f"{engine:7} depth {depth}: TIMEOUT (> {TIMEOUT_S} s) [{type(e).__name__}]")

with open("benchmark_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["engine", "depth", "median_seconds", "cycles", "status"])
    w.writerows(results)

print("\nCorrectness check (cycle counts must agree):")
by = {(r[0], r[1]): r for r in results}
for d in DEPTHS:
    s, n = by[("sqlite", d)], by[("neo4j", d)]
    if s[4] == "ok" and n[4] == "ok":
        print(f"  depth {d}: {'OK' if s[3] == n[3] else 'MISMATCH'} ({s[3]:,} vs {n[3]:,})")
    else:
        print(f"  depth {d}: not compared (sqlite {s[4]}, neo4j {n[4]})")

driver.close()
print("\nWrote benchmark_results.csv")
