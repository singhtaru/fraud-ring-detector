// 5f. Are high-PageRank accounts laundering-involved more often than the
// 1.23% baseline (5f2)? A modest lift supports fusing several signals.
MATCH (a:Account)
WITH a ORDER BY a.pageRank DESC LIMIT 1000
WITH count(a) AS top1000,
     count(CASE WHEN EXISTS { (a)-[:SENT {isLaundering: 1}]-() } THEN a END) AS involved
RETURN top1000, involved, round(100.0 * involved / top1000, 2) AS involvedPct
