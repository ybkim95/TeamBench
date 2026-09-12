"""DataLoader with worker RNG state bug."""
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader


class AugmentedDataset(Dataset):
    """
    tabular dataset with numpy noise augmentation.
    Uses NumPy random state for augmentation — sensitive to worker RNG seeding.
    """

    def __init__(self, X: np.ndarray, y: np.ndarray, augment: bool = True):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        self.augment = augment

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple:
        x = self.X[idx].numpy().copy()
        if self.augment:
            # NumPy-based augmentation — depends on worker's np.random state
            noise = np.random.randn(*x.shape).astype(np.float32) * 0.1
            x = x + noise
            # Random feature masking
            mask_idx = np.random.randint(0, x.shape[0])
            x[mask_idx] *= np.random.uniform(0.5, 1.5)
        return torch.tensor(x, dtype=torch.float32), self.y[idx]


def make_dataset(n: int = 568, seed: int = 42) -> tuple:
    """Generate synthetic tabular dataset with numpy noise augmentation."""
    rng = np.random.RandomState(seed)
    X = rng.randn(n, 20).astype(np.float32)
    y = (np.abs(X[:, :3].sum(axis=1)) % 3).astype(np.int64)
    return X, y


def make_dataloader(dataset: Dataset, batch_size: int = 32,
                    shuffle: bool = True, num_workers: int = 2) -> DataLoader:
    """
    Create a DataLoader for training.

    BUG: No worker_init_fn is provided. All 2 workers inherit
    the same NumPy random state from the parent process. Workers generate
    identical augmentations, reducing effective training diversity.

    Correct: Provide worker_init_fn that seeds each worker independently:
        def worker_init_fn(worker_id):
            seed = torch.initial_seed() % (2**32)
            np.random.seed(seed + worker_id)

    Note: This bug is most impactful with num_workers > 1.
    With num_workers=0 (main process), NumPy state is naturally sequential.
    """
    # BUG: No worker_init_fn — workers share NumPy random state
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        # BUG: worker_init_fn=None (should seed workers independently)
        worker_init_fn=None,
    )


def check_worker_diversity(dataset: Dataset, num_workers: int = 2,
                           n_batches: int = 4) -> dict:
    """
    Check if workers produce diverse augmentations.

    Returns metrics about augmentation diversity across workers.
    With the bug, workers produce similar augmentations.
    With the fix, workers produce diverse augmentations.
    """
    # Use num_workers=0 for main-process baseline
    loader_single = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0)
    batches_single = []
    for i, (x, _) in enumerate(loader_single):
        if i >= n_batches:
            break
        batches_single.append(x.numpy())

    # Reload with multiple workers
    loader_multi = make_dataloader(dataset, batch_size=16, shuffle=False,
                                   num_workers=num_workers)
    batches_multi = []
    for i, (x, _) in enumerate(loader_multi):
        if i >= n_batches:
            break
        batches_multi.append(x.numpy())

    return {
        "has_worker_init_fn": False,  # BUG: should be True after fix
        "num_workers": num_workers,
    }
