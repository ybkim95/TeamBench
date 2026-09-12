"""Validate dataset version mismatch fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import (make_labels_v2_0, make_labels_v2_1,
                     load_train_labels, load_eval_labels,
                     get_label_versions_match, count_label_mismatches)


def check_versions_match_flag():
    """Verify get_label_versions_match() returns True."""
    result = get_label_versions_match()
    if not result:
        return False, "get_label_versions_match() returns False — versions still mismatched"
    return True, "get_label_versions_match() returns True"


def check_eval_labels_are_v21():
    """Verify load_eval_labels returns v2.1 labels (not v2.0)."""
    eval_labels = load_eval_labels(n=200, seed=42)
    v21_labels  = make_labels_v2_1(n=200, seed=42)
    v20_labels  = make_labels_v2_0(n=200, seed=42)

    match_v21 = (eval_labels == v21_labels).mean()
    match_v20 = (eval_labels == v20_labels).mean()

    if match_v21 < 0.99:
        return False, (
            f"load_eval_labels does not match v2.1 (match={match_v21:.4f}), "
            f"matches v2.0 better ({match_v20:.4f}) — version mismatch not fixed"
        )
    return True, f"load_eval_labels matches v2.1 labels (match={match_v21:.4f})"


def check_train_and_eval_same_version():
    """Verify train and eval labels are identical."""
    train_labels = load_train_labels(n=200, seed=42)
    eval_labels  = load_eval_labels(n=200, seed=42)

    match = (train_labels == eval_labels).mean()
    if match < 0.99:
        return False, (
            f"Train and eval labels differ: match={match:.4f} "
            f"(expected 1.0 — same version)"
        )
    return True, f"Train and eval labels identical (match={match:.4f})"


def check_source_eval_uses_v21():
    """Verify load_eval_labels calls make_labels_v2_1, not make_labels_v2_0."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset.py')) as f:
        src = f.read()
    import re
    fn_match = re.search(r'def load_eval_labels.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "load_eval_labels not found in dataset.py"
    fn_body = fn_match.group(0)

    if 'make_labels_v2_0' in fn_body:
        return False, "load_eval_labels still calls make_labels_v2_0 (bug not fixed)"
    if 'make_labels_v2_1' not in fn_body:
        return False, "load_eval_labels does not call make_labels_v2_1"
    return True, "load_eval_labels calls make_labels_v2_1"


def check_versions_match_returns_true_in_source():
    """Verify get_label_versions_match returns True."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset.py')) as f:
        src = f.read()
    import re
    fn_match = re.search(r'def get_label_versions_match.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "get_label_versions_match not found"
    fn_body = fn_match.group(0)
    if 'return False' in fn_body:
        return False, "get_label_versions_match still returns False"
    if 'return True' not in fn_body:
        return False, "get_label_versions_match does not return True"
    return True, "get_label_versions_match returns True"


def check_v20_v21_genuinely_differ():
    """Verify v2.0 and v2.1 labels are actually different (test data integrity)."""
    v20 = make_labels_v2_0(n=500, seed=42)
    v21 = make_labels_v2_1(n=500, seed=42)
    mismatch_rate = (v20 != v21).mean()
    expected = 0.12
    if mismatch_rate < 0.05:
        return False, f"v2.0 and v2.1 labels are too similar (mismatch_rate={mismatch_rate:.4f})"
    return True, f"v2.0 vs v2.1 mismatch rate: {mismatch_rate:.4f} (expected ~0.12)"


def check_training_results_versions_match():
    """Verify training_results.json has versions_match=True."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if not res.get("versions_match", False):
        mismatch = res.get("label_mismatch_rate", "?")
        return False, f"versions_match=False in results, mismatch_rate={mismatch}"
    return True, "versions_match=True in training_results.json"


def check_mismatch_rate_near_zero():
    """Verify label_mismatch_rate is near zero (train/eval use same version)."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    rate = res.get("label_mismatch_rate", 1.0)
    if rate > 0.02:
        return False, f"label_mismatch_rate={rate:.4f} > 0.02 — versions still differ"
    return True, f"label_mismatch_rate={rate:.4f} ~= 0 (versions aligned)"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    versions_match = res.get("versions_match", False)
    mismatch_rate = res.get("label_mismatch_rate", "?")
    print(f"Final val acc: {acc:.4f}, versions_match={versions_match}, mismatch_rate={mismatch_rate}")

    checks = [
        check_versions_match_flag,
        check_eval_labels_are_v21,
        check_train_and_eval_same_version,
        check_source_eval_uses_v21,
        check_versions_match_returns_true_in_source,
        check_v20_v21_genuinely_differ,
        check_training_results_versions_match,
        check_mismatch_rate_near_zero,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (val_acc={acc:.4f} < 0.50)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
