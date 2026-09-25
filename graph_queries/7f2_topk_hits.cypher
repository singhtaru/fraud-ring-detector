// 7f. Pattern accounts among the top K by riskScore (change LIMIT to
// 100, 500, 1000, 5000). Ties broken by accountId for a stable order.
// Expected hits: top100 7, top500 18, top1000 40, top5000 222.
// P@K = hits/K, R@K = hits/3,170, lift = P@K / 0.615%.
MATCH (a:Account) WITH a ORDER BY a.riskScore DESC, a.accountId LIMIT 1000
RETURN count(CASE WHEN EXISTS { (a)-[:IN_PATTERN]->() } THEN 1 END) AS hits
