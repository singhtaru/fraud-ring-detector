// 4b. Temporal cycles: each hop happens no earlier than the previous one.
// Dedup: a time-ordered cycle has only one valid starting point, so the
// temporal check already stops a ring being counted once per member. The
// lowest-accountId rule only breaks ties when every hop has the same
// timestamp. (Applying it unconditionally would drop ~2/3 of real rings:
// only 17 of the 54 ground-truth cycles are time-ordered from their
// lowest-ID account, versus 49 from their true origin.)
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,8} (a)
WHERE all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp)
  AND (r[0].timestamp < r[-1].timestamp
       OR all(n IN nodes(path) WHERE a.accountId <= n.accountId))
RETURN path LIMIT 25
