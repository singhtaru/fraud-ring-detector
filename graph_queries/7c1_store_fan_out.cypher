// 7c. Fan-out detections: one account sending to 5-50 distinct accounts on
// one day (the cap of 50 keeps institutional hubs out). One detection per
// hub-day. Expected: 49,765 detections, 359,184 MEMBER_OF links.
:auto MATCH (hub:Account)-[r:SENT]->(c:Account) WHERE c <> hub
WITH hub, date(r.timestamp) AS day, collect(DISTINCT c) AS cps
WHERE 5 <= size(cps) <= 50
CALL (hub, day, cps) {
  MERGE (d:Detection {key: 'fan_out_daily:' + hub.accountId + ':' + toString(day)})
    ON CREATE SET d.method = 'fan_out_daily', d.target = 'FAN-OUT', d.size = size(cps) + 1
  MERGE (hub)-[:MEMBER_OF]->(d)
  FOREACH (x IN cps | MERGE (x)-[:MEMBER_OF]->(d))
} IN TRANSACTIONS OF 1000 ROWS
