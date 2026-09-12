# ML39: Quantization BN Mode Bug (Brief)

## Your Task
Fix `quantize.py` — `calibrate_model()` calls `model.train()` instead of `model.eval()`
before running calibration data through the model.

A **ResNet-style CNN with batch normalization** being quantized produces inaccurate activation ranges
because BatchNorm uses noisy batch statistics (train mode) instead of stable
running statistics (eval mode).

## What to Fix
- `quantize.py`: `calibrate_model()` — change `model.train()` to `model.eval()`
- Update `results["calibration_mode"] = "eval"`

## Success Criteria
- `python check_quantization.py` exits 0
- `calibration_mode == "eval"`
- `accuracy_drop < 0.10`
