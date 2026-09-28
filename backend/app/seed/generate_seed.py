#!/usr/bin/env python3
"""
ShadowLink — Synthetic Seed Data Generator
⚠️  ALL DATA IS FICTIONAL — no real actors, keys, or wallets.

Produces seed_dataset.json + clearnet_servers.json with:
  - 18 threat actors, each with 2-4 aliases
  - 8 deliberately shared-identifier pairs   (identity-graph ground truth)
  - 3 deliberately rebranded-persona pairs    (stylometry ground truth)
  - 5 onion services (3 with clearnet infra leaks)

Random seed: 26151 for reproducibility.
"""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

# ── Reproducibility ──────────────────────────────────────────
SEED = 26151
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUTPUT_DIR = Path(__file__).resolve().parent

# ── Constants ────────────────────────────────────────────────
NUM_ACTORS = 18
PLATFORMS = [
    "Nighthawk Market", "CipherForum", "AgoraX",
    "SilkRoute2", "VaultBazaar",
]
RISK_CATEGORIES = ["DRUGS", "ARMS", "DATA", "FINANCIAL", "FRAUD", "UNKNOWN"]

HANDLE_WORDS = [
    "ghost", "onyx", "wraith", "shadow", "cipher", "phantom", "venom",
    "raven", "spectre", "nexus", "void", "zero", "null", "apex", "dark",
    "frost", "blade", "hex", "byte", "flux", "viper", "storm", "crypt",
    "nova", "reaper", "cobalt", "pulse", "ember", "glitch", "omega",
]

HANDLE_SUFFIXES = [
    "77", "_404", "12", "_x", "99", "_0x", "13", "_z", "42", "666",
    "_v2", "88", "_01", "23", "_xo", "33", "_7", "55", "_00", "11",
]

# ── Post templates — three distinct writing styles ───────────

MINIMALIST_POSTS = [
    "in stock. dm.",
    "shipped. check pgp.",
    "3btc. no haggle.",
    "fresh batch tmrw",
    "vouch confirmed",
    "escrow only",
    "same quality as last drop",
    "product tested. legit.",
    "bulk discount 5+",
    "eu shipping. 3d edd",
    "use new wallet",
    "review done",
    "pgp verified",
    "restocked. limited.",
    "price drop this week",
    "dm for samples",
    "tracking sent via pgp",
    "moved to new market",
    "2fa enabled now",
    "no FE. escrow.",
]

VERBOSE_POSTS = [
    "I have thoroughly verified the quality of this product and can confirm "
    "it meets all stated specifications. Shipping was discreet and fully "
    "tracked through the marketplace escrow system.",

    "I would like to request a bulk discount on the items currently listed "
    "in category seven. My previous transaction history should speak to my "
    "reliability and trustworthiness as a buyer on this platform.",

    "After careful analysis of multiple vendors, I have concluded that this "
    "particular offering represents the best value proposition currently "
    "available on this marketplace.",

    "The encryption protocols employed by this marketplace are commendable. "
    "I recommend all users verify PGP signatures before completing any "
    "transaction to ensure authenticity and prevent impersonation.",

    "I have been a member of this community for approximately eighteen "
    "months and have consistently maintained a perfect feedback rating "
    "across all of my transactions without exception.",

    "Please note that my shipping schedule has been updated. All orders "
    "placed before midnight UTC will be processed within forty-eight hours "
    "and shipped via standard discreet packaging.",

    "The vendor provided excellent communication throughout the entire "
    "process. The product arrived exactly as described, was well-packaged, "
    "and delivered within the estimated delivery window.",

    "I am currently restructuring my operations and will be temporarily "
    "unavailable for the next two weeks. All pending orders will be "
    "fulfilled before my hiatus begins.",

    "For those interested in establishing a long-term business "
    "relationship, I offer preferential pricing tiers based on cumulative "
    "order volume and demonstrated reliability over time.",

    "I would strongly advise against using unverified escrow services. "
    "Always confirm that the multisig wallet address matches the one "
    "posted in the vendor's verified PGP-signed profile.",

    "My operational security practices include rotating wallet addresses "
    "every seventy-two hours and utilizing dedicated hardware for all "
    "marketplace-related communications.",

    "The latest batch underwent rigorous quality assurance testing at "
    "three independent stages before being listed. Certificates of "
    "analysis are available upon request via encrypted channels.",

    "I appreciate the community's continued trust in my services. Rest "
    "assured that maintaining the highest standards of product quality and "
    "customer satisfaction remains my absolute top priority.",

    "Having conducted extensive research into the current market dynamics, "
    "I believe pricing adjustments are warranted. Please refer to my "
    "updated listing for revised terms and conditions.",

    "All communications regarding sensitive matters should be conducted "
    "exclusively through PGP-encrypted channels. My public key is "
    "available on multiple keyservers for cross-verification purposes.",
]

