"""Replay buffer for continual learning — contains FIFO bias bug."""
import torch
import numpy as np
from collections import deque


class ReplayBuffer:
    """Experience replay buffer for continual learning.

    BUG: Uses FIFO (deque with maxlen) eviction. When buffer is full,
    new samples from the current task evict the OLDEST samples — which
    are samples from the earliest tasks. After training on N tasks, the
    buffer contains predominantly samples from the last task only.

    This defeats the purpose of replay: early tasks are forgotten because
    their samples are no longer in the buffer.

    Correct behavior: use reservoir sampling to maintain a UNIFORM random
    sample across all tasks seen so far. With reservoir sampling, each
    sample has an equal probability of being in the buffer regardless of
    when it was added.

    Reservoir sampling algorithm (Vitter 1985):
    - For the i-th sample (i > buffer_size): include with probability buffer_size/i
    - If included, evict a RANDOM buffer slot (not the oldest)
    """

    def __init__(self, capacity: int = 150):
        self.capacity = capacity
        # BUG: deque with maxlen uses FIFO eviction
        self.buffer = deque(maxlen=capacity)
        # CORRECT: use reservoir sampling instead
        # self._data_x = []
        # self._data_y = []
        # self._n_seen = 0
        self._n_seen = 0

    def add(self, x: torch.Tensor, y: torch.Tensor):
        """Add samples to buffer.

        BUG: deque.append() evicts oldest when full (FIFO).
        This means early-task samples are evicted first.
        """
        for xi, yi in zip(x, y):
            self._n_seen += 1
            # BUG: FIFO — always evicts oldest (early task) samples
            self.buffer.append((xi.clone(), yi.clone()))
            # CORRECT: reservoir sampling would be:
            # if len(self.buffer_x) < self.capacity:
            #     self.buffer_x.append(xi.clone())
            #     self.buffer_y.append(yi.clone())
            # else:
            #     j = np.random.randint(0, self._n_seen)
            #     if j < self.capacity:
            #         self.buffer_x[j] = xi.clone()
            #         self.buffer_y[j] = yi.clone()

    def sample(self, n: int) -> tuple:
        """Sample n random items from buffer."""
        if len(self.buffer) == 0:
            return None, None
        n = min(n, len(self.buffer))
        indices = np.random.choice(len(self.buffer), n, replace=False)
        xs = torch.stack([self.buffer[i][0] for i in indices])
        ys = torch.stack([self.buffer[i][1] for i in indices])
        return xs, ys

    def __len__(self):
        return len(self.buffer)

    @property
    def n_seen(self):
        return self._n_seen
