"""Transactions (SENT): CRUD that keeps the FLOWS_TO pair roll-up in sync."""
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import rows
from ..fx import USD_PER_UNIT, Currency

router = APIRouter(prefix="/transactions", tags=["Transactions"])

TX_RETURN = "RETURN r { .*, from: a.accountId, to: b.accountId } AS transaction"

# Rebuild one pair's FLOWS_TO from its SENT relationships, exactly as
# graph_queries/4a1 built it: time-ordered ts / usd / laund lists + txCount.
# Recomputing (not incrementing) means it can never drift.
SYNC_PAIR = """
MATCH (a:Account {accountId: $from}), (b:Account {accountId: $to})
WHERE a <> b
OPTIONAL MATCH (a)-[s:SENT]->(b)
WITH a, b, s ORDER BY s.timestamp
WITH a, b, collect(s.timestamp) AS ts,
     collect(s.amountPaid * $fx[s.paymentCurrency]) AS usd,
     collect(s.isLaundering) AS laund
OPTIONAL MATCH (a)-[f:FLOWS_TO]->(b)
FOREACH (_ IN CASE WHEN size(ts) = 0 AND f IS NOT NULL THEN [1] ELSE [] END | DELETE f)
FOREACH (_ IN CASE WHEN size(ts) > 0 THEN [1] ELSE [] END |
  MERGE (a)-[g:FLOWS_TO]->(b)
  SET g.ts = ts, g.usd = usd, g.laund = laund, g.txCount = size(ts))
"""


def sync_pair(from_id: str, to_id: str) -> None:
    rows(SYNC_PAIR, {"from": from_id, "to": to_id, "fx": USD_PER_UNIT})


class TransactionIn(BaseModel):
    fromAccountId: str = Field(examples=["999_DEMO1"])
    toAccountId: str = Field(examples=["999_DEMO2"])
    amountPaid: float = Field(gt=0, examples=[2500.0])
    paymentCurrency: Currency = "US Dollar"
    amountReceived: Optional[float] = Field(None, gt=0, description="Defaults to amountPaid")
    receivingCurrency: Optional[Currency] = Field(None, description="Defaults to paymentCurrency")
    paymentFormat: str = "ACH"
    timestamp: Optional[datetime] = Field(None, description="Defaults to now (UTC)")
    isLaundering: Literal[0, 1] = 0


class TransactionPatch(BaseModel):
    amountPaid: Optional[float] = Field(None, gt=0)
    paymentCurrency: Optional[Currency] = None
    paymentFormat: Optional[str] = None
    isLaundering: Optional[Literal[0, 1]] = None


@router.get("", summary="Transactions of one account")
def list_transactions(
    account_id: str,
    direction: Literal["out", "in", "both"] = "both",
    limit: int = Query(50, ge=1, le=500),
):
    arrow = {"out": "-[r:SENT]->", "in": "<-[r:SENT]-", "both": "-[r:SENT]-"}[direction]
    result = rows(
        f"MATCH (:Account {{accountId: $id}}){arrow}(:Account) "
        "WITH r, startNode(r) AS a, endNode(r) AS b ORDER BY r.timestamp DESC LIMIT $limit "
        + TX_RETURN,
        {"id": account_id, "limit": limit},
    )
    return {"count": len(result), "transactions": [r["transaction"] for r in result]}


@router.get("/{transaction_id}", summary="One transaction")
def get_transaction(transaction_id: str):
    result = rows("MATCH (a)-[r:SENT {transactionId: $id}]->(b) " + TX_RETURN, {"id": transaction_id})
    if not result:
        raise HTTPException(404, f"Transaction '{transaction_id}' not found")
    return result[0]["transaction"]


@router.post("", status_code=201, summary="Create a transaction (updates FLOWS_TO)")
def create_transaction(body: TransactionIn):
    ts = (body.timestamp or datetime.now(timezone.utc)).isoformat()
    result = rows(
        """
        MATCH (a:Account {accountId: $from}), (b:Account {accountId: $to})
        CREATE (a)-[r:SENT {
          transactionId: $id, timestamp: datetime($ts),
          amountPaid: $amountPaid, amountReceived: $amountReceived,
          paymentCurrency: $paymentCurrency, receivingCurrency: $receivingCurrency,
          paymentFormat: $paymentFormat, isLaundering: $isLaundering
        }]->(b)
        """ + TX_RETURN,
        {"from": body.fromAccountId, "to": body.toAccountId, "id": f"api-{uuid4().hex[:12]}",
         "ts": ts, "amountPaid": body.amountPaid,
         "amountReceived": body.amountReceived or body.amountPaid,
         "paymentCurrency": body.paymentCurrency,
         "receivingCurrency": body.receivingCurrency or body.paymentCurrency,
         "paymentFormat": body.paymentFormat, "isLaundering": body.isLaundering},
    )
    if not result:
        raise HTTPException(404, "fromAccountId or toAccountId does not exist")
    sync_pair(body.fromAccountId, body.toAccountId)
    return result[0]["transaction"]


@router.patch("/{transaction_id}", summary="Update a transaction (updates FLOWS_TO)")
def update_transaction(transaction_id: str, body: TransactionPatch):
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(422, "Nothing to update")
    result = rows("MATCH (a)-[r:SENT {transactionId: $id}]->(b) SET r += $changes " + TX_RETURN,
                  {"id": transaction_id, "changes": changes})
    if not result:
        raise HTTPException(404, f"Transaction '{transaction_id}' not found")
    tx = result[0]["transaction"]
    sync_pair(tx["from"], tx["to"])
    return tx


@router.delete("/{transaction_id}", summary="Delete a transaction (updates FLOWS_TO)")
def delete_transaction(transaction_id: str):
    result = rows(
        """
        MATCH (a)-[r:SENT {transactionId: $id}]->(b)
        WITH a.accountId AS fromId, b.accountId AS toId, r
        DELETE r
        RETURN fromId, toId
        """,
        {"id": transaction_id},
    )
    if not result:
        raise HTTPException(404, f"Transaction '{transaction_id}' not found")
    sync_pair(result[0]["fromId"], result[0]["toId"])
    return {"deleted": transaction_id}
