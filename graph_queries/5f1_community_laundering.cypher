// 5f. Communities with the highest share of laundering among their internal
// transactions (self-transfers excluded, matching the projection).
MATCH (a:Account)-[r:SENT]->(b:Account)
WHERE a.communityId = b.communityId AND a <> b
WITH a.communityId AS community, count(r) AS internalTxns,
     sum(r.isLaundering) AS launderingTxns
WHERE internalTxns >= 20
RETURN community, internalTxns, launderingTxns,
       round(100.0 * launderingTxns / internalTxns, 2) AS launderingPct
ORDER BY launderingPct DESC LIMIT 15
