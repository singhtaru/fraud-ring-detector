// 4a. Basic cycles, 2-8 hops.
// x <> y skips self-transfers; the accountId rule counts each ring once.
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,8} (a)
WHERE all(n IN nodes(path) WHERE a.accountId <= n.accountId)
RETURN path LIMIT 25
