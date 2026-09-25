"""Neo4j access for the API: one shared driver, configured from .env."""
import os

from neo4j import GraphDatabase, Query
from neo4j.time import Date, DateTime, Duration, Time

QUERY_TIMEOUT_S = 30  # no request may hold the database longer than this


def _read_env(path=".env"):
    env = dict(os.environ)
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip())
    return env


_env = _read_env()
driver = GraphDatabase.driver(_env.get("NEO4J_URI", "neo4j://127.0.0.1:7687"),
                              auth=(_env.get("NEO4J_USER", "neo4j"), _env["NEO4J_PASSWORD"]))
DATABASE = _env.get("NEO4J_DATABASE", "neo4j")


def clean(value):
    """Convert Neo4j temporal values to ISO strings so responses are JSON-serialisable."""
    if isinstance(value, (DateTime, Date, Time)):
        return value.iso_format()
    if isinstance(value, Duration):
        return str(value)
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def rows(query, params=None, timeout=QUERY_TIMEOUT_S):
    """Run a query and return its records as plain dicts."""
    with driver.session(database=DATABASE) as session:
        return [clean(r.data()) for r in session.run(Query(query, timeout=timeout), params or {})]
