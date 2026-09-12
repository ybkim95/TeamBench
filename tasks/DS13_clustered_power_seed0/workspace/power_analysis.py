"""
Power analysis for cluster-randomized school-based educational intervention.
BUG: Computes required sample size for INDEPENDENT observations,
ignoring the design effect from clustering.
When units are clustered (e.g., students within schools), observations within
the same cluster are correlated (ICC > 0), which REDUCES effective sample size.
Fix: Multiply required n by the design effect DEFF = 1 + (m - 1) * ICC,
where m = cluster size and ICC = intraclass correlation coefficient.
"""
import math
import json

# Study parameters
effect_size = 0.45   # Cohen's d
alpha = 0.05                # Significance level
power = 0.8                # Desired power
icc = 0.202                   # Intraclass correlation coefficient (given)
cluster_size = 41  # Average units per cluster

# Normal quantile approximation
def norm_ppf(p):
    if p < 0.5:
        return -norm_ppf(1 - p)
    t = math.sqrt(-2 * math.log(max(1e-9, 1 - p)))
    c = [2.515517, 0.802853, 0.010328]
    d = [1.432788, 0.189269, 0.001308]
    return t - (c[0] + c[1]*t + c[2]*t**2) / (1 + d[0]*t + d[1]*t**2 + d[2]*t**3)

z_alpha = norm_ppf(1 - alpha / 2)
z_beta = norm_ppf(power)

# BUG: computes n as if observations were INDEPENDENT
# Ignores design effect from clustering
n_per_arm = math.ceil(2 * ((z_alpha + z_beta) / effect_size) ** 2)

# Missing: design effect adjustment
# deff = 1 + (cluster_size - 1) * icc
# n_per_arm_clustered = math.ceil(n_per_arm * deff)
# n_clusters_per_arm = math.ceil(n_per_arm_clustered / cluster_size)

results = {
    "n_per_arm": n_per_arm,
    "n_clusters_per_arm": math.ceil(n_per_arm / cluster_size),  # BUG: no DEFF
    "deff": 1.0,      # BUG: should be 1 + (cluster_size - 1) * icc
    "method": "independent",  # BUG: should be "clustered"
    "icc": icc,
    "cluster_size": cluster_size,
    "effect_size": effect_size,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"n per arm (naive): {n_per_arm}")
print(f"n clusters per arm (naive): {results['n_clusters_per_arm']}")
print("WARNING: Design effect not applied — result is underpowered!")
