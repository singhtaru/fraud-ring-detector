// 4f (setup 3/4). Write each account's strongly connected component as sccId.
// Only 23,247 accounts (4.5%) are in an SCC of 2+ accounts (largest 17,075);
// everyone else can't be on any cycle.
CALL gds.scc.write('flows', {writeProperty: 'sccId'})
YIELD componentCount, nodePropertiesWritten, computeMillis
