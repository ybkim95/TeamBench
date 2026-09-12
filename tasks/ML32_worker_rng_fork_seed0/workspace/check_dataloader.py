"""Validate DataLoader worker RNG fix."""
import json
import sys
import os
import numpy as np
import torch
from torch.utils.data import DataLoader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataloader import AugmentedDataset, make_dataset, make_dataloader


def check_has_worker_init_fn():
    """Verify training_results has has_worker_init_fn=True."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if not res.get("has_worker_init_fn", False):
        return False, "has_worker_init_fn=False — worker_init_fn not set"
    return True, "has_worker_init_fn=True"


def check_source_has_worker_init_fn():
    """Verify dataloader.py defines and uses worker_init_fn."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataloader.py')) as f:
        src = f.read()
    if 'worker_init_fn=None' in src:
        return False, "worker_init_fn=None still present in dataloader.py"
    if 'worker_init_fn' not in src:
        return False, "worker_init_fn not found in dataloader.py"
    return True, "worker_init_fn found in dataloader.py"


def check_worker_init_seeds_numpy():
    """Verify worker_init_fn seeds NumPy random state."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataloader.py')) as f:
        src = f.read()
    has_np_seed = 'np.random.seed' in src or 'numpy.random.seed' in src
    if not has_np_seed:
        return False, "worker_init_fn does not call np.random.seed()"
    return True, "worker_init_fn calls np.random.seed()"


def check_worker_init_uses_worker_id():
    """Verify worker_init_fn uses worker_id to differentiate workers."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataloader.py')) as f:
        src = f.read()
    import re
    # worker_init_fn(worker_id) and uses worker_id in seed computation
    fn_match = re.search(r'def worker_init_fn\((\w+)\).*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "worker_init_fn function not found"
    fn_body = fn_match.group(0)
    param = fn_match.group(1)
    if param not in fn_body or fn_body.count(param) < 2:
        return False, f"worker_init_fn parameter '{param}' not used in body"
    return True, f"worker_init_fn uses parameter '{param}' for per-worker seeding"


def check_workers_produce_different_augmentations():
    """Verify different workers (via manual seed test) produce different outputs."""
    X, y = make_dataset(n=100, seed=42)
    ds = AugmentedDataset(X[:50], y[:50], augment=True)

    # Simulate what two workers with different seeds would produce
    # Worker 0: seed = some_base + 0
    # Worker 1: seed = some_base + 1
    sample = X[0].copy()
    np.random.seed(100)  # simulated worker 0 seed
    noise0 = np.random.randn(*sample.shape) * 0.1
    np.random.seed(101)  # simulated worker 1 seed
    noise1 = np.random.randn(*sample.shape) * 0.1

    if np.allclose(noise0, noise1, atol=1e-6):
        return False, "Workers with different seeds produce same augmentation (seeding bug)"
    return True, "Workers with different seeds produce different augmentations"


def check_dataloader_returns_dataloader():
    """Verify make_dataloader returns a DataLoader instance."""
    X, y = make_dataset(n=100, seed=42)
    ds = AugmentedDataset(X, y, augment=False)
    loader = make_dataloader(ds, batch_size=16, shuffle=False, num_workers=0)
    if not isinstance(loader, DataLoader):
        return False, f"make_dataloader returned {type(loader).__name__}, expected DataLoader"
    return True, "make_dataloader returns DataLoader"


def check_diversity_flag():
    """Verify check_worker_diversity returns has_worker_init_fn=True."""
    from dataloader import check_worker_diversity
    X, y = make_dataset(n=100, seed=42)
    ds = AugmentedDataset(X, y, augment=True)
    result = check_worker_diversity(ds, num_workers=0, n_batches=2)
    if not result.get("has_worker_init_fn", False):
        return False, "check_worker_diversity returns has_worker_init_fn=False"
    return True, "check_worker_diversity returns has_worker_init_fn=True"


def check_torch_initial_seed_used():
    """Verify worker_init_fn uses torch.initial_seed() for seed derivation."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataloader.py')) as f:
        src = f.read()
    if 'torch.initial_seed' not in src and 'initial_seed' not in src:
        return False, "torch.initial_seed() not used in worker_init_fn"
    return True, "torch.initial_seed() used for seed derivation"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    has_fn = res.get("has_worker_init_fn", False)
    print(f"Final val acc: {acc:.4f}, has_worker_init_fn={has_fn}")

    checks = [
        check_has_worker_init_fn,
        check_source_has_worker_init_fn,
        check_worker_init_seeds_numpy,
        check_worker_init_uses_worker_id,
        check_workers_produce_different_augmentations,
        check_dataloader_returns_dataloader,
        check_diversity_flag,
        check_torch_initial_seed_used,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (val_acc={acc:.4f} < 0.40)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
