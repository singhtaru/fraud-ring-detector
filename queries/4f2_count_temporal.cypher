// 4f (2/3). Count temporal rings: starting at some ring member, one real
// transaction per hop can be chosen so each is no earlier than the previous.
// Ring = distinct accounts a -> ... -> a over FLOWS_TO, counted once (start =
// lowest accountId; the inner predicate prunes the search to that start).
// {2,12} = longest ground-truth cycle (Phase 2). If it runs past ~3 min,
// change 12 to 8 in 4f1-4f3 and 4g and note the range used.
// Check (per rotation): st = timestamps reachable at the current hop; a hop
// keeps the transactions no earlier than some reachable one. Non-empty at
// the end = feasible. launderingRings = feasible using laundering txns only.
// Expected: {2,12} 4,224 rings / 219 laundering; {2,8} 4,201 / 205.
MATCH (a:Account)
MATCH (a) ((x)-[f:FLOWS_TO]->(y) WHERE y.accountId >= a.accountId){2,12} (a)
WHERE all(i IN range(0, size(x)-2) WHERE NOT x[i] IN x[i+1..])
WITH x, [k IN range(0, size(f)-1) | f[k..] + f[..k]] AS rotations
WITH any(rot IN rotations WHERE size(reduce(
         st = rot[0].ts,
         e IN rot[1..] |
         [j IN range(0, size(e.ts)-1) WHERE any(t IN st WHERE e.ts[j] >= t) | e.ts[j]])) > 0) AS ok,
     any(rot IN rotations WHERE size(reduce(
         st = [j IN range(0, size(rot[0].ts)-1) WHERE rot[0].laund[j] = 1 | rot[0].ts[j]],
         e IN rot[1..] |
         [j IN range(0, size(e.ts)-1) WHERE e.laund[j] = 1
            AND any(t IN st WHERE e.ts[j] >= t) | e.ts[j]])) > 0) AS okLaundering
WHERE ok
RETURN count(*) AS rings,
       sum(CASE WHEN okLaundering THEN 1 ELSE 0 END) AS launderingRings
