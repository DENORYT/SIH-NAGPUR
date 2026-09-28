#!/usr/bin/env python3
"""
ShadowLink -- Module Test Runner
Loads seed data into an in-memory SQLite database (no PostgreSQL needed),
then runs all three detection modules and prints results.

Usage:
    cd backend
    .\\venv\\Scripts\\python.exe run_modules.py
"""

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
SEED_DIR = BACKEND_DIR / "app" / "seed"

# Ensure app package is importable
sys.path.insert(0, str(BACKEND_DIR))

from app.modules import infra_matcher, identity_graph, stylometry  # noqa: E402

# ---------------------------------------------------------------------------
# SQLite-compatible schema (no ENUM / INET / JSONB / gen_random_uuid)
# The identifiers table intentionally omits UNIQUE(type, value) so the
# identity-graph module can discover shared keys via self-join.
# ---------------------------------------------------------------------------

SQLITE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS actors (
        id TEXT PRIMARY KEY,
        primary_handle TEXT NOT NULL,
        first_seen TEXT, last_seen TEXT,
        confidence_score REAL DEFAULT 0,
        risk_category TEXT DEFAULT 'UNKNOWN',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS aliases (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL REFERENCES actors(id),
        handle TEXT NOT NULL, platform TEXT NOT NULL,
        active_from TEXT, active_to TEXT,
        UNIQUE(handle, platform)
    )""",
    """CREATE TABLE IF NOT EXISTS identifiers (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL REFERENCES actors(id),
        alias_id TEXT REFERENCES aliases(id),
        type TEXT NOT NULL,
        value TEXT NOT NULL,
        first_seen TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        alias_id TEXT NOT NULL REFERENCES aliases(id),
        platform TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        raw_text TEXT,
        category TEXT DEFAULT 'UNKNOWN'
    )""",
    """CREATE TABLE IF NOT EXISTS infra_leaks (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL REFERENCES actors(id),
        type TEXT NOT NULL,
        onion_address TEXT,
        matched_clearnet_ip TEXT,
        matched_clearnet_domain TEXT,
        evidence TEXT,
        confidence REAL DEFAULT 0,
        detected_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS trust_links (
        id TEXT PRIMARY KEY,
        actor_a_id TEXT NOT NULL REFERENCES actors(id),
        actor_b_id TEXT NOT NULL REFERENCES actors(id),
        relationship_type TEXT NOT NULL,
        strength_score REAL DEFAULT 0,
        evidence TEXT,
        ai_suggested INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(actor_a_id, actor_b_id, relationship_type)
    )""",
    """CREATE TABLE IF NOT EXISTS ingestion_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT DEFAULT (datetime('now')),
        module TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        summary TEXT,
        duration_ms INTEGER
    )""",
]


def _load_seed(session):
    """Insert actors / aliases / identifiers / posts from seed_dataset.json.
    trust_links and infra_leaks are left EMPTY so the modules discover them.
    """
    with open(SEED_DIR / "seed_dataset.json", encoding="utf-8") as f:
        seed = json.load(f)

    for a in seed["actors"]:
        session.execute(text(
            "INSERT INTO actors (id, primary_handle, first_seen, last_seen,"
            " confidence_score, risk_category, notes)"
            " VALUES (:id,:h,:fs,:ls,:cs,:rc,:n)"
        ), {"id": a["id"], "h": a["primary_handle"],
            "fs": a["first_seen"], "ls": a["last_seen"],
            "cs": a["confidence_score"], "rc": a["risk_category"],
            "n": a["notes"]})

        for al in a["aliases"]:
            session.execute(text(
                "INSERT OR IGNORE INTO aliases"
                " (id, actor_id, handle, platform, active_from, active_to)"
                " VALUES (:id,:aid,:h,:p,:af,:at)"
            ), {"id": al["id"], "aid": a["id"], "h": al["handle"],
                "p": al["platform"], "af": al["active_from"],
                "at": al["active_to"]})

            for ident in al["identifiers"]:
                session.execute(text(
                    "INSERT INTO identifiers"
                    " (id, actor_id, alias_id, type, value, first_seen)"
                    " VALUES (:id,:aid,:alid,:t,:v,:fs)"
                ), {"id": ident["id"], "aid": a["id"], "alid": al["id"],
                    "t": ident["type"], "v": ident["value"],
                    "fs": ident["first_seen"]})

            for p in al["posts"]:
                session.execute(text(
                    "INSERT INTO posts"
                    " (id, alias_id, platform, timestamp, raw_text, category)"
                    " VALUES (:id,:alid,:p,:ts,:txt,:cat)"
                ), {"id": p["id"], "alid": al["id"], "p": p["platform"],
                    "ts": p["timestamp"], "txt": p["raw_text"],
                    "cat": p["category"]})

    session.commit()


def _table_counts(session) -> dict[str, int]:
    tables = ["actors", "aliases", "identifiers", "posts",
              "infra_leaks", "trust_links", "ingestion_log"]
    return {t: session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            for t in tables}


def _print_counts(counts: dict[str, int]):
    print("-" * 40)
    print(f" {'Table':<22} {'Rows':>6}")
    print("-" * 40)
    for t, c in counts.items():
        print(f" {t:<22} {c:>6}")
    print("-" * 40)


def main():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Session = sessionmaker(bind=engine)

    # -- schema --------------------------------------------------------
    with engine.begin() as conn:
        for ddl in SQLITE_SCHEMA:
            conn.execute(text(ddl))

    session = Session()

    print("=" * 56)
    print(" ShadowLink -- Module Test Runner (SQLite)")
    print("=" * 56)

    # -- seed data (no trust_links / infra_leaks) ----------------------
    print("\n[1/6] Loading seed data ...")
    _load_seed(session)
    counts = _table_counts(session)
    print(f"  actors={counts['actors']}  aliases={counts['aliases']}"
          f"  identifiers={counts['identifiers']}  posts={counts['posts']}")
    print("  trust_links and infra_leaks are EMPTY -- modules will"
          " discover them.\n")

    # -- infra_matcher -------------------------------------------------
    print("[2/6] Running infra_matcher ...")
    r1 = infra_matcher.run(session)
    print(f"  Infra leaks found: {r1['matches_found']}")
    for d in r1.get("details", []):
        print(f"    {d['type']:20s}  {d['clearnet']:25s}"
              f"  conf={d['confidence']:.1f}")

    # -- identity_graph ------------------------------------------------
    print("\n[3/6] Running identity_graph ...")
    r2 = identity_graph.run(session)
    print(f"  SAME_PGP/WALLET links: {r2['shared_identifier_links']}")
    print(f"  VOUCHED_FOR links:     {r2['vouched_for_links']}")

    # -- stylometry ----------------------------------------------------
    print("\n[4/6] Running stylometry ...")
    r3 = stylometry.run(session)
    print(f"  STYLE_MATCH links: {r3['matches_found']}")
    for d in r3.get("details", []):
        print(f"    {d['actor_a']} <-> {d['actor_b']}"
              f"  sim={d['similarity']:.4f}")

    # -- final counts --------------------------------------------------
    print("\n[5/6] Final table counts:")
    _print_counts(_table_counts(session))

    # -- graph frontend ------------------------------------------------
    print("\n[6/6] Testing get_graph_for_frontend() ...")
    gd = identity_graph.get_graph_for_frontend(session)
    clusters = set(n["cluster_id"] for n in gd["nodes"])
    print(f"  Nodes:    {len(gd['nodes'])}")
    print(f"  Edges:    {len(gd['edges'])}")
    print(f"  Clusters: {len(clusters)}")

    # -- summary -------------------------------------------------------
    print(f"\n{'='*56}")
    print(" RESULTS SUMMARY")
    print(f"{'='*56}")
    print(f"  Infra leaks (SSL/banner):  {r1['matches_found']:>3}"
          f"  (expected: 3)")
    print(f"  SAME_PGP / SAME_WALLET:    {r2['shared_identifier_links']:>3}"
          f"  (expected: ~8)")
    print(f"  VOUCHED_FOR:               {r2['vouched_for_links']:>3}"
          f"  (expected: 2-3)")
    print(f"  STYLE_MATCH:               {r3['matches_found']:>3}"
          f"  (expected: ~3)")
    print(f"{'='*56}")

    session.close()
    engine.dispose()


if __name__ == "__main__":
    main()
