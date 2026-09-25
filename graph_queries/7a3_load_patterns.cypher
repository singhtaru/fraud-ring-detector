// 7a. Load labelled patterns (patterns.csv from export_patterns.py).
LOAD CSV WITH HEADERS FROM 'file:///patterns.csv' AS row
MERGE (p:Pattern {patternId: toInteger(row.patternId)})
SET p.type = row.type;
