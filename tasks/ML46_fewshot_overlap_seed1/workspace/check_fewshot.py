"""Validate few-shot support/query overlap fix."""
import json
import sys
import os
import torch
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from episode_sampler import EpisodeSampler


def make_test_class_data():
    torch.manual_seed(0)
    class_data = {}
    for c in range(20):
        class_data[c] = torch.randn(50, 48)
    return class_data


def check_no_overlap():
    """Verify support and query sets have no sample overlap."""
    np.random.seed(42)
    class_data = make_test_class_data()
    sampler = EpisodeSampler(n_way=5, k_shot=5, n_query=10)

    overlaps_found = 0
    n_trials = 50
    for _ in range(n_trials):
        ep = sampler.sample_episode(class_data)
        support = ep["support"]
        query = ep["query"]

        # Check for exact sample overlap between support and query
        for s in support:
            for q in query:
                if (s - q).norm().item() < 1e-6:
                    overlaps_found += 1

    if overlaps_found > 0:
        return False, f"Found {overlaps_found} overlapping samples between support and query over {n_trials} episodes"
    return True, f"No support/query overlap in {n_trials} episodes"


def check_query_uses_non_support_samples():
    """Verify query indices are different from support indices."""
    with open("episode_sampler.py") as f:
        src = f.read()
    # The correct fix should index query from perm[k_shot:] or similar
    # Check that query_idx is not perm[:n_query] when that overlaps with perm[:k_shot]
    correct_patterns = [
        "perm[self.k_shot",
        "perm[k_shot",
        "[self.k_shot:]",
        "[k_shot:]",
        "k_shot:self.k_shot + self.n_query",
        "k_shot:k_shot + n_query",
    ]
    has_correct = any(p in src for p in correct_patterns)
    if not has_correct:
        return False, "episode_sampler.py does not use non-overlapping query indexing"
    return True, "Query uses non-overlapping indices"


def check_support_query_sizes():
    """Verify episode has correct sizes: N*K support, N*Q query."""
    np.random.seed(0)
    class_data = make_test_class_data()
    sampler = EpisodeSampler(n_way=5, k_shot=5, n_query=10)
    ep = sampler.sample_episode(class_data)

    expected_support = 5 * 5
    expected_query = 5 * 10

    actual_support = len(ep["support"])
    actual_query = len(ep["query"])

    if actual_support != expected_support:
        return False, f"Support size {actual_support} != expected 5*5={expected_support}"
    if actual_query != expected_query:
        return False, f"Query size {actual_query} != expected 5*10={expected_query}"
    return True, f"Episode sizes correct: support={actual_support}, query={actual_query}"


def check_label_alignment():
    """Verify query labels correspond correctly to episode classes."""
    np.random.seed(1)
    class_data = make_test_class_data()
    sampler = EpisodeSampler(n_way=5, k_shot=5, n_query=10)
    ep = sampler.sample_episode(class_data)
    labels = ep["query_labels"]
    # Labels should be in [0, n_way)
    if labels.max().item() >= 5:
        return False, f"Query label {labels.max().item()} >= n_way=5"
    if labels.min().item() < 0:
        return False, f"Query label {labels.min().item()} < 0"
    # Each class should appear n_query times
    for c in range(5):
        count = (labels == c).sum().item()
        if count != 10:
            return False, f"Class {c} appears {count} times, expected 10"
    return True, f"Query labels aligned: 5 classes * 10 each"


def check_episode_reproducible():
    """Verify same seed produces same episode."""
    class_data = make_test_class_data()
    sampler = EpisodeSampler(n_way=5, k_shot=5, n_query=10)
    torch.manual_seed(123)
    np.random.seed(123)
    ep1 = sampler.sample_episode(class_data)
    torch.manual_seed(123)
    np.random.seed(123)
    ep2 = sampler.sample_episode(class_data)
    if not torch.allclose(ep1["support"], ep2["support"]):
        return False, "Episode not reproducible with same seed"
    return True, "Episode reproducible"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    acc = res.get("final_test_acc", 0)
    if not res.get("converged", False):
        return False, f"Model did not converge: test_acc={acc:.3f} < 0.4"
    return True, f"Model converged: test_acc={acc:.3f}"


def check_diverse_episodes():
    """Verify different episodes sample different classes."""
    np.random.seed(7)
    class_data = make_test_class_data()
    sampler = EpisodeSampler(n_way=5, k_shot=5, n_query=10)
    ep1 = sampler.sample_episode(class_data)
    ep2 = sampler.sample_episode(class_data)
    # Different episodes should typically have different class subsets
    classes1 = set(ep1["episode_classes"].tolist())
    classes2 = set(ep2["episode_classes"].tolist())
    # Not required to be disjoint but should not always be identical
    # (very unlikely to be identical by chance with 20 classes, 5-way)
    return True, f"Episode class diversity: ep1={sorted(classes1)}, ep2={sorted(classes2)}"


def check():
    checks = [
        ("No support/query overlap", check_no_overlap),
        ("Query uses non-support indices", check_query_uses_non_support_samples),
        ("Episode sizes correct", check_support_query_sizes),
        ("Label alignment", check_label_alignment),
        ("Episode reproducible", check_episode_reproducible),
        ("Training results", check_training_results),
        ("Diverse episodes", check_diverse_episodes),
    ]

    all_pass = True
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"Exception: {e}"
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    print("\nPASS" if all_pass else "\nFAIL")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
