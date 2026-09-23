// 4e. Chains (multi-hop layering): 3-6 time-ordered hops, no self-transfers.
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){3,6} (b:Account)
WHERE a <> b
  AND all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp)
RETURN path LIMIT 10
