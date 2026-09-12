# ML32: DataLoader Workers Share NumPy Random State

## Goal
Fix `dataloader.py` so each DataLoader worker seeds its NumPy random state independently.
Run `python train.py` then `python check_dataloader.py` — both must pass.

## Task
Creating a DataLoader for a **tabular dataset with numpy noise augmentation** with 2 workers.
Workers use `np.random` for augmentation. Without seeding, all workers share the
same state, producing identical (non-diverse) augmentations.

---

## The Bug: Missing `worker_init_fn`

**Location**: `make_dataloader()` in `dataloader.py`

### Background: Worker Process RNG Inheritance

PyTorch's DataLoader creates worker processes via `fork()` (on Unix) or
`spawn()` (on Windows). In both cases, NumPy's random state is either:
- **Forked**: each worker has an identical copy of the parent's state
- **Uninitialized**: unpredictable, often same across workers

Without seeding, 2 workers generate correlated (or identical) augmentations.

### Current (Buggy) Code

```python
return DataLoader(
    dataset,
    batch_size=batch_size,
    shuffle=shuffle,
    num_workers=2,
    worker_init_fn=None,  # BUG: all workers share NumPy state
)
```

### Correct Fix

```python
def worker_init_fn(worker_id: int) -> None:
    # Derive seed from PyTorch's per-worker seed + worker_id
    seed = torch.initial_seed() % (2**32)
    np.random.seed(seed + worker_id)

return DataLoader(
    dataset,
    batch_size=batch_size,
    shuffle=shuffle,
    num_workers=2,
    worker_init_fn=worker_init_fn,  # each worker gets unique NumPy seed
)
```

`torch.initial_seed()` returns a unique seed for each worker set by PyTorch's
random number generator. Adding `worker_id` ensures uniqueness even if two
workers are initialized at the same time.

Also update:
- `check_worker_diversity()` to return `"has_worker_init_fn": True`

### Why This Matters

| Without fix | With fix |
|-------------|----------|
| Workers 0..1 all use same np.random | Each worker has unique seed |
| Batch `i` from worker `k` same as from worker `j` | Each worker produces different augmentation |
| Effective dataset diversity reduced | Full augmentation diversity |

---

## Training Config
- Workers: 2, LR: 0.002, Epochs: 19, Batch: 32

## Deliverables
1. Fixed `dataloader.py` with `worker_init_fn` that seeds NumPy per worker
2. Updated `check_worker_diversity()` returning `has_worker_init_fn=True`
3. `training_results.json` after running `python train.py`
4. `python check_dataloader.py` exits 0
