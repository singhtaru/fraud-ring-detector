"""FastAPI entry point.  Run:  uvicorn app.main:app --reload --host 127.0.0.1
Interactive documentation: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from .db import rows
from .routers import accounts, analysis, rings, transactions

app = FastAPI(
    title="Fraud Ring Detector API",
    version="0.3.0",
    description="Graph-based money-laundering ring detection on IBM AML HI-Small (Neo4j). "
                "Full-graph detection is precomputed into :Detection nodes; searches anchored "
                "on one account run live.",
)

# Lets the Phase 10 React dev server (Vite, port 5173) call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceUnavailable)
def neo4j_down(request: Request, exc: ServiceUnavailable):
    return JSONResponse(status_code=503, content={"detail": "Neo4j is not reachable. Is the instance running?"})


@app.exception_handler(Neo4jError)
def neo4j_error(request: Request, exc: Neo4jError):
    # Includes query timeouts (see QUERY_TIMEOUT_S in db.py).
    return JSONResponse(status_code=503, content={"detail": exc.message, "code": exc.code})


@app.get("/health", tags=["Health"], summary="API and Neo4j status")
def health():
    rows("RETURN 1 AS ok")
    return {"status": "ok"}


app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(rings.router)
app.include_router(analysis.router)
