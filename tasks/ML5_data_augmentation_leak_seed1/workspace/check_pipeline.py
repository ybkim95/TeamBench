"""Check pipeline correctness and design-choice preservation."""
import json
import sys
import os


def check():
    if not os.path.exists("pipeline_results.json"):
        print("ERROR: pipeline_results.json not found. Run augment_pipeline.py first.")
        return False

    with open("pipeline_results.json") as f:
        r = json.load(f)

    checks = []

    # Real bug 1: augmentation must happen AFTER split
    aug_before = r.get("augmentation_applied_before_split", True)
    checks.append(("augment_after_split",
                   not aug_before,
                   "augmentation still applied before split (test contaminated)"))

    # Real bug 2: normalization must be fitted on train only
    norm_before = r.get("normalization_applied_before_split", True)
    checks.append(("normalization_after_split",
                   not norm_before,
                   "StandardScaler still fitted on full dataset (leaks test distribution)"))

    # Test set size should be from original (not augmented) data
    n_test = r.get("n_test", 0)
    n_orig = r.get("n_original", 1000)
    expected_test = int(n_orig * 0.2)
    checks.append(("test_size_correct",
                   abs(n_test - expected_test) <= max(5, int(expected_test * 0.10)),
                   f"n_test={n_test}, expected ~{expected_test} (original test fraction)"))

    # Train set should be augmented
    n_train = r.get("n_train", 0)
    checks.append(("train_set_augmented",
                   n_train > int(n_orig * (1 - 0.2)),
                   f"n_train={n_train} not larger than original train 800"))

    # Intentional: label smoothing must be preserved
    checks.append(("label_smoothing_preserved",
                   r.get("label_smoothing_preserved", False),
                   "label_smoothing removed"))

    checks.append(("augmentation_seed_preserved",
                   r.get("augmentation_seed_preserved", False) and r.get("augmentation_seed") == 42,
                   "AUGMENTATION_SEED=42 removed/changed"))

    checks.append(("tta_preserved",
                   r.get("tta_preserved", False),
                   "tta_predict removed"))

    all_pass = True
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
