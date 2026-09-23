// 5e. Weakly Connected Components (preprocessing step in the design).
CALL gds.wcc.write('txn', {writeProperty: 'componentId'})
YIELD componentCount, computeMillis
