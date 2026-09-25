"""Phase 8: build the SQLite side of the Cypher-vs-SQL benchmark.

Stores one row per distinct sender -> receiver pair (self-transfers skipped)
in benchmark.db, i.e. the same edges as Neo4j's FLOWS_TO relationships.
Standard library only.  Usage: python build_flows_sqlite.py
"""
import csv
import os
import sqlite3

if os.path.exists("benchmark.db"):
    os.remove("benchmark.db")
con = sqlite3.connect("benchmark.db")
con.execute("CREATE TABLE flows (src TEXT NOT NULL, dst TEXT NOT NULL, PRIMARY KEY (src, dst))")

pairs = set()
with open("transactions.csv", newline="") as f:
    for row in csv.DictReader(f):
        if row["fromId"] != row["toId"]:
            pairs.add((row["fromId"], row["toId"]))

con.executemany("INSERT INTO flows VALUES (?, ?)", pairs)
con.execute("CREATE INDEX flows_src ON flows (src)")
con.commit()
print(f"{con.execute('SELECT count(*) FROM flows').fetchone()[0]:,} pairs in benchmark.db "
      "(must equal the FLOWS_TO count in Neo4j: 647,939)")
