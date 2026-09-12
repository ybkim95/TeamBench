# ML30: Image Augmentation Applied After Normalization

## Goal
Fix `augment.py` so augmentation transforms are applied BEFORE normalization.
Run `python train.py` then `python check_augment.py` — both must pass.

## Task
Building an image augmentation pipeline for a **tiny image dataset with color augmentation**.
Images: 3×28×28, pixel values in [0, 1].
Normalization stats: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]

---

## The Bug: Normalize Before Augment

**Location**: `train_transform()` in `augment.py`

### Background: Expected Pixel Value Ranges

| Stage | Pixel values | Expected by |
|-------|-------------|-------------|
| Raw image | [0.0, 1.0] | augmentation transforms |
| After augment | [0.0, 1.0] (approx) | normalization |
| After normalize | ~[-2.0, 2.0] | model input |

### Current (Buggy) Code

```python
def train_transform(x):
    x = normalize(x)              # BUG: values → ~[-2, 2] first
    x = random_horizontal_flip(x) # OK geometrically
    x = random_crop(x, pad=3)       # padding fills 0.0, but 0.0 ≠ black after norm
    x = apply_color_jitter(x)     # BUG: jitter on ~[-2, 2], designed for [0, 1]
    return x
```

**Problems**:
1. `apply_color_jitter` / `apply_brightness` adds brightness scaled for [0,1] but input is [-2,2]
2. `random_crop` pads with 0.0 — correct for [0,1] (black pixel) but wrong after normalization
3. Training data distribution differs from inference (only normalize at inference)

### Correct Fix

```python
def train_transform(x):
    # Augment FIRST (on raw [0,1] pixel values)
    x = random_horizontal_flip(x)
    x = random_crop(x, pad=3)
    x = apply_color_jitter(x)     # now operates on [0,1] as designed
    x = normalize(x)              # normalize LAST
    return x
```

Also update `get_pipeline_order()` to return `"flip,crop,color,normalize"`.

### Inference Consistency

At inference, only `val_transform` (normalize only) is used.
This is only consistent if training augmentation also ends with normalize.

---

## Training Config
- Image size: 3×28×28
- LR: 0.0005, Epochs: 24, Batch: 16

## Deliverables
1. Fixed `augment.py` with augment-then-normalize order
2. Updated `get_pipeline_order()` returning correct order string
3. `training_results.json` after running `python train.py`
4. `python check_augment.py` exits 0
