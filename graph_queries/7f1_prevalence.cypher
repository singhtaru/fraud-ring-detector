// 7f. Account level: how many accounts are in any labelled pattern.
// Expected: 3,170 of 515,088 (prevalence 0.615%).
MATCH (a:Account)
RETURN count(CASE WHEN EXISTS { (a)-[:IN_PATTERN]->() } THEN 1 END) AS patternAccounts,
       count(a) AS allAccounts
