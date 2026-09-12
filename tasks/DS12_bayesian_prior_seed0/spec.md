# DS12: Bayesian Prior Sensitivity — Empirical Bayes

## Task
Estimate segment-level **email marketing campaign open rates across segments** using Bayesian shrinkage.
The dataset has **64 segments** with varying sample sizes.

## The Problem with Flat Prior
The current script uses `Beta(1, 1)` — a completely uninformative prior.
This means each segment's posterior is estimated independently.
For small segments (n < 20), this gives **high-variance, poorly calibrated** estimates.

## Empirical Bayes Solution
Instead of assuming Beta(1,1), **estimate the prior from the data itself**:

1. The segments' true rates are drawn from `Beta(alpha, beta)`
2. Estimate `alpha` and `beta` using Method of Moments:
   - Compute the sample mean `m` and variance `v` of observed rates `k/n`
   - `kappa = m*(1-m)/v - 1`
   - `alpha = m * kappa`
   - `beta = (1-m) * kappa`
3. Compute posterior mean for each segment:
   - `posterior_i = (alpha + k_i) / (alpha + beta + n_i)`

## Data
File: `data/segments.csv`
- `campaign_id`: segment identifier
- `emails_sent`: total observations
- `opens`: number of successes

## Requirements
1. Estimate `prior_alpha` and `prior_beta` via Method of Moments from the data
2. Compute posterior mean for each segment using the empirical prior
3. Save to `results.json`:
   - `prior_alpha`: estimated alpha (should be in range [4.20, 16.81])
   - `prior_beta`: estimated beta (should be in range [17.88, 71.52])
   - `posterior_means`: list of posterior means
   - `mean_posterior`: mean of all posterior means
   - `method`: `"empirical_bayes"`
4. Fix `analysis.py`

## Expected Prior Parameters
True prior: approximately `Beta(8.41, 35.76)`, population mean ≈ 0.190

## Deliverables
- Fixed `analysis.py` with empirical Bayes estimation
- `results.json` with estimated prior and posterior means
