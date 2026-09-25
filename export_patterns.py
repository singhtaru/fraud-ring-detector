"""Export the labelled patterns from fraud.db to CSV for LOAD CSV (Phase 7).

Writes patterns.csv (patternId, type) and pattern_members.csv
(patternId, accountId). Account IDs use the same "<bank>_<account>" key
as the graph, so they match Account.accountId directly.
"""
import csv
import sqlite3

con = sqlite3.connect("fraud.db")

with open("patterns.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["patternId", "type"])
    w.writerows(con.execute("SELECT pattern_id, pattern_type FROM patterns"))

with open("pattern_members.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["patternId", "accountId"])
    w.writerows(con.execute("SELECT pattern_id, account_id FROM pattern_members"))

print("done")
