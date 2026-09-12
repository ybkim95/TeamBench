# ML49: FedAvg Poisoned by Noisy Large Client

## Goal
Fix `fedavg.py` so aggregation clips client updates to prevent noisy clients from dominating.
Run `python train.py` then `python check_fedavg.py` — both must pass.

## Task
**federated learning with imbalanced data sizes** with 8 clients, one of which has 10x
more data with random labels. The global model must achieve >0.5 accuracy.

---

## The Bug: Sample-Weighted Aggregation Dominated by Noisy Client

**Location**: `fedavg.py` `FedAvgServer.aggregate()` — weight computation

### Background: FedAvg Aggregation

Standard FedAvg weights each client by its sample count:
```
w_i = n_i / sum(n_j)
global_params = sum(w_i * client_params_i)
```

**Problem**: Client 0 has 10x more samples than any other client,
and its data is pure noise (random labels). Its weight is `10/(10 + 7) ≈ 0.59`,
dominating the aggregation and destroying the useful updates from honest clients.

### Fix: Clip Update Deltas

Compute the update **delta** (diff from global model), clip its L2 norm to
`clip_norm = 1.0`, then aggregate with **uniform weights**:

```python
delta = {k: update[k] - global_state[k] for k in global_state}
delta_norm = sum(d.norm()**2 for d in delta.values()) ** 0.5
scale = min(1.0, self.clip_norm / (delta_norm + 1e-8))

weight = 1.0 / len(client_updates)  # uniform
for k in global_state:
    new_state[k] += weight * (global_state[k] + scale * delta[k])
```

This limits any single client's influence to at most `clip_norm` in L2 norm.

---

## Training Config
- 8 clients, lr: 0.005, local epochs: 3
- Noisy client: 10x data, random labels, clip_norm: 1.0

## Deliverables
1. Fixed `fedavg.py` with update norm clipping
2. `training_results.json` after running `python train.py`
3. `python check_fedavg.py` exits 0
