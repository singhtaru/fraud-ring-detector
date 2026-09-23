// 4f (setup 2/4). Project FLOWS_TO into GDS for strongly connected components.
// Every cycle lies inside one SCC, so the ring queries only search accounts
// that share an SCC. Expect nodeCount 515,088, relationshipCount 647,939.
CALL gds.graph.project('flows', 'Account', 'FLOWS_TO')
YIELD graphName, nodeCount, relationshipCount, projectMillis
