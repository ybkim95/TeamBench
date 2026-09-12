"""Validate point-in-time join fix."""
import json
import sys
import os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_store import (make_feature_store, make_label_events,
                           get_features_at, check_pit_correctness, FEATURE_NAMES)


def check_uses_strict_lt():
    """Verify check_pit_correctness returns uses_strict_lt=True."""
    result = check_pit_correctness()
    if not result.get("uses_strict_lt", False):
        return False, f"uses_strict_lt=False, operator={result.get('operator', '?')}"
    return True, f"uses_strict_lt=True, operator={result.get('operator')}"


def check_source_uses_lt():
    """Verify feature_store.py uses < not <= for point-in-time join."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feature_store.py')) as f:
        src = f.read()
    import re
    # Find get_features_at function
    fn_match = re.search(r'def get_features_at.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "get_features_at function not found"
    fn_body = fn_match.group(0)

    # Must use strict < (not <=) on the timestamp comparison
    if re.search(r'\["ts"\]\s*<=\s*event_ts', fn_body):
        return False, 'Still uses ts <= event_ts (point-in-time leak not fixed)'
    if not re.search(r'\["ts"\]\s*<\s*event_ts', fn_body):
        return False, 'Strict ts < event_ts not found in get_features_at'
    return True, "get_features_at uses strict < for point-in-time join"


def check_same_ts_excluded():
    """Verify features at exact event_ts are excluded."""
    # Build a minimal feature store: entity 0 has features at ts=100, 200, 300
    rows = [
        {"entity_id": 0, "ts": 100, **{n: 0.1 * (i+1) for i, n in enumerate(FEATURE_NAMES)}},
        {"entity_id": 0, "ts": 200, **{n: 0.2 * (i+1) for i, n in enumerate(FEATURE_NAMES)}},
        {"entity_id": 0, "ts": 300, **{n: 0.3 * (i+1) for i, n in enumerate(FEATURE_NAMES)}},
    ]
    store = pd.DataFrame(rows)

    # Event at ts=300 (same as last feature snapshot)
    feats = get_features_at(entity_id=0, event_ts=300, feature_store=store)

    # With < fix: should return features from ts=200 (not ts=300)
    expected_val = 0.2 * 1  # FEATURE_NAMES[0] at ts=200
    if abs(feats[0] - expected_val) > 1e-4:
        # Could be ts=300 features (bug) or ts=200 (fix)
        if abs(feats[0] - 0.3) < 1e-4:
            return False, f"Features at event_ts=300 are included (val={feats[0]:.4f}) — <= bug not fixed"
        return False, f"Unexpected feature value: {feats[0]:.4f}, expected ~{expected_val:.4f} (ts=200)"
    return True, f"Features at event_ts excluded; got ts=200 features (val={feats[0]:.4f})"


def check_future_features_excluded():
    """Verify features after event_ts are also excluded."""
    rows = [
        {"entity_id": 0, "ts": 100, **{n: 1.0 for n in FEATURE_NAMES}},
        {"entity_id": 0, "ts": 200, **{n: 2.0 for n in FEATURE_NAMES}},
        {"entity_id": 0, "ts": 300, **{n: 3.0 for n in FEATURE_NAMES}},
    ]
    store = pd.DataFrame(rows)

    # Event at ts=150 — only ts=100 feature should be available
    feats = get_features_at(entity_id=0, event_ts=150, feature_store=store)
    if abs(feats[0] - 1.0) > 1e-4:
        return False, f"Expected ts=100 features (val=1.0), got {feats[0]:.4f}"
    return True, f"Only past features returned for event at ts=150"


def check_no_features_before_event_returns_zeros():
    """Verify empty result when no features available before event."""
    rows = [
        {"entity_id": 0, "ts": 500, **{n: 9.9 for n in FEATURE_NAMES}},
    ]
    store = pd.DataFrame(rows)

    # Event at ts=100 — no features available (all at ts=500 > 100)
    feats = get_features_at(entity_id=0, event_ts=100, feature_store=store)
    if feats.sum() != 0.0:
        return False, f"Expected zeros when no prior features, got {feats}"
    return True, "Returns zero vector when no features available before event"


def check_most_recent_features_used():
    """Verify the most recent pre-event features are used (not oldest)."""
    rows = [
        {"entity_id": 0, "ts": 100, **{n: 1.0 for n in FEATURE_NAMES}},
        {"entity_id": 0, "ts": 200, **{n: 2.0 for n in FEATURE_NAMES}},
        {"entity_id": 0, "ts": 250, **{n: 2.5 for n in FEATURE_NAMES}},
    ]
    store = pd.DataFrame(rows)

    # Event at ts=300 (after all feature snapshots) — should use ts=250
    feats = get_features_at(entity_id=0, event_ts=300, feature_store=store)
    if abs(feats[0] - 2.5) > 1e-4:
        return False, f"Expected most recent features (ts=250, val=2.5), got {feats[0]:.4f}"
    return True, "Most recent pre-event features returned"


def check_training_results_pit_flag():
    """Verify training_results.json has uses_strict_lt=True."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if not res.get("uses_strict_lt", False):
        return False, f"uses_strict_lt=False, operator={res.get('pit_operator', '?')}"
    return True, f"uses_strict_lt=True, operator={res.get('pit_operator')}"


def check_entity_isolation():
    """Verify features from other entities are not returned."""
    rows = [
        {"entity_id": 0, "ts": 100, **{n: 1.0 for n in FEATURE_NAMES}},
        {"entity_id": 1, "ts": 50,  **{n: 9.0 for n in FEATURE_NAMES}},
    ]
    store = pd.DataFrame(rows)
    feats = get_features_at(entity_id=0, event_ts=200, feature_store=store)
    if abs(feats[0] - 1.0) > 1e-4:
        return False, f"Entity isolation broken: got {feats[0]:.4f}, expected 1.0 for entity 0"
    return True, "Entity features are correctly isolated"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    operator = res.get("pit_operator", "?")
    print(f"Final val acc: {acc:.4f}, PIT operator: {operator!r}")

    checks = [
        check_uses_strict_lt,
        check_source_uses_lt,
        check_same_ts_excluded,
        check_future_features_excluded,
        check_no_features_before_event_returns_zeros,
        check_most_recent_features_used,
        check_training_results_pit_flag,
        check_entity_isolation,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (val_acc={acc:.4f} < 0.45)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
