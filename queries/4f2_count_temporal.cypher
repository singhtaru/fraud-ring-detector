// 4f (2/3). Count temporal cycles (as 4b).
// {2,5} because counting explores the whole graph. If it runs past ~3 min,
// stop it, change to {2,4} in all three 4f files, and note the range used.
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,5} (a)
WHERE all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp)
  AND (r[0].timestamp < r[-1].timestamp
       OR all(n IN nodes(path) WHERE a.accountId <= n.accountId))
RETURN count(path) AS cycles,
       sum(CASE WHEN all(rel IN relationships(path) WHERE rel.isLaundering = 1)
                THEN 1 ELSE 0 END) AS launderingCycles
