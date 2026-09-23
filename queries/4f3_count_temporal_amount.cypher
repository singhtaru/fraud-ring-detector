// 4f (3/3). Count temporal rings with amount conservation: as 4f2, and each
// chosen hop passes on 50-120% of the previous hop's USD value.
// Ring = distinct accounts a -> ... -> a over FLOWS_TO, counted once (start =
// lowest accountId; the inner predicate prunes the search to that start).
// {2,12} = longest ground-truth cycle (Phase 2). If it runs past ~3 min,
// change 12 to 8 in 4f1-4f3 and 4g and note the range used.
// States are [timestamp, usd] pairs of transactions reachable at each hop.
// Expected: {2,12} 1,234 rings / 80 laundering; {2,8} 1,224 / 70.
MATCH (a:Account)
MATCH (a) ((x)-[f:FLOWS_TO]->(y) WHERE y.accountId >= a.accountId){2,12} (a)
WHERE all(i IN range(0, size(x)-2) WHERE NOT x[i] IN x[i+1..])
WITH x, [k IN range(0, size(f)-1) | f[k..] + f[..k]] AS rotations
WITH any(rot IN rotations WHERE size(reduce(
         st = [j IN range(0, size(rot[0].ts)-1) | [rot[0].ts[j], rot[0].usd[j]]],
         e IN rot[1..] |
         [j IN range(0, size(e.ts)-1) WHERE any(s IN st WHERE e.ts[j] >= s[0]
            AND e.usd[j] > 0.5 * s[1] AND e.usd[j] < 1.2 * s[1])
          | [e.ts[j], e.usd[j]]])) > 0) AS ok,
     any(rot IN rotations WHERE size(reduce(
         st = [j IN range(0, size(rot[0].ts)-1) WHERE rot[0].laund[j] = 1
               | [rot[0].ts[j], rot[0].usd[j]]],
         e IN rot[1..] |
         [j IN range(0, size(e.ts)-1) WHERE e.laund[j] = 1 AND any(s IN st WHERE e.ts[j] >= s[0]
            AND e.usd[j] > 0.5 * s[1] AND e.usd[j] < 1.2 * s[1])
          | [e.ts[j], e.usd[j]]])) > 0) AS okLaundering
WHERE ok
RETURN count(*) AS rings,
       sum(CASE WHEN okLaundering THEN 1 ELSE 0 END) AS launderingRings
