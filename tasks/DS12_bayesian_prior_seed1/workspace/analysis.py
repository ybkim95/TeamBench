"""
Bayesian shrinkage estimation of display ad conversion rates across ad groups.
BUG: Uses Beta(1,1) uninformative (flat) prior for all segments.
This is suboptimal — it treats each segment independently and gives poor
estimates for small segments (high variance, biased toward 0.5).
Fix: Estimate empirical Bayes prior (alpha, beta) from the data using
Method of Moments or MLE, then compute posterior means with that prior.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/segments.csv")

n_col = "impressions"
k_col = "conversions"
seg_col = "ad_group_id"

n = df[n_col].values
k = df[k_col].values

# BUG: flat Beta(1,1) prior — ignores information from other segments
prior_alpha = 1.0
prior_beta = 1.0

# Posterior mean with flat prior: (1 + k) / (2 + n)
posterior_means = (prior_alpha + k) / (prior_alpha + prior_beta + n)

results = {
    "prior_alpha": prior_alpha,
    "prior_beta": prior_beta,
    "posterior_means": posterior_means.tolist(),
    "mean_posterior": float(posterior_means.mean()),
    "method": "flat_prior",  # BUG: should be "empirical_bayes"
}

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Prior: Beta({prior_alpha}, {prior_beta})")
print(f"Mean posterior: {posterior_means.mean():.4f}")
print("Saved results.json")
