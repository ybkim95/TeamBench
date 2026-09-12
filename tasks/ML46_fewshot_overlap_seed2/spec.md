# ML46: Few-Shot Support/Query Set Overlap

## Goal
Fix `episode_sampler.py` so support and query sets are disjoint.
Run `python train.py` then `python check_fewshot.py` — both must pass.

## Task
Training a **episodic few-shot learner** with 3-way 1-shot episodes.
Must achieve >0.4 test accuracy (evaluated on fresh episodes, no train contamination).

---

## The Bug: Query Samples Same as Support Samples

**Location**: `episode_sampler.py` `EpisodeSampler.sample_episode()` — `query_idx`

### Background: Episodic Few-Shot Learning

In few-shot learning, each "episode" consists of:
- **Support set**: K examples per class (the "training data" for this episode)
- **Query set**: Q examples per class (the "test data" for this episode)

**Critical requirement**: support and query must be DISJOINT samples.
If they overlap, the model can memorize support and trivially solve query.

### Current (Buggy) Code

```python
perm = torch.randperm(min(n_available, total_needed + 5))[:total_needed]
support_idx = perm[:self.k_shot]

# BUG: query uses same indices as support
query_idx = perm[:self.n_query]   # overlaps with support_idx!
```

When `n_query <= k_shot`, `query_idx == support_idx` (complete overlap).
Even when `n_query > k_shot`, the first `k_shot` indices overlap.

### Correct Fix

```python
perm = torch.randperm(min(n_available, total_needed + 5))[:total_needed]
support_idx = perm[:self.k_shot]

# CORRECT: query uses indices AFTER the support indices
query_idx = perm[self.k_shot:self.k_shot + self.n_query]
```

---

## Training Config
- 3-way 1-shot, 5 query per class
- 15 meta-classes, 22 samples per class
- Episodes: 828, lr: 0.0005

## Deliverables
1. Fixed `episode_sampler.py` with non-overlapping query indices
2. `training_results.json` after running `python train.py`
3. `python check_fewshot.py` exits 0
