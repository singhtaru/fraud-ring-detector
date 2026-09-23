// 4d. Fan-in: accounts receiving from many distinct senders.
MATCH (hub:Account)<-[:SENT]-(src:Account)
WHERE hub <> src
WITH hub, count(DISTINCT src) AS fanIn
WHERE fanIn >= 5
RETURN hub.accountId, fanIn ORDER BY fanIn DESC LIMIT 25
