"""
ShadowLink -- Stylometry Module
Detects rebranded personas through writing-style analysis.  Uses
TF-IDF vectorisation + cosine similarity to correlate post corpora
of aliases belonging to *different* actors that share NO identifiers.

SYNTHETIC DATA ONLY -- all post text is computer-generated.
"""

import json
import uuid
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text

# Similarity threshold -- pairs above this get a proposed STYLE_MATCH link
SIMILARITY_THRESHOLD = 0.52


# ---------------------------------------------------------------------------
# Feature extraction (for evidence payload)
# ---------------------------------------------------------------------------

def _extract_features(posts: list[str]) -> dict:
    """Compute hand-crafted stylometric features for a collection of posts.

    Features:
      - avg_sentence_len   (words per sentence)
      - avg_word_len        (characters per word)
      - vocab_richness      (unique / total words)
      - punct_freq          (frequency of ! ? , .)
      - function_word_freq  (proportion of function words)
    """
    if not posts:
        return {}

    all_text = " ".join(posts)
    words = all_text.split()
    if not words:
        return {}

    # Sentence splitting (crude but good enough for demo text)
    sentences = all_text.replace("!", ".").replace("?", ".").split(".")
    sentences = [s.strip() for s in sentences if s.strip()]

    avg_sent = (
        float(np.mean([len(s.split()) for s in sentences]))
        if sentences else 0.0
    )
    avg_wlen = float(np.mean([len(w) for w in words]))
    richness = len(set(w.lower() for w in words)) / len(words)

    n = max(len(all_text), 1)
    punct = {c: round(all_text.count(c) / n, 4) for c in "!?,." }

    func_words = {
        "the", "a", "an", "is", "are", "was", "were", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "i", "my", "me", "you",
        "your", "it", "this", "that", "and", "or", "but", "not", "no",
    }
    fw = sum(1 for w in words if w.lower() in func_words) / len(words)

    return {
        "avg_sentence_len":  round(avg_sent, 2),
        "avg_word_len":      round(avg_wlen, 2),
        "vocab_richness":    round(richness, 4),
        "punct_freq":        punct,
        "function_word_freq": round(fw, 4),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(session, threshold: float = SIMILARITY_THRESHOLD) -> dict:
    """Detect rebranded personas via TF-IDF cosine similarity.

    1. Group all posts by *actor* (across all that actor's aliases).
    2. Build per-actor TF-IDF document vectors.
    3. Compare pairs of actors that share **no** identifiers.
    4. Pairs above *threshold* get a ``STYLE_MATCH`` trust link with
       ``ai_suggested = TRUE``.

    Returns a summary dict.
    """

    # ── Collect posts per actor ──────────────────────────────
    rows = session.execute(
        text(
            "SELECT al.actor_id, p.raw_text "
            "FROM posts p "
            "JOIN aliases al ON al.id = p.alias_id "
            "ORDER BY al.actor_id"
        )
    ).fetchall()

    actor_posts: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        actor_posts[r[0]].append(r[1])

    # ── Actors already linked by shared identifiers (exclude) ─
    linked_rows = session.execute(
        text(
            "SELECT actor_a_id, actor_b_id FROM trust_links "
            "WHERE relationship_type IN ('SAME_PGP', 'SAME_WALLET')"
        )
    ).fetchall()
    linked_pairs: set[tuple[str, str]] = set()
    for r in linked_rows:
        linked_pairs.add(tuple(sorted([r[0], r[1]])))

    # ── Build TF-IDF per actor ───────────────────────────────
    actor_ids = sorted(actor_posts.keys())
    if len(actor_ids) < 2:
        return {"module": "stylometry", "matches_found": 0, "details": []}

    documents = [" ".join(actor_posts[aid]) for aid in actor_ids]

    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words=None,        # keep everything -- stylometric signal
        ngram_range=(1, 2),     # unigrams + bigrams
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(documents)

    # ── Pairwise cosine similarity ───────────────────────────
    sim_matrix = cosine_similarity(tfidf_matrix)
    feature_names = vectorizer.get_feature_names_out()

    proposed: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for i in range(len(actor_ids)):
        for j in range(i + 1, len(actor_ids)):
            a_id, b_id = actor_ids[i], actor_ids[j]
            pair = tuple(sorted([a_id, b_id]))

            if pair in linked_pairs or pair in seen:
                continue

            sim = float(sim_matrix[i, j])
            if sim > threshold:
                seen.add(pair)
                
                # Explainable AI: Find top shared n-grams
                vec_i = tfidf_matrix[i].toarray()[0]
                vec_j = tfidf_matrix[j].toarray()[0]
                shared_indices = [idx for idx in range(len(feature_names)) if vec_i[idx] > 0 and vec_j[idx] > 0]
                
                # Sort by combined TF-IDF importance
                shared_indices.sort(key=lambda idx: (vec_i[idx] + vec_j[idx]), reverse=True)
                top_shared = [feature_names[idx] for idx in shared_indices[:5]]

                proposed.append({
                    "actor_a_id": pair[0],
                    "actor_b_id": pair[1],
                    "similarity": round(sim, 4),
                    "strength":   round(sim * 100, 2),
                    "shared_n_grams": top_shared,
                    "features_a": _extract_features(actor_posts[a_id]),
                    "features_b": _extract_features(actor_posts[b_id]),
                })

    # ── Persist proposed STYLE_MATCH links ───────────────────
    for link in proposed:
        session.execute(
            text(
                "INSERT INTO trust_links"
                "  (id, actor_a_id, actor_b_id, relationship_type,"
                "   strength_score, evidence, ai_suggested)"
                " VALUES (:id, :a, :b, 'STYLE_MATCH', :str, :ev, 1)"
                " ON CONFLICT (actor_a_id, actor_b_id, relationship_type)"
                " DO NOTHING"
            ),
            {
                "id": str(uuid.uuid4()),
                "a": link["actor_a_id"],
                "b": link["actor_b_id"],
                "str": link["strength"],
                "ev": json.dumps({
                    "cosine_similarity": link["similarity"],
                    "shared_n_grams": link.get("shared_n_grams", []),
                    "features_a": link["features_a"],
                    "features_b": link["features_b"],
                }),
            },
        )
    session.commit()

    return {
        "module": "stylometry",
        "matches_found": len(proposed),
        "threshold": threshold,
        "details": [
            {
                "actor_a": lk["actor_a_id"][:8] + "...",
                "actor_b": lk["actor_b_id"][:8] + "...",
                "similarity": lk["similarity"],
                "strength":   lk["strength"],
            }
            for lk in proposed
        ],
    }
