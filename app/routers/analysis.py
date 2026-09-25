"""Live, anchored searches from one account.

Full-graph detection is precomputed (stored :Detection nodes, see the rings
router): a live full-graph search runs out of memory (Phase 4). Searches
anchored on one account are fast (milliseconds in the Phase 8 benchmark),
so they are offered live here.
"""
from fastapi import APIRouter, HTTPException, Query

from ..db import rows

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _require_account(account_id):
    result = rows("MATCH (a:Account {accountId: $id}) RETURN a.sccId AS scc", {"id": account_id})
    if not result:
        raise HTTPException(404, f"Account '{account_id}' not found")
    return result[0]["scc"]


def _cycle_query(depth):
    """Fixed-length ring start -> n1 -> ... -> start over FLOWS_TO, inside the
    start's SCC, rejecting a repeated account at every hop (as in Phase 8)."""
    inner = [f"n{i}" for i in range(1, depth)]
    rels = [f"f{i}" for i in range(1, depth + 1)]
    pattern = "(s)" + "".join(f"-[{rels[i]}:FLOWS_TO]->({n})" for i, n in enumerate(inner))
    pattern += f"-[{rels[-1]}:FLOWS_TO]->(s)"
    conds = [f"{n}.sccId = s.sccId AND {n} <> s"
             + (f" AND NOT {n} IN [{', '.join(inner[:i])}]" if i else "")
             for i, n in enumerate(inner)]
    return (
        f"MATCH (s:Account {{accountId: $start}}) MATCH {pattern} WHERE " + " AND ".join(conds)
        + f" RETURN [x IN [s, {', '.join(inner)}] | x.accountId] AS accounts,"
        + f" [f IN [{', '.join(rels)}] | {{txCount: f.txCount,"
        + " totalUsd: reduce(t = 0.0, u IN f.usd | t + u)}] AS hops LIMIT $limit"
    )


@router.get("/cycles", summary="Live search: rings through one account (FLOWS_TO within its SCC)")
def cycles(
    start_account: str = Query(..., description="Account to search from"),
    max_hops: int = Query(6, ge=2, le=8),
    limit: int = Query(25, ge=1, le=100),
):
    if _require_account(start_account) is None:
        return {"startAccount": start_account, "maxHops": max_hops, "count": 0, "rings": [],
                "graph": {"nodes": [], "links": []}, "note": "Account has no sccId (not in any cycle)"}
    rings = []
    for depth in range(2, max_hops + 1):
        if len(rings) >= limit:
            break
        rings += rows(_cycle_query(depth), {"start": start_account, "limit": limit - len(rings)})

    nodes, links = {}, []
    for ring in rings:
        accs = ring["accounts"]
        for i, acc in enumerate(accs):
            nodes[acc] = {"id": acc}
            links.append({"source": acc, "target": accs[(i + 1) % len(accs)], **ring["hops"][i]})
    return {
        "startAccount": start_account, "maxHops": max_hops, "count": len(rings),
        "rings": [{"accounts": r["accounts"], "length": len(r["accounts"]), "hops": r["hops"]}
                  for r in rings],
        "graph": {"nodes": list(nodes.values()), "links": links},
    }


@router.get("/risk-histogram", summary="How many accounts fall in each risk-score band")
def risk_histogram(bins: int = Query(20, ge=5, le=100)):
    return rows(
        """
        MATCH (a:Account) WHERE a.riskScore IS NOT NULL
        WITH toInteger(a.riskScore / (100.0 / $bins)) AS b
        WITH CASE WHEN b >= $bins THEN $bins - 1 ELSE b END AS b
        RETURN b * (100.0 / $bins) AS bandStart, count(*) AS accounts
        ORDER BY bandStart
        """,
        {"bins": bins},
    )


@router.get("/chains", summary="Live search: time-ordered layering chains from one account")
def chains(
    start_account: str = Query(...),
    min_hops: int = Query(3, ge=2, le=6),
    max_hops: int = Query(5, ge=2, le=6),
    limit: int = Query(10, ge=1, le=50),
):
    if min_hops > max_hops:
        raise HTTPException(422, "min_hops must be <= max_hops")
    _require_account(start_account)
    result = rows(
        f"""
        MATCH (a:Account {{accountId: $start}})
        MATCH path = (a)-[r:SENT]->{{{min_hops},{max_hops}}}(b:Account)
        WHERE a <> b
          AND all(i IN range(0, size(r) - 2) WHERE r[i].timestamp <= r[i + 1].timestamp)
          AND all(n IN nodes(path) WHERE single(m IN nodes(path) WHERE m = n))
        RETURN [n IN nodes(path) | n.accountId] AS accounts,
               [x IN r | x {{ .transactionId, .timestamp, .amountPaid, .paymentCurrency }}] AS hops
        LIMIT $limit
        """,
        {"start": start_account, "limit": limit},
    )
    nodes, links = {}, []
    for chain in result:
        accs = chain["accounts"]
        for acc in accs:
            nodes[acc] = {"id": acc}
        links += [{"source": accs[i], "target": accs[i + 1], **hop} for i, hop in enumerate(chain["hops"])]
    return {"count": len(result), "chains": result,
            "graph": {"nodes": list(nodes.values()), "links": links}}
