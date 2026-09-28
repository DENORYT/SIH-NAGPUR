"""
ShadowLink -- Infrastructure Matcher Module
Correlates onion-service metadata with clearnet server records to
identify operational-security leaks.

SYNTHETIC DATA ONLY -- all addresses and fingerprints are fictional.
"""

import json
import random
import uuid
from pathlib import Path

from sqlalchemy import text

# STUB: real Tor scraper plugs in here
SEED_DIR = Path(__file__).resolve().parents[1] / "seed"
_rng = random.Random(42)  # deterministic confidence scores


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

def _load_fixtures() -> tuple[list[dict], list[dict]]:
    """Load onion-service records and clearnet-server fixture files.

    Returns (onion_services, clearnet_servers).
    """
    # STUB: real Tor scraper plugs in here
    with open(SEED_DIR / "seed_dataset.json", encoding="utf-8") as f:
        seed = json.load(f)
    with open(SEED_DIR / "clearnet_servers.json", encoding="utf-8") as f:
        clearnet = json.load(f)
    return seed.get("onion_services", []), clearnet


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def _match_ssl(onion: dict, clearnet_entry: dict) -> dict | None:
    """Exact SSL-certificate fingerprint comparison.  confidence 90-98."""
    # STUB: real Tor scraper plugs in here
    o_fp = onion.get("ssl_fingerprint", "")
    c_fp = clearnet_entry.get("ssl_fingerprint", "")
    if o_fp and c_fp and o_fp == c_fp:
        return {
            "type": "SSL_CERT_MATCH",
            "confidence": round(_rng.uniform(90, 98), 2),
            "evidence": {
                "ssl_fingerprint": o_fp,
                "match_source": "cert_fingerprint_exact",
            },
        }
    return None


def _match_banner(onion: dict, clearnet_entry: dict) -> dict | None:
    """Exact server-banner / version-string comparison.  confidence 60-75."""
    # STUB: real Tor scraper plugs in here
    o_b = onion.get("server_banner", "")
    c_b = clearnet_entry.get("server_banner", "")
    if o_b and c_b and o_b == c_b:
        return {
            "type": "SERVER_BANNER",
            "confidence": round(_rng.uniform(60, 75), 2),
            "evidence": {
                "server_banner": o_b,
                "match_source": "banner_version_exact",
            },
        }
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(session) -> dict:
    """Run infrastructure matching: compare every onion service against
    every clearnet server.  Write matches into ``infra_leaks``.

    Returns a summary dict.
    """
    # STUB: real Tor scraper plugs in here
    onion_services, clearnet_servers = _load_fixtures()

    matches: list[dict] = []

    for onion in onion_services:
        best_match = None
        best_server = None

        for cs in clearnet_servers:
            # Prefer SSL match (higher confidence, definitive)
            ssl = _match_ssl(onion, cs)
            if ssl:
                best_match = ssl
                best_server = cs
                break  # cert match is definitive -- stop searching

            # Fall back to banner match
            banner = _match_banner(onion, cs)
            if banner and (
                best_match is None
                or banner["confidence"] > best_match["confidence"]
            ):
                best_match = banner
                best_server = cs

        if best_match and best_server:
            # Inject geo data for Leaflet mapping
            best_match["evidence"]["lat"] = best_server.get("lat")
            best_match["evidence"]["lng"] = best_server.get("lng")
            
            matches.append({
                "actor_id": onion["actor_id"],
                "type": best_match["type"],
                "onion_address": onion["onion_address"],
                "clearnet_ip": best_server["ip"],
                "clearnet_domain": best_server["domain"],
                "confidence": best_match["confidence"],
                "evidence": best_match["evidence"],
            })

    # ── Persist to infra_leaks ────────────────────────────────
    for m in matches:
        session.execute(
            text(
                "INSERT INTO infra_leaks"
                "  (id, actor_id, type, onion_address,"
                "   matched_clearnet_ip, matched_clearnet_domain,"
                "   evidence, confidence)"
                " VALUES"
                "  (:id, :actor_id, :type, :onion,"
                "   :ip, :domain, :evidence, :confidence)"
            ),
            {
                "id": str(uuid.uuid4()),
                "actor_id": m["actor_id"],
                "type": m["type"],
                "onion": m["onion_address"],
                "ip": m["clearnet_ip"],
                "domain": m["clearnet_domain"],
                "evidence": json.dumps(m["evidence"]),
                "confidence": m["confidence"],
            },
        )
    session.commit()

    return {
        "module": "infra_matcher",
        "matches_found": len(matches),
        "details": [
            {
                "onion": m["onion_address"][:20] + "...",
                "clearnet": m["clearnet_domain"],
                "type": m["type"],
                "confidence": m["confidence"],
            }
            for m in matches
        ],
    }
