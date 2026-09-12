"""
Fuzzy deduplication for person name record linkage.
BUG: Finds pairwise matches within edit distance threshold=5 but does NOT
apply transitive closure. Records A, B, C where A≈B and B≈C but dist(A,C)>5
will be assigned to separate clusters, missing the transitive duplicate relationship.

Fix: After finding all pairs, apply union-find (disjoint set) to compute transitive
closure, so all transitively connected records share the same cluster_id.
"""
import pandas as pd
import json

def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]; dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if a[i-1] == b[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]

df = pd.read_csv("data/records.csv")
names = df["full_name"].tolist()
ids = df["person_id"].tolist()
n = len(df)
threshold = 5

# Find pairwise matches
pairs = []
for i in range(n):
    for j in range(i+1, n):
        if edit_distance(names[i], names[j]) <= threshold:
            pairs.append((i, j))

# BUG: naive label assignment — no transitive closure
# If A→B and B→C, C gets B's label but not A's label
cluster_id = list(range(n))
for i, j in pairs:
    # BUG: only propagates one level, misses chains
    cluster_id[j] = cluster_id[i]

clusters = {}
for idx, cid in enumerate(cluster_id):
    clusters.setdefault(str(cid), []).append(ids[idx])

results = {
    "n_records": n,
    "n_pairs": len(pairs),
    "n_clusters": len(clusters),
    "transitive_closure_applied": False,  # BUG: should be True
    "threshold": threshold,
    "clusters": clusters,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Records: {n}, Pairs: {len(pairs)}, Clusters: {len(clusters)}")
print("WARNING: No transitive closure — may over-count clusters!")
