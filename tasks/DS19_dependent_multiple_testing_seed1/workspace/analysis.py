"""
Multiple testing correction for fMRI voxel-wise activation analysis with spatial correlation.
BUG: Uses Benjamini-Hochberg (BH) procedure, which only controls FDR under
INDEPENDENCE or positive regression dependence (PRDS).
This dataset has arbitrary dependence structure — BH is not
valid here and may produce excess false positives.
Fix: Use Benjamini-Yekutieli (BY) procedure which controls FDR under
ARBITRARY dependence by multiplying the BH threshold by 1/c_m,
where c_m = sum(1/k, k=1..m) ≈ ln(m) + 0.5772.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/pvalues.csv")
pvalues = df["pvalue"].values
m = len(pvalues)
alpha = 0.05

# BH procedure (INCORRECT for this dependence structure)
sorted_idx = np.argsort(pvalues)
sorted_p = pvalues[sorted_idx]
ranks = np.arange(1, m + 1)
bh_thresholds = alpha * ranks / m

# Find BH threshold
bh_threshold = 0.0
for k in range(m, 0, -1):
    if sorted_p[k-1] <= alpha * k / m:
        bh_threshold = sorted_p[k-1]
        break

rejected_bh = pvalues <= bh_threshold
n_rejected = int(rejected_bh.sum())

results = {
    "method": "BH",         # BUG: should be "BY" for this dependence structure
    "threshold": float(bh_threshold),
    "n_rejected": n_rejected,
    "alpha": alpha,
    "m_tests": m,
    "harmonic_constant": 1.0,  # BUG: should be sum(1/k for k=1..m)
    "rejected_ids": df["voxel_id"][rejected_bh].tolist(),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"BH rejections: {n_rejected}/334")
print("WARNING: BH may not control FDR under this dependence structure!")
print("Saved results.json")
