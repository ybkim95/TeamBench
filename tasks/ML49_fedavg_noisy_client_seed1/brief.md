# ML49: FedAvg Noisy Client Bug (Brief)

## Your Task
Fix the FedAvg aggregation in `fedavg.py` to clip client updates.

**federated learning with imbalanced data sizes** fails because one large client with noisy data
dominates the sample-weighted aggregation, corrupting the global model.

## Symptoms
- Global model accuracy near random chance (1/5 ≈ 0.20)
- Clean clients' updates are overwhelmed by the noisy large client
- Loss does not decrease despite most clients training correctly

## What to Fix
- `fedavg.py`: `FedAvgServer.aggregate()` — compute delta, clip to `clip_norm=1.0`, use uniform weights
- Do NOT modify `train.py`

## Success Criteria
- `python check_fedavg.py` exits 0
- Final accuracy > 0.5
