// 5f. Do laundering transactions stay inside Louvain communities or cross
// between them? Compares the intra-community share of laundering vs normal
// transactions (self-transfers excluded). Overall laundering rate: 5,166 of
// 4,487,133 non-self txns = 0.115%.
MATCH (a:Account)-[r:SENT]->(b:Account)
WHERE a <> b
WITH r.isLaundering AS laundering,
     count(*) AS txns,
     sum(CASE WHEN a.communityId = b.communityId THEN 1 ELSE 0 END) AS intra
RETURN laundering, txns, intra,
       round(100.0 * intra / txns, 1) AS intraPct
ORDER BY laundering
