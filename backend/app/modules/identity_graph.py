"""
ShadowLink -- Identity Graph Module
Builds an actor-correlation graph from shared cryptographic identifiers
(PGP keys, wallet addresses) using NetworkX.

SYNTHETIC DATA ONLY -- all identifiers are fictional.
"""

import json
import uuid

import networkx as nx
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_shared_identifiers(session) -> list[dict]:
    """Self-join on identifiers to find (actor_a, actor_b) pairs that
    share the same PGP key or wallet address."""
    rows = session.execute(
        text(
            "SELECT i1.actor_id, i2.actor_id, i1.type, i1.value "
            "FROM identifiers i1 "
            "JOIN identifiers i2 "
            "  ON i1.type  = i2.type "
            " AND i1.value = i2.value "
            " AND i1.actor_id < i2.actor_id"
        )
    ).fetchall()

    seen: set[tuple] = set()
    pairs: list[dict] = []
    for r in rows:
        key = (r[0], r[1], r[2])
        if key not in seen:
            seen.add(key)
            pairs.append({
                "actor_a_id": r[0],
                "actor_b_id": r[1],
                "type": r[2],
                "value": r[3],
            })
    return pairs


def _get_all_actors(session) -> list[dict]:
    rows = session.execute(
        text("SELECT id, primary_handle, confidence_score, risk_category "
             "FROM actors")
    ).fetchall()
    return [
        {"id": r[0], "handle": r[1],
         "confidence": float(r[2]), "risk": r[3]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(session) -> dict:
    """Discover shared-identifier links, add VOUCHED_FOR edges, write
    everything into ``trust_links``.

    Returns a summary dict.
    """
    # ── Shared identifiers ───────────────────────────────────
    shared_pairs = _find_shared_identifiers(session)
    link_count = 0

    for pair in shared_pairs:
        link_type = (
            "SAME_PGP" if pair["type"] == "PGP_KEY" else "SAME_WALLET"
        )
        strength = 95.0 if pair["type"] == "PGP_KEY" else 90.0

        session.execute(
            text(
                "INSERT INTO trust_links"
                "  (id, actor_a_id, actor_b_id, relationship_type,"
                "   strength_score, evidence, ai_suggested)"
                " VALUES (:id, :a, :b, :type, :str, :ev, 0)"
                " ON CONFLICT (actor_a_id, actor_b_id, relationship_type)"
                " DO NOTHING"
            ),
            {
                "id": str(uuid.uuid4()),
                "a": pair["actor_a_id"],
                "b": pair["actor_b_id"],
                "type": link_type,
                "str": strength,
                "ev": json.dumps({
                    "shared_value": pair["value"],
                    "identifier_type": pair["type"],
                }),
            },
        )
        link_count += 1

    # ── Synthetic VOUCHED_FOR edges ──────────────────────────
    actors = _get_all_actors(session)
    vouch_count = 0
    if len(actors) >= 13:
        vouch_list = [
            (actors[0], actors[2],
             "Forum endorsement in CipherForum thread #4421"),
            (actors[4], actors[6],
             "Mutual vendor review on Nighthawk Market"),
            (actors[10], actors[12],
             "PGP-signed vouch message on AgoraX"),
        ]
        for a, b, reason in vouch_list:
            a_id, b_id = sorted([a["id"], b["id"]])
            session.execute(
                text(
                    "INSERT INTO trust_links"
                    "  (id, actor_a_id, actor_b_id, relationship_type,"
                    "   strength_score, evidence, ai_suggested)"
                    " VALUES (:id, :a, :b, 'VOUCHED_FOR', 65.0, :ev, 0)"
                    " ON CONFLICT (actor_a_id, actor_b_id, relationship_type)"
                    " DO NOTHING"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "a": a_id, "b": b_id,
                    "ev": json.dumps({"reason": reason}),
                },
            )
            vouch_count += 1

    session.commit()

    return {
        "module": "identity_graph",
        "shared_identifier_links": link_count,
        "vouched_for_links": vouch_count,
        "total_links_created": link_count + vouch_count,
    }


def get_graph_for_frontend(session, actor_id=None) -> dict:
    """Return graph data for frontend visualisation.

    Returns::

        {
          "nodes": [{"id", "label", "type", "confidence", "risk",
                      "cluster_id"}, ...],
          "edges": [{"source", "target", "type", "strength",
                      "ai_suggested", "evidence"}, ...]
        }
    """
    G = nx.Graph()

    # -- nodes ---------------------------------------------------------
    actors = _get_all_actors(session)
    for a in actors:
        G.add_node(a["id"], **a)

    # -- edges ---------------------------------------------------------
    rows = session.execute(
        text(
            "SELECT actor_a_id, actor_b_id, relationship_type,"
            "       strength_score, evidence, ai_suggested "
            "FROM trust_links"
        )
    ).fetchall()

    edge_dicts: list[dict] = []
    for r in rows:
        G.add_edge(r[0], r[1], type=r[2], strength=float(r[3]))
        edge_dicts.append({
            "source": r[0],
            "target": r[1],
            "type": r[2],
            "strength": float(r[3]),
            "ai_suggested": bool(r[5]),
            "evidence": json.loads(r[4]) if r[4] else {},
        })

    # -- connected-component cluster ids -------------------------------
    components = list(nx.connected_components(G))
    cluster_map: dict[str, int] = {}
    for cid, comp in enumerate(components):
        for nid in comp:
            cluster_map[nid] = cid

    # -- optional actor filter -----------------------------------------
    if actor_id:
        relevant: set[str] = set()
        for comp in components:
            if actor_id in comp:
                relevant = comp
                break
        if not relevant:
            relevant = {actor_id}
    else:
        relevant = {a["id"] for a in actors}

    nodes = [
        {
            "id": a["id"],
            "label": a["handle"],
            "type": "actor",
            "confidence": a["confidence"],
            "risk": a["risk"],
            "cluster_id": cluster_map.get(a["id"], -1),
        }
        for a in actors
        if a["id"] in relevant
    ]
    edges = [
        e for e in edge_dicts
        if e["source"] in relevant and e["target"] in relevant
    ]

    return {"nodes": nodes, "edges": edges}
