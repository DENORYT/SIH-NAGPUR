#!/usr/bin/env python3
"""
ShadowLink -- Offline verification of seed data using SQLite.
Proves the data is structurally valid without needing PostgreSQL.

Run this AFTER generate_seed.py to validate the seed dataset.
"""

import json
import sqlite3
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SEED_FILE = SCRIPT_DIR / "seed_dataset.json"
CLEARNET_FILE = SCRIPT_DIR / "clearnet_servers.json"

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS actors (
    id TEXT PRIMARY KEY,
    primary_handle TEXT NOT NULL,
    first_seen TEXT,
    last_seen TEXT,
    confidence_score REAL DEFAULT 0,
    risk_category TEXT DEFAULT 'UNKNOWN',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS aliases (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL REFERENCES actors(id),
    handle TEXT NOT NULL,
    platform TEXT NOT NULL,
    active_from TEXT,
    active_to TEXT,
    UNIQUE(handle, platform)
);

CREATE TABLE IF NOT EXISTS identifiers (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL REFERENCES actors(id),
    alias_id TEXT REFERENCES aliases(id),
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    first_seen TEXT,
    UNIQUE(type, value)
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    alias_id TEXT NOT NULL REFERENCES aliases(id),
    platform TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    raw_text TEXT,
    category TEXT DEFAULT 'UNKNOWN'
);

CREATE TABLE IF NOT EXISTS infra_leaks (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL REFERENCES actors(id),
    type TEXT NOT NULL,
    onion_address TEXT,
    matched_clearnet_ip TEXT,
    matched_clearnet_domain TEXT,
    evidence TEXT,
    confidence REAL DEFAULT 0,
    detected_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trust_links (
    id TEXT PRIMARY KEY,
    actor_a_id TEXT NOT NULL REFERENCES actors(id),
    actor_b_id TEXT NOT NULL REFERENCES actors(id),
    relationship_type TEXT NOT NULL,
    strength_score REAL DEFAULT 0,
    evidence TEXT,
    ai_suggested INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(actor_a_id, actor_b_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT DEFAULT (datetime('now')),
    module TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    summary TEXT,
    duration_ms INTEGER
);
"""


def main():
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        seed = json.load(f)
    with open(CLEARNET_FILE, "r", encoding="utf-8") as f:
        clearnet = json.load(f)

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Apply schema
    cur.executescript(SQLITE_SCHEMA)
    print("[OK] Schema applied (SQLite in-memory)\n")

    # Insert actors
    for a in seed["actors"]:
        cur.execute(
            "INSERT INTO actors (id, primary_handle, first_seen, last_seen, "
            "confidence_score, risk_category, notes) VALUES (?,?,?,?,?,?,?)",
            (a["id"], a["primary_handle"], a["first_seen"], a["last_seen"],
             a["confidence_score"], a["risk_category"], a["notes"]),
        )

    # Insert aliases
    for a in seed["actors"]:
        for al in a["aliases"]:
            cur.execute(
                "INSERT INTO aliases (id, actor_id, handle, platform, "
                "active_from, active_to) VALUES (?,?,?,?,?,?)",
                (al["id"], a["id"], al["handle"], al["platform"],
                 al["active_from"], al["active_to"]),
            )

    # Insert identifiers (ON CONFLICT IGNORE for shared-key duplicates)
    id_ok, id_dup = 0, 0
    for a in seed["actors"]:
        for al in a["aliases"]:
            for ident in al["identifiers"]:
                try:
                    cur.execute(
                        "INSERT INTO identifiers (id, actor_id, alias_id, "
                        "type, value, first_seen) VALUES (?,?,?,?,?,?)",
                        (ident["id"], a["id"], al["id"],
                         ident["type"], ident["value"], ident["first_seen"]),
                    )
                    id_ok += 1
                except sqlite3.IntegrityError:
                    id_dup += 1

    # Insert posts
    for a in seed["actors"]:
        for al in a["aliases"]:
            for p in al["posts"]:
                cur.execute(
                    "INSERT INTO posts (id, alias_id, platform, timestamp, "
                    "raw_text, category) VALUES (?,?,?,?,?,?)",
                    (p["id"], al["id"], p["platform"],
                     p["timestamp"], p["raw_text"], p["category"]),
                )

    # Insert trust_links from ground truth
    gt = seed["ground_truth"]
    for pair in gt["shared_identifier_pairs"]:
        link_type = ("SAME_PGP" if pair["shared_identifier_type"] == "PGP_KEY"
                     else "SAME_WALLET")
        cur.execute(
            "INSERT INTO trust_links (id, actor_a_id, actor_b_id, "
            "relationship_type, strength_score, evidence, ai_suggested) "
            "VALUES (?,?,?,?,?,?,0)",
            (str(uuid.uuid4()), pair["actor_a_id"], pair["actor_b_id"],
             link_type, 95.0,
             json.dumps({"shared_value": pair["shared_identifier_value"],
                         "type": pair["shared_identifier_type"]})),
        )
    for pair in gt["rebranded_persona_pairs"]:
        cur.execute(
            "INSERT INTO trust_links (id, actor_a_id, actor_b_id, "
            "relationship_type, strength_score, evidence, ai_suggested) "
            "VALUES (?,?,?,?,?,?,1)",
            (str(uuid.uuid4()), pair["actor_a_id"], pair["actor_b_id"],
             "STYLE_MATCH", 82.5,
             json.dumps({"shared_style": pair["shared_style"]})),
        )

    # Insert infra_leaks
    for match in gt["infra_leak_matches"]:
        cur.execute(
            "INSERT INTO infra_leaks (id, actor_id, type, onion_address, "
            "matched_clearnet_ip, matched_clearnet_domain, evidence, "
            "confidence) VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), match["actor_id"], match["match_type"],
             match["onion_address"], match["clearnet_ip"],
             match["clearnet_domain"],
             json.dumps({"matched_value": match["matched_value"]}), 92.5),
        )

    # Ingestion log
    cur.execute(
        "INSERT INTO ingestion_log (module, status, summary, duration_ms) "
        "VALUES (?,?,?,?)",
        ("verify_seed", "SUCCESS",
         json.dumps(seed["metadata"]["counts"]), 0),
    )
    conn.commit()

    # Print table counts
    tables = ["actors", "aliases", "identifiers", "posts",
              "infra_leaks", "trust_links", "ingestion_log"]
    print("-" * 40)
    print(f" {'Table':<22} {'Rows':>6}")
    print("-" * 40)
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f" {t:<22} {cur.fetchone()[0]:>6}")
    print("-" * 40)

    # Verification assertions
    cur.execute("SELECT COUNT(*) FROM actors")
    actor_count = cur.fetchone()[0]
    assert actor_count == 18, f"Expected 18 actors, got {actor_count}"

    cur.execute("SELECT COUNT(*) FROM trust_links WHERE relationship_type IN ('SAME_PGP','SAME_WALLET')")
    shared_links = cur.fetchone()[0]
    assert shared_links == 8, f"Expected 8 shared-id trust_links, got {shared_links}"

    cur.execute("SELECT COUNT(*) FROM trust_links WHERE relationship_type = 'STYLE_MATCH'")
    style_links = cur.fetchone()[0]
    assert style_links == 3, f"Expected 3 style-match trust_links, got {style_links}"

    cur.execute("SELECT COUNT(*) FROM infra_leaks")
    infra_count = cur.fetchone()[0]
    assert infra_count == 3, f"Expected 3 infra_leaks, got {infra_count}"

    print(f"\n  Identifier duplicates (shared keys): {id_dup}")
    print(f"\n[PASS] All assertions passed:")
    print(f"  actors          = 18")
    print(f"  shared-id links = 8")
    print(f"  style links     = 3")
    print(f"  infra leaks     = 3")

    conn.close()


if __name__ == "__main__":
    main()
