#!/usr/bin/env python3
"""
ShadowLink — Seed Data Loader
Reads seed_dataset.json + clearnet_servers.json → PostgreSQL.
Applies schema.sql first, then inserts in FK-safe order.
"""

import json
import os
import sys
import uuid
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ── Paths ────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[1]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/shadowlink",
)

SEED_FILE    = SCRIPT_DIR / "seed_dataset.json"
CLEARNET_FILE = SCRIPT_DIR / "clearnet_servers.json"
SCHEMA_FILE  = SCRIPT_DIR.parent / "models" / "schema.sql"


def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # ── Load files ───────────────────────────────────────────
    seed = load_json(SEED_FILE)
    clearnet = load_json(CLEARNET_FILE)
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    print("Connecting to database ...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ── 1. Apply schema ──────────────────────────────────
        print("  Applying schema.sql ...")
        cur.execute(schema_sql)
        conn.commit()
        print("  [OK] Schema applied\n")

        # ── 2. Insert actors ─────────────────────────────────
        actor_rows = 0
        for a in seed["actors"]:
            cur.execute(
                """INSERT INTO actors
                       (id, primary_handle, first_seen, last_seen,
                        confidence_score, risk_category, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""",
                (a["id"], a["primary_handle"], a["first_seen"],
                 a["last_seen"], a["confidence_score"],
                 a["risk_category"], a["notes"]),
            )
            actor_rows += cur.rowcount
        conn.commit()
        print(f"  actors:       {actor_rows} inserted")

        # ── 3. Insert aliases ────────────────────────────────
        alias_rows = 0
        for a in seed["actors"]:
            for al in a["aliases"]:
                cur.execute(
                    """INSERT INTO aliases
                           (id, actor_id, handle, platform,
                            active_from, active_to)
                       VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (handle, platform) DO NOTHING""",
                    (al["id"], a["id"], al["handle"],
                     al["platform"], al["active_from"], al["active_to"]),
                )
                alias_rows += cur.rowcount
        conn.commit()
        print(f"  aliases:      {alias_rows} inserted")

        # ── 4. Insert identifiers ────────────────────────────
        id_ok, id_dup = 0, 0
        for a in seed["actors"]:
            for al in a["aliases"]:
                for ident in al["identifiers"]:
                    cur.execute(
                        """INSERT INTO identifiers
                               (id, actor_id, alias_id, type, value, first_seen)
                           VALUES (%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (type, value) DO NOTHING""",
                        (ident["id"], a["id"], al["id"],
                         ident["type"], ident["value"],
                         ident["first_seen"]),
                    )
                    if cur.rowcount:
                        id_ok += 1
                    else:
                        id_dup += 1
        conn.commit()
        print(f"  identifiers:  {id_ok} inserted  ({id_dup} shared-key duplicates skipped)")

        # ── 5. Insert posts ──────────────────────────────────
        post_rows = 0
        for a in seed["actors"]:
            for al in a["aliases"]:
                for p in al["posts"]:
                    cur.execute(
                        """INSERT INTO posts
                               (id, alias_id, platform, timestamp,
                                raw_text, category)
                           VALUES (%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (id) DO NOTHING""",
                    (p["id"], al["id"], p["platform"],
                     p["timestamp"], p["raw_text"], p["category"]),
                    )
                    post_rows += cur.rowcount
        conn.commit()
        print(f"  posts:        {post_rows} inserted")

        # ── 6. Insert trust_links from ground truth ──────────
        gt = seed["ground_truth"]
        tl_rows = 0
        for pair in gt["shared_identifier_pairs"]:
            link_type = (
                "SAME_PGP" if pair["shared_identifier_type"] == "PGP_KEY"
                else "SAME_WALLET"
            )
            cur.execute(
                """INSERT INTO trust_links
                       (id, actor_a_id, actor_b_id, relationship_type,
                        strength_score, evidence, ai_suggested)
                   VALUES (%s,%s,%s,%s,%s,%s, FALSE)
                   ON CONFLICT (actor_a_id, actor_b_id, relationship_type)
                   DO NOTHING""",
                (str(uuid.uuid4()), pair["actor_a_id"], pair["actor_b_id"],
                 link_type, 95.00,
                 json.dumps({
                     "shared_value": pair["shared_identifier_value"],
                     "type": pair["shared_identifier_type"],
                 })),
            )
            tl_rows += cur.rowcount

        # Also insert STYLE_MATCH links for rebranded pairs
        for pair in gt["rebranded_persona_pairs"]:
            cur.execute(
                """INSERT INTO trust_links
                       (id, actor_a_id, actor_b_id, relationship_type,
                        strength_score, evidence, ai_suggested)
                   VALUES (%s,%s,%s,%s,%s,%s, TRUE)
                   ON CONFLICT (actor_a_id, actor_b_id, relationship_type)
                   DO NOTHING""",
                (str(uuid.uuid4()), pair["actor_a_id"], pair["actor_b_id"],
                 "STYLE_MATCH", 82.50,
                 json.dumps({"shared_style": pair["shared_style"]})),
            )
            tl_rows += cur.rowcount
        conn.commit()
        print(f"  trust_links:  {tl_rows} inserted")

        # ── 7. Insert infra_leaks ────────────────────────────
        il_rows = 0
        for match in gt["infra_leak_matches"]:
            cur.execute(
                """INSERT INTO infra_leaks
                       (id, actor_id, type, onion_address,
                        matched_clearnet_ip, matched_clearnet_domain,
                        evidence, confidence)
                   VALUES (%s,%s,%s,%s,%s::inet,%s,%s,%s)""",
                (str(uuid.uuid4()), match["actor_id"],
                 match["match_type"], match["onion_address"],
                 match["clearnet_ip"], match["clearnet_domain"],
                 json.dumps({"matched_value": match["matched_value"]}),
                 92.50),
            )
            il_rows += cur.rowcount
        conn.commit()
        print(f"  infra_leaks:  {il_rows} inserted")

        # ── 8. Log the ingestion ─────────────────────────────
        cur.execute(
            """INSERT INTO ingestion_log (module, status, summary, duration_ms)
               VALUES (%s, %s, %s, %s)""",
            ("seed_loader", "SUCCESS",
             json.dumps(seed["metadata"]["counts"]), 0),
        )
        conn.commit()

        # ── 9. Print final counts ────────────────────────────
        tables = [
            "actors", "aliases", "identifiers", "posts",
            "infra_leaks", "trust_links", "ingestion_log",
        ]
        print(f"\n{'-'*40}")
        print(f" {'Table':<22} {'Rows':>6}")
        print(f"{'-'*40}")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")  # noqa: S608
            print(f" {t:<22} {cur.fetchone()[0]:>6}")
        print(f"{'-'*40}")
        print("\n  Seed data loaded successfully!")

    except Exception as exc:
        conn.rollback()
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
