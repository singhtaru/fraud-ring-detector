// 4g. Mark members of temporal rings (as 4f2) with inCycle = true.
// UPDATE for CRUD; used by the risk score. Run 4f0 first.
// Expected: {2,12} 6,941 accounts; use the same range as the 4f counts.
MATCH (a:Account)
MATCH (a) ((x)-[f:FLOWS_TO]->(y) WHERE y.accountId >= a.accountId){2,12} (a)
WHERE all(i IN range(0, size(x)-2) WHERE NOT x[i] IN x[i+1..])
WITH x, [k IN range(0, size(f)-1) | f[k..] + f[..k]] AS rotations
WHERE any(rot IN rotations WHERE size(reduce(
        st = rot[0].ts,
        e IN rot[1..] |
        [j IN range(0, size(e.ts)-1) WHERE any(t IN st WHERE e.ts[j] >= t) | e.ts[j]])) > 0)
UNWIND x AS n
WITH DISTINCT n
SET n.inCycle = true
RETURN count(n) AS accountsInCycles
