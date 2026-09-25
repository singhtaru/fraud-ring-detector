// 7d. A detection matches a pattern when their account sets have Jaccard
// similarity >= 0.5 (shared / union): at least half the pattern found without
// too much unrelated around it. Only overlapping pairs are compared.
MATCH (d:Detection)<-[:MEMBER_OF]-(a:Account)-[:IN_PATTERN]->(p:Pattern)
WITH d, p, count(DISTINCT a) AS overlap
WITH d, p, toFloat(overlap) / (d.size + p.size - overlap) AS jaccard
WHERE jaccard >= 0.5
MERGE (d)-[m:MATCHES]->(p)
SET m.jaccard = jaccard
RETURN count(m) AS matchLinks
