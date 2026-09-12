# ML32: DataLoader Worker RNG Fork Bug (Brief)

## Your Task
Fix the DataLoader in `dataloader.py`.

A **tabular dataset with numpy noise augmentation** uses 2 DataLoader workers with
NumPy-based augmentation. Without a `worker_init_fn`, all workers share
the same NumPy random state, producing identical augmentations.

## What to Fix
- `dataloader.py`: `make_dataloader()` — add `worker_init_fn` that calls
  `np.random.seed(torch.initial_seed() % 2**32 + worker_id)`
- Update `check_worker_diversity()` to return `"has_worker_init_fn": True`
- Do NOT modify `train.py`

## Success Criteria
- `python check_dataloader.py` exits 0
- `has_worker_init_fn=True` in training_results.json
