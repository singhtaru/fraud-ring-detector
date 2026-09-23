// 5d. Louvain: groups accounts that transact more with each other than with
// outsiders. Modularity > 0.3 = meaningful community structure.
CALL gds.louvain.write('txn_undirected', {writeProperty: 'communityId'})
YIELD communityCount, modularity, computeMillis
