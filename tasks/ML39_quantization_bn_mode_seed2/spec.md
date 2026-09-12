# ML39: Quantization BN Mode Mismatch (train() During Calibration)

## Goal
Fix `quantize.py` so `calibrate_model()` uses `model.eval()` before the calibration loop.
Run `python quantize.py` then `python check_quantization.py` — both must pass.

## Task
A **feedforward network with batch normalization layers** is being quantized using Post-Training Quantization (PTQ).
During calibration (collecting activation statistics for quantization range estimation),
the model is left in `train()` mode. BatchNorm layers use noisy batch statistics
instead of stable running statistics, making activation ranges inaccurate.

---

## The Bug: model.train() During PTQ Calibration

### Background: BatchNorm in train vs eval mode

**Train mode** (`model.train()`):
```
BN output = (x - batch_mean) / sqrt(batch_var + eps) * gamma + beta
```
- Uses statistics from the **current batch** — varies with each input
- Noisy for small calibration batches

**Eval mode** (`model.eval()`):
```
BN output = (x - running_mean) / sqrt(running_var + eps) * gamma + beta
```
- Uses **running statistics** accumulated during training — stable

For PTQ calibration, we need **stable, representative** activation distributions.
Using train() mode gives different activation ranges for each batch, producing
noisy quantization scales and degrading post-quantization accuracy.

### Current (Buggy) Code

```python
def calibrate_model(model, calib_x):
    model.train()   # BUG: noisy batch stats corrupt activation range estimation
    return simulate_quantization(model, calib_x)
```

### Correct Fix

```python
def calibrate_model(model, calib_x):
    model.eval()    # Correct: stable running stats → accurate activation ranges
    return simulate_quantization(model, calib_x)
```

Also update `results["calibration_mode"] = "eval"`.

---

## Config
- n_train: 628, n_calib: 111, n_test: 221
- batch_size: 32, calib_batch: 8, epochs: 20, lr: 0.002

## Deliverables
1. Fixed `quantize.py` with `model.eval()` in `calibrate_model()`
2. `quantization_results.json` with `calibration_mode: "eval"` and `accuracy_drop < 0.10`
3. `python check_quantization.py` exits 0
