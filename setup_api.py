"""Phase 9 one-time setup in Neo4j for the API (safe to re-run).

1. Numeric detectionId on every :Detection (keys contain | and :, awkward in URLs).
2. Precomputed avgRisk / maxRisk / bestJaccard per detection, so /rings loads instantly.
3. Indexes used by the API.
Usage: python setup_api.py   (reads .env)
"""
from app.db import rows

STEPS = [
    ("Numbering detections", """
        MATCH (d:Detection) WITH d ORDER BY d.method, d.key
        WITH collect(d) AS ds
        UNWIND range(0, size(ds) - 1) AS i
        WITH ds[i] AS d, i
        SET d.detectionId = i + 1
        RETURN count(d) AS n"""),
    ("detectionId constraint", """
        CREATE CONSTRAINT detection_id IF NOT EXISTS
        FOR (d:Detection) REQUIRE d.detectionId IS UNIQUE"""),
    ("Precomputing ring risk and match quality", """
        MATCH (d:Detection)
        CALL (d) {
          MATCH (a:Account)-[:MEMBER_OF]->(d)
          WITH d, avg(a.riskScore) AS avgRisk, max(a.riskScore) AS maxRisk
          OPTIONAL MATCH (d)-[m:MATCHES]->(:Pattern)
          WITH d, avgRisk, maxRisk, max(m.jaccard) AS bestJaccard
          SET d.avgRisk = round(avgRisk, 3), d.maxRisk = maxRisk,
              d.bestJaccard = coalesce(bestJaccard, 0.0)
        } IN TRANSACTIONS OF 5000 ROWS"""),
    ("Index on Detection.method",
     "CREATE INDEX detection_method IF NOT EXISTS FOR (d:Detection) ON (d.method)"),
    ("Index on Detection.avgRisk",
     "CREATE INDEX detection_risk IF NOT EXISTS FOR (d:Detection) ON (d.avgRisk)"),
    ("Index on SENT.transactionId",
     "CREATE INDEX sent_txid IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.transactionId)"),
]

for title, query in STEPS:
    print(f"- {title} ...", end=" ", flush=True)
    out = rows(query, timeout=None)
    print(out[0] if out else "done")

check = rows("""
MATCH (d:Detection)
RETURN count(d) AS detections, count(d.detectionId) AS numbered,
       count(d.avgRisk) AS withRisk, max(d.detectionId) AS maxId
""")[0]
print("\nCheck:", check, "(expect 70,171 of each)")
print("Note: the SENT.transactionId index builds in the background over 5M relationships;")
print("      lookups by transaction id are slow until it is ONLINE (SHOW INDEXES).")
