"""Parse HI-Small_Patterns.txt into fraud.db (SQLite) as ground truth.

Account IDs use the same "<bank>_<account>" key as the Neo4j load, with
bank codes kept exactly as written. Both files use identical zero-padded
bank strings, and some codes differ only in padding ("039198" vs
"0039198"), so int()-normalising them would merge distinct banks.
"""
import csv
import re
import sqlite3
from collections import Counter

patterns, current = [], None
with open("data/HI-Small_Patterns.txt") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("BEGIN LAUNDERING ATTEMPT"):
            ptype = line.split("-", 1)[1].split(":")[0].strip()
            hops = re.search(r"Max (\d+)", line)
            current = {"pattern_id": len(patterns) + 1, "pattern_type": ptype,
                       "declared_max": int(hops.group(1)) if hops else None,
                       "accounts": set(), "transactions": []}
        elif line.startswith("END LAUNDERING ATTEMPT"):
            patterns.append(current)
            current = None
        elif current is not None:
            p = line.split(",")
            src = f"{p[1]}_{p[2]}"
            dst = f"{p[3]}_{p[4]}"
            current["accounts"].update([src, dst])
            current["transactions"].append((p[0], src, dst, float(p[7])))

con = sqlite3.connect("fraud.db")
con.executescript("""
DROP TABLE IF EXISTS patterns; DROP TABLE IF EXISTS pattern_members;
CREATE TABLE patterns (pattern_id INTEGER PRIMARY KEY, pattern_type TEXT,
                       declared_max INTEGER, n_accounts INTEGER, n_transactions INTEGER);
CREATE TABLE pattern_members (pattern_id INTEGER, account_id TEXT);
""")
for p in patterns:
    con.execute("INSERT INTO patterns VALUES (?,?,?,?,?)",
                (p["pattern_id"], p["pattern_type"], p["declared_max"],
                 len(p["accounts"]), len(p["transactions"])))
    con.executemany("INSERT INTO pattern_members VALUES (?,?)",
                    [(p["pattern_id"], a) for a in p["accounts"]])
con.commit()

print("Total patterns:", len(patterns))
for t, n in Counter(p["pattern_type"] for p in patterns).most_common():
    group = [p for p in patterns if p["pattern_type"] == t]
    sizes = [len(p["accounts"]) for p in group]
    txs = [len(p["transactions"]) for p in group]
    print(f"{t:15} count={n:4}  avg accounts={sum(sizes)/n:5.1f}  "
          f"min={min(sizes):3}  max={max(sizes):3}  avg tx={sum(txs)/n:5.1f}")

cycles = [p for p in patterns if p["pattern_type"] == "CYCLE"]
print("\nCycle length (accounts) distribution:",
      sorted(Counter(len(p["accounts"]) for p in cycles).items()))
print(f"HI-Small contains {len(cycles)} cycle patterns, averaging "
      f"{sum(len(p['accounts']) for p in cycles)/len(cycles):.1f} accounts each "
      f"(max {max(len(p['accounts']) for p in cycles)}).")

# Sanity check: every pattern account must exist in the transactions file,
# otherwise evaluation against Neo4j would silently score zero.
member_ids = set().union(*(p["accounts"] for p in patterns))
seen = set()
with open("data/HI-Small_Trans.csv", newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for v in reader:
        seen.add(f"{v[1]}_{v[2]}")
        seen.add(f"{v[3]}_{v[4]}")
missing = member_ids - seen
print(f"\nPattern accounts: {len(member_ids)}, missing from Trans.csv: {len(missing)}")
