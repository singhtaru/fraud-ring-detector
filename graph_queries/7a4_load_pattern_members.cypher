// 7a. Link accounts to their patterns (pattern_members.csv).
LOAD CSV WITH HEADERS FROM 'file:///pattern_members.csv' AS row
MATCH (p:Pattern {patternId: toInteger(row.patternId)})
MATCH (a:Account {accountId: row.accountId})
MERGE (a)-[:IN_PATTERN]->(p);
