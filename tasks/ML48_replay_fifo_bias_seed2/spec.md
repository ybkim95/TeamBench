# ML48: Replay Buffer FIFO Bias (Continual Learning)

## Goal
Fix `replay_buffer.py` to use reservoir sampling instead of FIFO eviction.
Run `python train.py` then `python check_continual.py` — both must pass.

## Task
Training a **domain-incremental continual learning** across 4 sequential tasks.
The model must avoid catastrophic forgetting (task 0 forgetting < 0.3, final acc > 0.3).

---

## The Bug: FIFO Eviction Removes Early-Task Samples

**Location**: `replay_buffer.py` `ReplayBuffer.add()` — deque FIFO eviction

### Background: Experience Replay in Continual Learning

Continual learning uses a replay buffer to retain examples from past tasks.
When the buffer is full, a decision must be made about which sample to evict.

**FIFO (First-In, First-Out)**:
- Evicts the oldest sample (earliest task first)
- After training on T tasks, buffer contains ONLY recent-task samples
- Early tasks are catastrophically forgotten despite "replay"

**Reservoir Sampling (Vitter 1985)**:
- For the i-th sample: include with probability `min(1, capacity/i)`
- If included: evict a **random** buffer slot (not the oldest)
- Result: each sample has equal probability `capacity/n_total` of being in buffer
- ALL tasks represented proportionally regardless of when they were added

### Current (Buggy) Code

```python
self.buffer = deque(maxlen=capacity)  # FIFO!

def add(self, x, y):
    for xi, yi in zip(x, y):
        self._n_seen += 1
        self.buffer.append((xi, yi))  # FIFO eviction when full
```

### Correct Fix (Reservoir Sampling)

```python
def add(self, x, y):
    for xi, yi in zip(x, y):
        self._n_seen += 1
        if len(self.buffer_x) < self.capacity:
            self.buffer_x.append(xi.clone())
            self.buffer_y.append(yi.clone())
        else:
            j = np.random.randint(0, self._n_seen)
            if j < self.capacity:
                self.buffer_x[j] = xi.clone()
                self.buffer_y[j] = yi.clone()
```

---

## Training Config
- Tasks: 4, buffer size: 160, replay batch: 40
- lr: 0.0005, Epochs per task: 11, Batch: 32

## Deliverables
1. Fixed `replay_buffer.py` with reservoir sampling
2. `training_results.json` after running `python train.py`
3. `python check_continual.py` exits 0
