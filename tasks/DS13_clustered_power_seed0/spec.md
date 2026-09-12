# DS13: Clustered Power Analysis — Design Effect

## Task
Compute the **correct sample size** for a cluster-randomized school-based educational intervention.
The naive calculation ignores intraclass correlation (ICC) and underestimates the
required number of clusters, leading to an underpowered study.

## Study Design
- **Design**: Cluster-randomized trial (randomization at school level)
- **Outcome**: test score improvement
- **Effect size**: Cohen's d = 0.45
- **Significance level**: α = 0.05 (two-sided)
- **Target power**: 80%
- **ICC**: 0.202 (intraclass correlation coefficient)
- **Cluster size**: m = 41 students per school

## The Design Effect Formula
When units are clustered, observations within the same cluster are correlated.
The **design effect** inflates the required sample size:

```
DEFF = 1 + (m - 1) × ICC = 1 + (41 - 1) × 0.202 = 9.0800
```

The clustered sample size per arm:
```
n_clustered = n_independent × DEFF = 78 × 9.0800 = 709
n_clusters_per_arm = ceil(709 / 41) = 18
```

## Requirements
1. Compute `n_independent` (standard two-sample t-test formula)
2. Compute `deff = 1 + (cluster_size - 1) * icc`
3. Compute `n_per_arm_clustered = ceil(n_independent * deff)`
4. Compute `n_clusters_per_arm = ceil(n_per_arm_clustered / cluster_size)`
5. Save to `results.json`:
   - `n_per_arm`: independent sample size
   - `deff`: design effect (should be ≈ 9.0800)
   - `n_clusters_per_arm`: correct number of clusters needed (should be ≈ 18)
   - `method`: `"clustered"`
6. Fix `power_analysis.py`

## Data
Pilot data available in `data/pilot_data.csv` (for ICC estimation if needed).

## Deliverables
- Fixed `power_analysis.py` with design effect correction
- `results.json` with correct cluster counts
