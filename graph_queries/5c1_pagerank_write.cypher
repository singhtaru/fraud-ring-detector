// 5c. PageRank: high when money flows in from other high-scoring accounts.
CALL gds.pageRank.write('txn', {writeProperty: 'pageRank'})
YIELD nodePropertiesWritten, ranIterations, computeMillis
