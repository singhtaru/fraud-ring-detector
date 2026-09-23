// 5f. Baseline: share of ALL accounts involved in any laundering transaction
// (expected 6,357 of 515,088 = 1.23%). Compare the top-1000 share against it.
MATCH (a:Account)
RETURN count(a) AS accounts,
       count(CASE WHEN EXISTS { (a)-[:SENT {isLaundering: 1}]-() } THEN a END) AS involved,
       round(100.0 * count(CASE WHEN EXISTS { (a)-[:SENT {isLaundering: 1}]-() } THEN a END)
             / count(a), 2) AS involvedPct