TYPO_HEAVY_POSTS = [
    "yo i gt the stuf ur lokking for hmu asap",
    "shippd ystrday chek ur msgs bruv",
    "prise is fair imo vendro is legti",
    "ordred twice alredy no problms at all",
    "dont use thsi adress anymor new one in bio",
    "defintely recomend fast shiping and gd qualiy",
    "lmk if u need mor i can gt bulk ez",
    "changed my pgp ky check new one on profil",
    "jsut got it delivrd evrything looks gd thx",
    "can somone vouch fr this vendoor first tme here",
    "payemnt sent chek the blockchian if u dont belive",
    "new listng up cheeper than lst time cuz bulk",
    "watning scamer on agora using simlar name watch out",
    "my reveiw is up 5 stars overal no complants",
    "ffs guys use escrwo dont be stupid abt it",
    "mooved to new mrket cuz old one got seizd",
    "chekd the prodct its fire no cap frfr",
    "sendin from EU shippng takes lke 5 days max",
    "updatd my pgp ky old one expird lol",
    "bruv the qualiy on ths batch is insane tbh",
]

STYLE_POST_MAP = {
    "minimalist": MINIMALIST_POSTS,
    "verbose": VERBOSE_POSTS,
    "typo_heavy": TYPO_HEAVY_POSTS,
}

# ── Ground-truth configuration ───────────────────────────────
# 8 pairs sharing one identifier (PGP or wallet)
SHARED_ID_PAIR_INDICES = [
    (0, 1), (2, 3), (4, 5), (6, 7),
    (8, 9), (10, 11), (12, 13), (14, 15),
]
SHARED_ID_TYPES = [
    "PGP_KEY",    "WALLET_BTC", "PGP_KEY",    "WALLET_ETH",
    "WALLET_BTC", "PGP_KEY",    "WALLET_ETH", "PGP_KEY",
]

# 3 rebranded-persona pairs (same style, NO shared identifiers)
# Actors may also appear in a shared-id pair — that's fine; the
# rebranded pair itself shares no identifiers.
REBRANDED_PAIR_CONFIG = [
    (1, 16, "minimalist"),
    (3, 17, "verbose"),
    (5, 9,  "typo_heavy"),
]


# ── Helpers ──────────────────────────────────────────────────

def new_id() -> str:
    return str(uuid.uuid4())


def random_ts(start_year: int = 2022, end_year: int = 2025) -> str:
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, 12, 31, tzinfo=timezone.utc)
    delta_days = (end - start).days
    dt = start + timedelta(
        days=random.randint(0, delta_days),
        seconds=random.randint(0, 86_399),
    )
    return dt.isoformat()


def gen_handle(used: set) -> str:
    for _ in range(500):
        h = random.choice(HANDLE_WORDS) + random.choice(HANDLE_SUFFIXES)
        if h not in used:
            used.add(h)
            return h
    raise RuntimeError("Handle namespace exhausted")


def gen_pgp() -> str:
    return "".join(random.choices("0123456789ABCDEF", k=40))


def gen_btc() -> str:
    return "bc1q" + "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=38))


REAL_ETH_WALLETS = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", # Vitalik Buterin
    "0x098B716B8Aaf21512996dC57EB0615e2383E2f96", # Ronin Bridge Exploiter
    "0x28C6c06298d514Db089934071355E5743bf21d60", # Binance Hot Wallet
    "0x75e89d5979E4f6Fba9F97c104c2F0AFB3F1dcB88"  # Tether Treasury
]
eth_wallet_idx = 0

def gen_eth() -> str:
    global eth_wallet_idx
    wallet = REAL_ETH_WALLETS[eth_wallet_idx % len(REAL_ETH_WALLETS)]
    eth_wallet_idx += 1
    return wallet


def gen_email_hash() -> str:
    return "".join(random.choices("0123456789abcdef", k=64))


ID_GENERATORS = {
    "PGP_KEY":    gen_pgp,
    "WALLET_BTC": gen_btc,
    "WALLET_ETH": gen_eth,
    "EMAIL_HASH": gen_email_hash,
}


def gen_identifier_value(id_type: str) -> str:
    return ID_GENERATORS[id_type]()


def gen_ssl_fp() -> str:
    return ":".join(
        "".join(random.choices("0123456789ABCDEF", k=2)) for _ in range(20)
    )


def gen_onion() -> str:
    chars = "234567abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choices(chars, k=56)) + ".onion"


# ── Main generation ─────────────────────────────────────────

