// 7a. Store each pattern's account count (used in Jaccard).
MATCH (p:Pattern)
SET p.size = COUNT { (p)<-[:IN_PATTERN]-() };
