// 7a. Check the account IDs matched the graph.
// Expected: 370 patterns, 3,596 member links, 0 empty patterns.
MATCH (p:Pattern)
RETURN count(p) AS patterns, sum(p.size) AS memberLinks,
       count(CASE WHEN p.size = 0 THEN 1 END) AS emptyPatterns
