# DS13: Clustered Power Analysis — Design Effect

## Task
Compute the **correct sample size** for a cluster-randomized workplace wellness program evaluation.
The naive calculation ignores intraclass correlation (ICC) and underestimates the
required number of clusters, leading to an underpowered study.

## Study Design
- **Design**: Cluster-randomized trial (randomization at office level)
- **Outcome**: productivity score increase
- **Effect size**: Cohen's d = 0.49
- **Significance level**: α = 0.05 (two-sided)
- **Target power**: 80%
- **ICC**: 0.24 (intraclass correlation coefficient)
- **Cluster size**: m = 18 employees per office

## The Design Effect Formula
When units are clustered, observations within the same cluster are correlated.
The **design effect** inflates the required sample size:

```
DEFF = 1 + (m - 1) × ICC = 1 + (18 - 1) × 0.24 = 5.0800
```

The clustered sample size per arm:
```
n_clustered = n_independent × DEFF = 66 × 5.0800 = 336
n_clusters_per_arm = ceil(336 / 18) = 19
```

## Requirements
1. Compute `n_independent` (standard two-sample t-test formula)
2. Compute `deff = 1 + (cluster_size - 1) * icc`
3. Compute `n_per_arm_clustered = ceil(n_independent * deff)`
4. Compute `n_clusters_per_arm = ceil(n_per_arm_clustered / cluster_size)`
5. Save to `results.json`:
   - `n_per_arm`: independent sample size
   - `deff`: design effect (should be ≈ 5.0800)
   - `n_clusters_per_arm`: correct number of clusters needed (should be ≈ 19)
   - `method`: `"clustered"`
6. Fix `power_analysis.py`

## Data
Pilot data available in `data/pilot_data.csv` (for ICC estimation if needed).

## Deliverables
- Fixed `power_analysis.py` with design effect correction
- `results.json` with correct cluster counts
