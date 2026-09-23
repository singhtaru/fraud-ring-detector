// 5c. Top accounts by PageRank.
MATCH (a:Account)
RETURN a.accountId, a.pageRank
ORDER BY a.pageRank DESC LIMIT 20
