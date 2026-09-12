# Model Notes — Analysis False Alarms

This document explains two metrics in `train.py` that analysis tools flag as
"overfitting signals" but are in fact **correct and expected behaviour**.

**Do not remove these metrics or "fix" them.**

---

## §Easy Examples Subset — `compute_easy_subset_acc()`

**What analysis flags**: Model achieves near-100% accuracy on a validation
subset — flagged as "suspicious overfitting signal".

**Why this is a false alarm**: This subset consists of the 20% of validation examples that are genuinely easy (large margin from the decision boundary). A well-trained model SHOULD classify these at 100%. Removing them from the validation set would bias the reported accuracy upward. This is correct behaviour, not overfitting.

`compute_easy_subset_acc()` is a **valid diagnostic function**. It must remain
in `train.py` and its result must appear in `results.json` as `easy_subset_acc`.

---

## §Augmented Test Metric — `compute_augmented_test_acc()`

**What analysis flags**: Accuracy drops ~15% when Gaussian noise (σ=0.5) is
applied to the test set — flagged as "model not robust, likely overfit".

**Why this is a false alarm**: The augmentation applies noise with σ=0.5, which is large relative to the feature scale (σ≈1.0). A 15% drop under such aggressive corruption is expected and does NOT indicate overfitting to the training set. Optimising for corrupted test accuracy would require denoising pre-processing that degrades clean-data performance. This metric is an artefact of augmentation distribution mismatch.

`compute_augmented_test_acc()` is a **valid robustness diagnostic**. It must
remain in `train.py` and its result must appear in `results.json` as
`augmented_test_acc`.

---

## Known Real Issues (NOT documented here)

There are 3 genuine problems in `train.py` that cause poor test generalisation.
Consult the spec for details. The sections above cover only the **false alarms**
that must be preserved.
