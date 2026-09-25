"""Stored detections (rings and fans), evaluation summary and risk runs.

bestJaccard and matchedPatterns come from the dataset labels (Phase 7), like
`label` on accounts: they support the evaluation view, not something an
investigator would have in real use.
"""
import json
import sqlite3
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import rows

router = APIRouter(tags=["Rings"])

RING_FIELDS = "d { .detectionId, .method, .target, .size, .avgRisk, .maxRisk, .bestJaccard }"


@router.get("/rings", summary="Stored detections, ranked by their members' risk")
def list_rings(
    method: Optional[str] = Query(None, examples=["cycles_time_amount"]),
    target: Optional[str] = Query(None, examples=["CYCLE"]),
    sort_by: Literal["avgRisk", "maxRisk", "size"] = "avgRisk",
    min_size: int = Query(2, ge=1),
    matched_only: bool = Query(False, description="Only rings matching a labelled pattern (Jaccard >= 0.5)"),
    limit: int = Query(25, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    result = rows(
        f"""
        MATCH (d:Detection)
        WHERE ($method IS NULL OR d.method = $method)
          AND ($target IS NULL OR d.target = $target)
          AND d.size >= $minSize
          AND (NOT $matchedOnly OR d.bestJaccard >= 0.5)
        RETURN {RING_FIELDS} AS ring
        ORDER BY coalesce(d[$sortBy], -1) DESC, d.detectionId SKIP $skip LIMIT $limit
        """,
        {"method": method, "target": target, "minSize": min_size, "matchedOnly": matched_only,
         "sortBy": sort_by, "skip": skip, "limit": limit},
    )
    return {"count": len(result), "rings": [r["ring"] for r in result]}


@router.get("/rings/{detection_id}", summary="One ring: members, risk breakdowns, graph, matched patterns")
def get_ring(detection_id: int):
    result = rows(
        f"""
        MATCH (d:Detection {{detectionId: $id}})
        CALL (d) {{
          MATCH (a:Account)-[:MEMBER_OF]->(d)
          RETURN collect(a {{
            .accountId, .pageRank, .communityId,
            riskScore: a.riskScore, riskCycle: a.riskCycle,
            riskCrossCommunity: a.riskCrossCommunity,
            riskPageRank: a.riskPageRank, riskVelocity: a.riskVelocity
          }}) AS members
        }}
        CALL (d) {{
          MATCH (a:Account)-[:MEMBER_OF]->(d)<-[:MEMBER_OF]-(b:Account)
          MATCH (a)-[f:FLOWS_TO]->(b)
          RETURN collect({{source: a.accountId, target: b.accountId, txCount: f.txCount,
                          totalUsd: reduce(t = 0.0, u IN f.usd | t + u),
                          launderingTxns: reduce(t = 0, x IN f.laund | t + x),
                          firstTs: f.ts[0], lastTs: f.ts[-1]}}) AS links
        }}
        CALL (d) {{
          OPTIONAL MATCH (d)-[m:MATCHES]->(p:Pattern)
          RETURN collect(CASE WHEN p IS NULL THEN null
                 ELSE {{patternId: p.patternId, type: p.type, jaccard: m.jaccard}} END) AS matches
        }}
        RETURN {RING_FIELDS} AS ring, members, links, matches
        """,
        {"id": detection_id},
    )
    if not result:
        raise HTTPException(404, f"Detection {detection_id} not found")
    r = result[0]
    return {
        **r["ring"],
        "matchedPatterns": r["matches"],
        "graph": {"nodes": [{"id": m["accountId"], **m} for m in r["members"]], "links": r["links"]},
    }


@router.get("/accounts/{account_id}/rings", summary="Detections an account belongs to")
def account_rings(account_id: str, limit: int = Query(50, ge=1, le=200)):
    if not rows("MATCH (a:Account {accountId: $id}) RETURN 1 AS ok", {"id": account_id}):
        raise HTTPException(404, f"Account '{account_id}' not found")
    result = rows(
        f"""
        MATCH (:Account {{accountId: $id}})-[:MEMBER_OF]->(d:Detection)
        RETURN {RING_FIELDS} AS ring ORDER BY d.avgRisk DESC LIMIT $limit
        """,
        {"id": account_id, "limit": limit},
    )
    return {"count": len(result), "rings": [r["ring"] for r in result]}


@router.get("/evaluation", summary="Precision, recall and F1 per detection method (Phase 7)")
def evaluation():
    per_method = rows(
        """
        MATCH (d:Detection)
        RETURN d.method AS method, d.target AS target, count(d) AS detections,
               count(CASE WHEN EXISTS { (d)-[:MATCHES]->() } THEN 1 END) AS matched
        ORDER BY method
        """
    )
    found = rows(
        """
        MATCH (p:Pattern)<-[:MATCHES]-(d:Detection)
        RETURN d.method AS method, p.type AS type, count(DISTINCT p) AS n
        """
    )
    labelled = {r["type"]: r["n"] for r in rows("MATCH (p:Pattern) RETURN p.type AS type, count(p) AS n")}
    by_type = {(r["method"], r["type"]): r["n"] for r in found}

    methods = []
    for m in per_method:
        n_target = labelled.get(m["target"], 0)
        rec = by_type.get((m["method"], m["target"]), 0)
        distinct = sum(n for (meth, _), n in by_type.items() if meth == m["method"])
        p = m["matched"] / m["detections"] if m["detections"] else 0.0
        r = rec / n_target if n_target else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        methods.append({
            **m, "precision": round(p, 4), "targetRecalled": rec, "targetLabelled": n_target,
            "recall": round(r, 4), "f1": round(f1, 4), "distinctPatternsFound": distinct,
            # Review effort per real pattern found; per-detection precision alone
            # rewards finding the same large pattern many times (Phase 7).
            "detectionsPerPatternFound": round(m["detections"] / distinct, 1) if distinct else None,
        })
    return {"jaccardThreshold": 0.5, "methods": methods, "labelledByType": labelled}


@router.get("/runs/latest", summary="The most recent risk-score run and its weights")
def latest_run():
    # risk_score.py logs every run to SQLite (fraud.db), not to the graph.
    try:
        con = sqlite3.connect("fraud.db")
        row = con.execute("SELECT run_id, created_at, config_json, bounds_json FROM risk_runs "
                          "ORDER BY run_id DESC LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        raise HTTPException(404, "No risk runs found (run risk_score.py)")
    config = json.loads(row[2])
    return {"runId": row[0], "createdAt": row[1], "weights": config["weights"],
            "config": config, "normalisationBounds": json.loads(row[3])}
