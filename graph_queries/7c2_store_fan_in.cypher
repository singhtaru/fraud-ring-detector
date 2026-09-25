// 7c. Fan-in detections: one account receiving from 5-50 distinct accounts
// on one day. Expected: 6,516 detections, 74,814 MEMBER_OF links.
:auto MATCH (hub:Account)<-[r:SENT]-(c:Account) WHERE c <> hub
WITH hub, date(r.timestamp) AS day, collect(DISTINCT c) AS cps
WHERE 5 <= size(cps) <= 50
CALL (hub, day, cps) {
  MERGE (d:Detection {key: 'fan_in_daily:' + hub.accountId + ':' + toString(day)})
    ON CREATE SET d.method = 'fan_in_daily', d.target = 'FAN-IN', d.size = size(cps) + 1
  MERGE (hub)-[:MEMBER_OF]->(d)
  FOREACH (x IN cps | MERGE (x)-[:MEMBER_OF]->(d))
} IN TRANSACTIONS OF 1000 ROWS
