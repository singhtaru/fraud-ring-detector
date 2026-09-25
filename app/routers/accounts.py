"""Accounts: CRUD plus a grouped view of graph metrics and the risk breakdown."""
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import rows

router = APIRouter(prefix="/accounts", tags=["Accounts"])

ReviewStatus = Literal["unreviewed", "under_review", "cleared", "escalated"]

# Grouped so a score reads as its named parts (NFR 7). `label` is the
# dataset's ground truth, shown for demonstration; the risk score never uses it.
ACCOUNT_RETURN = """
RETURN a {
  .accountId, .bankId, .accountNumber, .notes,
  reviewStatus: coalesce(a.reviewStatus, 'unreviewed'),
  sentCount: COUNT { (a)-[:SENT]->() },
  receivedCount: COUNT { (a)<-[:SENT]-() },
  graph: {
    pageRank: a.pageRank, communityId: a.communityId,
    componentId: a.componentId, sccId: a.sccId,
    inCycle: coalesce(a.inCycle, false)
  },
  risk: {
    score: a.riskScore, cycle: a.riskCycle,
    crossCommunity: a.riskCrossCommunity,
    pageRank: a.riskPageRank, velocity: a.riskVelocity,
    runId: a.riskRunId
  },
  ringCount: COUNT { (a)-[:MEMBER_OF]->(:Detection) },
  label: {
    launderingInvolved: a.evalLaunderingInvolved,
    patternTypes: COLLECT { MATCH (a)-[:IN_PATTERN]->(p:Pattern) RETURN p.type }
  }
} AS account
"""


class AccountIn(BaseModel):
    bankId: str = Field(examples=["999"])
    accountNumber: str = Field(examples=["DEMO1"])
    notes: Optional[str] = None


class AccountPatch(BaseModel):
    notes: Optional[str] = None
    reviewStatus: Optional[ReviewStatus] = None


def _get(account_id):
    result = rows("MATCH (a:Account {accountId: $id})" + ACCOUNT_RETURN, {"id": account_id})
    if not result:
        raise HTTPException(404, f"Account '{account_id}' not found")
    return result[0]["account"]


@router.get("", summary="List accounts, highest risk (or PageRank) first")
def list_accounts(
    sort_by: Literal["riskScore", "pageRank"] = "riskScore",
    in_cycle: Optional[bool] = None,
    review_status: Optional[ReviewStatus] = None,
    limit: int = Query(25, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    # sort_by is a validated literal, so it is safe to place in the query text;
    # the IS NOT NULL lets Neo4j walk the property index in order.
    result = rows(
        f"""
        MATCH (a:Account) WHERE a.{sort_by} IS NOT NULL
          AND ($inCycle IS NULL OR coalesce(a.inCycle, false) = $inCycle)
          AND ($status IS NULL OR coalesce(a.reviewStatus, 'unreviewed') = $status)
        WITH a ORDER BY a.{sort_by} DESC SKIP $skip LIMIT $limit
        """ + ACCOUNT_RETURN,
        {"inCycle": in_cycle, "status": review_status, "skip": skip, "limit": limit},
    )
    return {"count": len(result), "accounts": [r["account"] for r in result]}


@router.get("/{account_id}", summary="One account with its risk breakdown")
def get_account(account_id: str):
    return _get(account_id)


@router.get("/{account_id}/graph", summary="Direct counterparties as {nodes, links}")
def account_graph(account_id: str, limit: int = Query(50, ge=1, le=200)):
    centre = _get(account_id)
    result = rows(
        """
        MATCH (a:Account {accountId: $id})-[f:FLOWS_TO]-(b:Account)
        WITH a, b, f ORDER BY f.txCount DESC LIMIT $limit
        RETURN b { .accountId, riskScore: b.riskScore, inCycle: coalesce(b.inCycle, false) } AS node,
               {source: startNode(f).accountId, target: endNode(f).accountId,
                txCount: f.txCount, totalUsd: reduce(t = 0.0, u IN f.usd | t + u)} AS link
        """,
        {"id": account_id, "limit": limit},
    )
    nodes = {account_id: {"id": account_id, "riskScore": centre["risk"]["score"],
                          "inCycle": centre["graph"]["inCycle"]}}
    for r in result:
        nodes[r["node"]["accountId"]] = {"id": r["node"]["accountId"], **r["node"]}
    return {"nodes": list(nodes.values()), "links": [r["link"] for r in result]}


@router.post("", status_code=201, summary="Create an account")
def create_account(body: AccountIn):
    account_id = f"{body.bankId}_{body.accountNumber}"
    if rows("MATCH (a:Account {accountId: $id}) RETURN 1 AS ok", {"id": account_id}):
        raise HTTPException(409, f"Account '{account_id}' already exists")
    rows(
        """
        CREATE (a:Account {accountId: $id, bankId: $bank, accountNumber: $number,
                           notes: $notes, reviewStatus: 'unreviewed'})
        """,
        {"id": account_id, "bank": body.bankId, "number": body.accountNumber, "notes": body.notes},
    )
    return _get(account_id)


@router.patch("/{account_id}", summary="Update notes or review status")
def update_account(account_id: str, body: AccountPatch):
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(422, "Nothing to update")
    _get(account_id)
    rows("MATCH (a:Account {accountId: $id}) SET a += $changes", {"id": account_id, "changes": changes})
    return _get(account_id)


@router.delete("/{account_id}", summary="Delete an account and all its transactions")
def delete_account(account_id: str):
    # DETACH DELETE also removes its FLOWS_TO and MEMBER_OF links. Stored
    # detections keep their old size: they are a snapshot of a detection run.
    result = rows(
        """
        MATCH (a:Account {accountId: $id})
        WITH a, COUNT { (a)-[:SENT]-() } AS transactions
        DETACH DELETE a
        RETURN transactions
        """,
        {"id": account_id},
    )
    if not result:
        raise HTTPException(404, f"Account '{account_id}' not found")
    return {"deleted": account_id, "transactionsDeleted": result[0]["transactions"]}
