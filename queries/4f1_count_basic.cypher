// 4f (1/3). Count all rings (no temporal or amount filter).
// Ring = distinct accounts a -> ... -> a over FLOWS_TO, counted once (start =
// lowest accountId; the inner predicate prunes the search to that start).
// {2,12} = longest ground-truth cycle (Phase 2). If it runs past ~3 min,
// change 12 to 8 in 4f1-4f3 and 4g and note the range used.
// launderingRings = every hop has at least one laundering transaction.
// Expected: {2,12} 12,885 rings / 2,086 laundering; {2,8} 6,621 / 1,222.
MATCH (a:Account)
MATCH (a) ((x)-[f:FLOWS_TO]->(y) WHERE y.accountId >= a.accountId){2,12} (a)
WHERE all(i IN range(0, size(x)-2) WHERE NOT x[i] IN x[i+1..])
RETURN count(*) AS rings,
       sum(CASE WHEN all(e IN f WHERE 1 IN e.laund) THEN 1 ELSE 0 END) AS launderingRings
