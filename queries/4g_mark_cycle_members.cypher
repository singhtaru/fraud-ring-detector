// 4g. Mark members of temporal cycles (UPDATE for CRUD; used by risk score).
// No dedup needed: DISTINCT n already collapses repeated rings.
// Use the same hop range as the 4f counts.
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,5} (a)
WHERE all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp)
UNWIND nodes(path) AS n
WITH DISTINCT n
SET n.inCycle = true
RETURN count(n) AS accountsInCycles
