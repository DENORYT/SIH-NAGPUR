"""Debug: print all pairwise cosine similarities to find the right threshold."""
import json, sys
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

with open('app/seed/seed_dataset.json') as f:
    seed = json.load(f)

gt_shared = set()
for p in seed['ground_truth']['shared_identifier_pairs']:
    gt_shared.add((p['actor_a_id'], p['actor_b_id']))
    gt_shared.add((p['actor_b_id'], p['actor_a_id']))

gt_reb = set()
for p in seed['ground_truth']['rebranded_persona_pairs']:
    gt_reb.add((p['actor_a_id'], p['actor_b_id']))
    gt_reb.add((p['actor_b_id'], p['actor_a_id']))

actor_posts = defaultdict(list)
for a in seed['actors']:
    for al in a['aliases']:
        for p in al['posts']:
            actor_posts[a['id']].append(p['raw_text'])

actor_ids = sorted(actor_posts.keys())
docs = [' '.join(actor_posts[aid]) for aid in actor_ids]

vec = TfidfVectorizer(max_features=500, stop_words=None, ngram_range=(1,2), sublinear_tf=True)
mat = vec.fit_transform(docs)
sims = cosine_similarity(mat)

results = []
for i in range(len(actor_ids)):
    for j in range(i+1, len(actor_ids)):
        a, b = actor_ids[i], actor_ids[j]
        if (a, b) in gt_shared:
            continue
        is_rb = (a, b) in gt_reb
        results.append((sims[i,j], is_rb, a[:8], b[:8]))

results.sort(reverse=True)
print("Top 20 similarities (excluding shared-id pairs):")
print(f"{'Sim':>8}  {'Rebrand?':>8}  Actor_A   Actor_B")
print("-" * 48)
for s, rb, a, b in results[:20]:
    tag = "<<< YES" if rb else ""
    print(f"{s:8.4f}  {'YES' if rb else 'no':>8}  {a}  {b}  {tag}")

print(f"\nRebranded pairs found in top 20: {sum(1 for _,rb,_,_ in results[:20] if rb)}")
print(f"\nAll rebranded pair similarities:")
for s, rb, a, b in results:
    if rb:
        print(f"  {a} <-> {b}: {s:.4f}")
