"""Validate FedAvg noisy client fix."""
import json
import sys
import os
import torch
import copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fedavg import ClientModel, FedAvgServer


def make_model():
    return ClientModel(input_dim=16, hidden_dim=64, n_classes=4)


def check_clipping_in_aggregate():
    """Verify update norm clipping is applied."""
    with open("fedavg.py") as f:
        src = f.read()
    has_clip = "clip_norm" in src and (
        "scale" in src or "clip" in src.lower() or "norm" in src
    )
    if not has_clip:
        return False, "fedavg.py aggregate() does not appear to clip update norms"
    return True, "Norm clipping present in aggregate()"


def check_large_client_limited():
    """Verify a large noisy client cannot dominate aggregation."""
    torch.manual_seed(0)
    model = make_model()
    server = FedAvgServer(model, clip_norm=2.0)
    global_state = {k: v.clone() for k, v in model.state_dict().items()}

    # Create updates: one large noisy client, several clean clients
    n_clients = 10
    clean_update = {k: v + 0.01 * torch.randn_like(v) for k, v in global_state.items()}
    noisy_update = {k: v + 100.0 * torch.randn_like(v) for k, v in global_state.items()}

    updates = [noisy_update] + [clean_update] * (n_clients - 1)
    n_samples = [1000] + [100] * (n_clients - 1)  # noisy client 10x larger

    server.aggregate(updates, n_samples)
    new_state = server.global_model.state_dict()

    # The aggregated model should be close to clean_update, not noisy_update
    dist_to_clean = sum(
        (new_state[k] - clean_update[k]).norm().item()
        for k in global_state
    )
    dist_to_noisy = sum(
        (new_state[k] - noisy_update[k]).norm().item()
        for k in global_state
    )

    if dist_to_noisy < dist_to_clean:
        return False, (
            f"Aggregated model closer to noisy client (dist={dist_to_noisy:.4f}) "
            f"than clean clients (dist={dist_to_clean:.4f}). "
            "Large noisy client still dominates."
        )
    return True, (
        f"Clean clients dominate: dist_to_clean={dist_to_clean:.4f} < "
        f"dist_to_noisy={dist_to_noisy:.4f}"
    )


def check_clip_norm_applied():
    """Verify clip_norm attribute is used."""
    model = make_model()
    server = FedAvgServer(model, clip_norm=2.0)
    if server.clip_norm != 2.0:
        return False, f"clip_norm={server.clip_norm} != 2.0"
    return True, f"clip_norm={server.clip_norm} set correctly"


def check_aggregate_finite():
    """Verify aggregation produces finite model parameters."""
    torch.manual_seed(0)
    model = make_model()
    server = FedAvgServer(model, clip_norm=2.0)
    global_state = {k: v.clone() for k, v in model.state_dict().items()}

    # Very large update from one client
    huge_update = {k: v + 1e6 * torch.randn_like(v) for k, v in global_state.items()}
    small_update = {k: v.clone() for k, v in global_state.items()}

    server.aggregate([huge_update, small_update], [1000, 100])
    new_state = server.global_model.state_dict()
    for k, v in new_state.items():
        if not torch.isfinite(v).all():
            return False, f"Parameter {k} is non-finite after aggregating huge update"
    return True, "All parameters finite after aggregating large update"


def check_uniform_or_clipped():
    """Verify weighting is either uniform or uses clipped deltas."""
    with open("fedavg.py") as f:
        src = f.read()
    # Should NOT use raw n / n_total weighting without clipping
    uses_raw_weight = (
        "n / n_total" in src or
        "n_samples[" in src and "clip" not in src.lower()
    )
    uses_clipping = "clip_norm" in src and ("scale" in src or "min(1" in src or "norm" in src)
    uses_uniform = "1.0 / len(" in src or "1 / len(" in src or "1/len(" in src

    if not (uses_clipping or uses_uniform):
        return False, "aggregate() neither clips updates nor uses uniform weighting"
    return True, "Aggregation uses clipping or uniform weights"


def check_multiple_rounds_stable():
    """Verify multiple rounds of aggregation stay stable."""
    torch.manual_seed(1)
    model = make_model()
    server = FedAvgServer(model, clip_norm=2.0)

    for _ in range(5):
        global_state = {k: v.clone() for k, v in server.global_model.state_dict().items()}
        updates = [
            {k: v + 10.0 * torch.randn_like(v) for k, v in global_state.items()}
        ] + [
            {k: v + 0.01 * torch.randn_like(v) for k, v in global_state.items()}
            for _ in range(10 - 1)
        ]
        n_samples = [500] + [50] * (10 - 1)
        server.aggregate(updates, n_samples)

    final_state = server.global_model.state_dict()
    for k, v in final_state.items():
        if not torch.isfinite(v).all():
            return False, f"Parameter {k} non-finite after 5 rounds"
        if v.norm().item() > 1e4:
            return False, f"Parameter {k} norm={v.norm().item():.2e} exploded"
    return True, "5 rounds stable with noisy large client"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    acc = res.get("final_acc", 0)
    if not res.get("converged", False):
        return False, f"FedAvg did not converge: acc={acc:.3f} < 0.5"
    return True, f"FedAvg converged: acc={acc:.3f}"


def check():
    checks = [
        ("Clipping in aggregate", check_clipping_in_aggregate),
        ("Large client limited", check_large_client_limited),
        ("clip_norm applied", check_clip_norm_applied),
        ("Aggregate finite", check_aggregate_finite),
        ("Uniform or clipped weighting", check_uniform_or_clipped),
        ("Multiple rounds stable", check_multiple_rounds_stable),
        ("Training results", check_training_results),
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
