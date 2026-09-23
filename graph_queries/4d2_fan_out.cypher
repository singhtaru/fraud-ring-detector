// 4d. Fan-out: accounts sending to many distinct receivers.
MATCH (hub:Account)-[:SENT]->(dst:Account)
WHERE hub <> dst
WITH hub, count(DISTINCT dst) AS fanOut
WHERE fanOut >= 5
RETURN hub.accountId, fanOut ORDER BY fanOut DESC LIMIT 25
