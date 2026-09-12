# Experiments — Sprint 0 (compute-free sharpenings)

Four analyses that reuse existing data to shore up paper claims before new runs are launched.

Run all four (order independent):

```bash
cd /u/ybkim95/TeamBench
./venv/bin/python experiments/strong_baseline/analyze.py
./venv/bin/python experiments/equalizer_replication/replicate.py
./venv/bin/python experiments/statistical_rigor/recompute.py
./venv/bin/python experiments/learned_router/train.py
```

| Script | Input | Output | Claim tested |
|---|---|---|---|
| `strong_baseline/analyze.py` | `shared/ablation_results/strong_baseline_*.json` + matching `crossmodel_*.json` | `shared/paper/strong_baseline_comparison.json`, `table_strong_baseline_v2.tex` | Scaffolded oracles (CoT, 2-pass) do not close the gap to full team |
| `equalizer_replication/replicate.py` | `shared/ablation_results/crossmodel_*_seed0.json` | `equalizer_replication.json`, `table_equalizer_replication.tex` | r(oracle, uplift) < 0 replicates across model providers |
| `statistical_rigor/recompute.py` | `shared/paper/task_regression_data.csv` | `statistical_rigor.json`, `table_statistical_rigor.tex` | Which category uplifts survive Holm-Bonferroni |
| `learned_router/train.py` | `shared/paper/task_regression_data.csv` | `learned_router_results.json`, `table_learned_router.tex` | Task-conditional topology beats static full |

None of these scripts make API calls. All outputs are deterministic (seeded `numpy.random.default_rng(42)`).

## What's NOT here (needs new compute)

- Strong-baseline rerun on Claude/GPT primaries (~8 GPU-hrs / $30 API)
- Communication injection experiment (2 hrs replay compute)
- Multi-turn ablation (30 runs)
- Human baseline (ongoing on matlaberp8)
