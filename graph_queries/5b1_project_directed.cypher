// 5b. Directed projection (PageRank, WCC).
// Self-transfers are excluded: 591,212 SENT rels (11.6%) are account -> same
// account, and 92,354 accounts have nothing else. A native projection keeps
// those loops, which pins those accounts at PageRank ~1.0 (the top of the
// ranking) and makes each its own Louvain community. OPTIONAL MATCH keeps
// every account as a node, so all 515,088 still get results written.
MATCH (a:Account)
OPTIONAL MATCH (a)-[:SENT]->(b:Account) WHERE a <> b
WITH gds.graph.project('txn', a, b) AS g
RETURN g.graphName, g.nodeCount, g.relationshipCount, g.projectMillis
