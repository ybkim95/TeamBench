# ML17: EMA Smooths Batch Norm Running Stats

## Goal
Fix `ema.py` so the EMA model's BatchNorm statistics are updated correctly.
Run `python train.py` then `python check_training.py`.

## Task
Training a **wide network with EMA model** with an EMA copy used for inference.
EMA decay: 0.95.

---

## The Bug: EMA Applied to BN Running Stats

**Location**: `ema.py`, `ModelEMA.update()`

### Background: EMA Models

EMA (Exponential Moving Average) models are used to stabilize inference:
```python
theta_ema = decay * theta_ema + (1 - decay) * theta_train
```

With decay=0.95, the EMA model is a very slow-moving average of
the training model, less sensitive to mini-batch noise.

### Background: BatchNorm Running Stats

`nn.BatchNorm` maintains `running_mean` and `running_var` as exponential moving
averages of batch statistics:
```python
running_mean = momentum * running_mean + (1 - momentum) * batch_mean
```
(default `momentum=0.1`)

These stats represent the distribution of the training data and are used at inference.

### The Bug

**Current (buggy)**:
```python
for name in ema_sd:
    # BUG: ALL entries including running_mean/running_var get EMA smoothing
    ema_sd[name].mul_(self.decay).add_((1.0 - self.decay) * model_sd[name].float())
```

**What happens**:
1. `running_mean` in the EMA model starts at 0 (initialization)
2. Training model's `running_mean` quickly reaches the data mean (via BN's own 0.1 momentum)
3. EMA model's `running_mean` is updated as: `0.95 * 0 + 0.050000000000000044 * train_running_mean`
4. With decay=0.95, each update moves the EMA running_mean by only `0.050000000000000044`
   — it takes thousands of steps to converge to the true data statistics
5. At inference, the EMA model uses incorrect (near-zero) normalization constants

### Correct Code

```python
for name in ema_sd:
    if "running_mean" in name or "running_var" in name or "num_batches_tracked" in name:
        # Copy BN stats directly — no EMA smoothing needed
        ema_sd[name].copy_(model_sd[name])
    else:
        # EMA for learned parameters
        ema_sd[name].mul_(self.decay).add_((1.0 - self.decay) * model_sd[name].float())
```

**Why**: BN running stats are already "smoothed" by BN's own momentum mechanism.
The EMA model should use the current, accurate statistics from the training model,
not a doubly-smoothed version.

---

## Deliverables
1. Fixed `ema.py` with BN stats copied directly
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