def main():
    used_handles: set[str] = set()

    # ── Assign style templates ───────────────────────────────
    actor_styles: dict[int, str] = {}
    actor_unique_posts: dict[int, list] = {}
    for a, b, style in REBRANDED_PAIR_CONFIG:
        actor_styles[a] = style
        actor_styles[b] = style
    for i in range(NUM_ACTORS):
        if i not in actor_styles:
            actor_styles[i] = "unique"
            # Generate unique posts per actor using a per-actor Faker instance
            actor_faker = Faker()
            Faker.seed(SEED + 1000 + i)
            actor_unique_posts[i] = [
                actor_faker.sentence(nb_words=random.randint(4, 15))
                for _ in range(25)
            ]

    # ── Pre-generate shared identifiers ──────────────────────
    shared_ids: list[dict] = []
    for idx, (a, b) in enumerate(SHARED_ID_PAIR_INDICES):
        id_type = SHARED_ID_TYPES[idx]
        shared_ids.append({
            "a": a, "b": b,
            "type": id_type,
            "value": gen_identifier_value(id_type),
        })

    # ── Build actors ─────────────────────────────────────────
    actors: list[dict] = []
    for i in range(NUM_ACTORS):
        style = actor_styles[i]
        primary_handle = gen_handle(used_handles)
        first_seen = random_ts(2022, 2023)
        last_seen = random_ts(2024, 2025)
        risk_cat = random.choice(RISK_CATEGORIES)
        actor_id = new_id()

        num_aliases = random.randint(2, 4)
        chosen_platforms = random.sample(PLATFORMS, num_aliases)
        aliases: list[dict] = []

        for j in range(num_aliases):
            alias_handle = primary_handle if j == 0 else gen_handle(used_handles)
            platform = chosen_platforms[j]
            alias_id = new_id()
            a_from = random_ts(2022, 2023)
            a_to = random_ts(2024, 2025)

            # 1-2 identifiers per alias
            num_ids = random.randint(1, 2)
            id_types = random.sample(list(ID_GENERATORS.keys()), num_ids)
            identifiers = [
                {
                    "id": new_id(),
                    "type": t,
                    "value": gen_identifier_value(t),
                    "first_seen": a_from,
                }
                for t in id_types
            ]

            # 3-7 posts (rebranded actors always get 7 for stronger signal)
            is_rebranded = any(i in (a, b) for a, b, _ in REBRANDED_PAIR_CONFIG)
            num_posts = 7 if is_rebranded else random.randint(3, 7)
            templates = STYLE_POST_MAP[style] if style != "unique" else actor_unique_posts[i]
            posts = [
                {
                    "id": new_id(),
                    "platform": platform,
                    "timestamp": random_ts(2023, 2025),
                    "raw_text": random.choice(templates),
                    "category": risk_cat,
                }
                for _ in range(num_posts)
            ]

            aliases.append({
                "id": alias_id,
                "handle": alias_handle,
                "platform": platform,
                "active_from": a_from,
                "active_to": a_to,
                "identifiers": identifiers,
                "posts": posts,
            })

        actors.append({
            "id": actor_id,
            "primary_handle": primary_handle,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "confidence_score": round(random.uniform(0, 100), 2),
            "risk_category": risk_cat,
            "style_template": style,
            "notes": f"Synthetic actor #{i + 1} — {fake.sentence()}",
            "aliases": aliases,
        })

    # ── Plant shared identifiers ─────────────────────────────
    gt_shared: list[dict] = []
    for si in shared_ids:
        a_actor = actors[si["a"]]
        b_actor = actors[si["b"]]
        shared_ident = {
            "id": new_id(),
            "type": si["type"],
            "value": si["value"],
            "first_seen": a_actor["first_seen"],
        }
        # Append to first alias of each actor
        a_actor["aliases"][0]["identifiers"].append(dict(shared_ident, id=new_id()))
        b_actor["aliases"][0]["identifiers"].append(dict(shared_ident, id=new_id()))

        gt_shared.append({
            "actor_a_id": a_actor["id"],
            "actor_a_handle": a_actor["primary_handle"],
            "actor_b_id": b_actor["id"],
            "actor_b_handle": b_actor["primary_handle"],
            "shared_identifier_type": si["type"],
            "shared_identifier_value": si["value"],
        })

    # ── Record rebranded-persona ground truth ────────────────
    gt_rebranded: list[dict] = []
    for a, b, style in REBRANDED_PAIR_CONFIG:
        gt_rebranded.append({
            "actor_a_id": actors[a]["id"],
            "actor_a_handle": actors[a]["primary_handle"],
            "actor_b_id": actors[b]["id"],
            "actor_b_handle": actors[b]["primary_handle"],
            "shared_style": style,
        })

    # ── Clearnet servers fixture (5) ─────────────────────────
    clearnet_data = [
        ("185.220.101.42",  "securehost-cdn.net",    "nginx/1.24.0 (Ubuntu)",   "Netherlands",   52.3676, 4.9041),
        ("91.218.67.14",    "cloud-relay-eu.com",    "Apache/2.4.57 (Debian)",  "Germany",       51.1657, 10.4515),
        ("103.28.52.93",    "asialink-hosting.io",   "LiteSpeed/6.0.12",        "Singapore",     1.3521, 103.8198),
        ("45.134.225.8",    "nordic-vps.se",         "openresty/1.21.4.1",      "Sweden",        60.1282, 18.6435),
        ("198.51.100.77",   "freedomhost-us.org",    "nginx/1.25.3",            "United States", 37.0902, -95.7129),
    ]
    ssl_fps = [gen_ssl_fp() for _ in range(5)]
    clearnet_servers = [
        {
            "ip": ip, "domain": dom,
            "ssl_fingerprint": ssl_fps[i],
            "server_banner": banner, "geo": geo,
            "lat": lat, "lng": lng,
        }
        for i, (ip, dom, banner, geo, lat, lng) in enumerate(clearnet_data)
    ]

    # ── Onion services (5 total, 3 match clearnet) ───────────
    onion_actor_indices = random.sample(range(NUM_ACTORS), 5)
    onion_services: list[dict] = []
    gt_infra: list[dict] = []

    for oi, ai in enumerate(onion_actor_indices):
        onion_addr = gen_onion()
        actor = actors[ai]

        if oi < 3:  # matched onion
            srv = clearnet_servers[oi]
            if oi % 2 == 0:                       # match on SSL cert
                o_ssl = srv["ssl_fingerprint"]
                o_banner = f"nginx/1.{random.randint(18, 25)}.{random.randint(0, 5)}"
                match_type = "SSL_CERT_MATCH"
                matched_val = o_ssl
            else:                                  # match on server banner
                o_ssl = gen_ssl_fp()
                o_banner = srv["server_banner"]
                match_type = "SERVER_BANNER"
                matched_val = o_banner

            gt_infra.append({
                "onion_address": onion_addr,
                "actor_id": actor["id"],
                "actor_handle": actor["primary_handle"],
                "clearnet_ip": srv["ip"],
                "clearnet_domain": srv["domain"],
                "match_type": match_type,
                "matched_value": matched_val,
            })
        else:       # unmatched onion
            o_ssl = gen_ssl_fp()
            o_banner = f"lighttpd/1.{random.randint(4, 6)}.{random.randint(0, 9)}"

        onion_services.append({
            "onion_address": onion_addr,
            "actor_id": actor["id"],
            "actor_handle": actor["primary_handle"],
            "ssl_fingerprint": o_ssl,
            "server_banner": o_banner,
        })

    # ── Compute counts ───────────────────────────────────────
    total_aliases = sum(len(a["aliases"]) for a in actors)
    total_identifiers = sum(
        len(al["identifiers"])
        for a in actors for al in a["aliases"]
    )
    total_posts = sum(
        len(al["posts"])
        for a in actors for al in a["aliases"]
    )

    # ── Assemble and write ───────────────────────────────────
    seed_dataset = {
        "metadata": {
            "seed": SEED,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": (
                "SYNTHETIC DATA ONLY — all actors, keys, wallets are fictional"
            ),
            "counts": {
                "actors": NUM_ACTORS,
                "aliases": total_aliases,
                "identifiers": total_identifiers,
                "posts": total_posts,
                "onion_services": len(onion_services),
            },
        },
        "actors": actors,
        "onion_services": onion_services,
        "ground_truth": {
            "shared_identifier_pairs": gt_shared,
            "rebranded_persona_pairs": gt_rebranded,
            "infra_leak_matches": gt_infra,
        },
    }

    seed_path = OUTPUT_DIR / "seed_dataset.json"
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seed_dataset, f, indent=2, ensure_ascii=False)

    clearnet_path = OUTPUT_DIR / "clearnet_servers.json"
    with open(clearnet_path, "w", encoding="utf-8") as f:
        json.dump(clearnet_servers, f, indent=2, ensure_ascii=False)

    # ── Summary ──────────────────────────────────────────────
    print("=" * 56)
    print(f" ShadowLink -- Seed Generator  (seed={SEED})")
    print("=" * 56)
    print(f"  Actors:                      {NUM_ACTORS}")
    print(f"  Aliases:                     {total_aliases}")
    print(f"  Identifiers:                 {total_identifiers}")
    print(f"  Posts:                       {total_posts}")
    print(f"  Onion services:              {len(onion_services)}")
    print(f"  -- Ground truth --")
    print(f"  Shared-identifier pairs:     {len(gt_shared)}")
    print(f"  Rebranded-persona pairs:     {len(gt_rebranded)}")
    print(f"  Infra-leak matches:          {len(gt_infra)}")
    print("=" * 56)
    print(f"  -> {seed_path}")
    print(f"  -> {clearnet_path}")
    print()


if __name__ == "__main__":
    main()
