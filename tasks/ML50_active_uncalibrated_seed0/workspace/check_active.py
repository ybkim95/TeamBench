"""Validate active learning strategy fix."""
import json
import sys
import os
import torch
import torch.nn.functional as F
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from query_strategy import EntropyStrategy, MCDropoutStrategy
from model import ActiveModel


def check_mc_dropout_strategy_exists():
    """Verify MCDropoutStrategy is implemented."""
    mc = MCDropoutStrategy()
    if not hasattr(mc, "select"):
        return False, "MCDropoutStrategy missing select() method"
    if not hasattr(mc, "n_mc_samples"):
        return False, "MCDropoutStrategy missing n_mc_samples attribute"
    return True, f"MCDropoutStrategy exists with n_mc_samples={mc.n_mc_samples}"


def check_mc_uses_dropout_enabled():
    """Verify MC strategy runs model in train mode (dropout enabled)."""
    with open("query_strategy.py") as f:
        src = f.read()
    mc_section = src[src.find("class MCDropoutStrategy"):]
    if "model.train()" not in mc_section:
        return False, "MCDropoutStrategy.select() does not call model.train() to enable dropout"
    return True, "MC strategy enables dropout via model.train()"


def check_different_selections():
    """Verify MC Dropout selects different samples than raw entropy."""
    torch.manual_seed(0)
    np.random.seed(0)
    model = ActiveModel()
    X = torch.randn(100, 20)

    entropy_strat = EntropyStrategy()
    mc_strat = MCDropoutStrategy(n_mc_samples=20)

    entropy_idx = set(entropy_strat.select(model, X, 10).tolist())
    mc_idx = set(mc_strat.select(model, X, 10).tolist())

    overlap = len(entropy_idx & mc_idx)
    if overlap == 10:
        return False, "MC Dropout selects identical samples as entropy — strategies are the same"
    return True, f"MC and entropy select different samples (overlap={overlap}/10)"


def check_bald_score_computation():
    """Verify BALD = H(mean) - E[H] is computed."""
    with open("query_strategy.py") as f:
        src = f.read()
    mc_section = src[src.find("class MCDropoutStrategy"):]
    has_bald = (
        ("H_mean" in mc_section and "E_H" in mc_section) or
        ("bald" in mc_section.lower()) or
        ("H_mean - E_H" in mc_section) or
        ("mean_probs" in mc_section and "individual" in mc_section.lower())
    )
    if not has_bald:
        return False, "BALD computation not found in MCDropoutStrategy"
    return True, "BALD score computation present"


def check_mc_selects_boundary_samples():
    """Verify MC Dropout selects samples near decision boundary."""
    torch.manual_seed(42)
    model = ActiveModel()

    # Create pool: half clearly in-class (far from boundary), half near boundary
    n_clear = 50
    n_boundary = 50
    n_classes = 4

    # Clear samples: close to class centers
    centers = torch.eye(n_classes, 20) * 5.0
    X_clear = torch.cat([centers[c] + 0.1 * torch.randn(n_clear // n_classes, 20)
                          for c in range(n_classes)])

    # Boundary samples: midpoint between two class centers
    X_boundary = 0.5 * (centers[0] + centers[1]) + 0.3 * torch.randn(n_boundary, 20)

    X_pool = torch.cat([X_clear, X_boundary])
    labels_true = torch.cat([
        torch.cat([torch.full((n_clear // n_classes,), c) for c in range(n_classes)]),
        torch.zeros(n_boundary, dtype=torch.long)
    ])

    mc_strat = MCDropoutStrategy(n_mc_samples=20)
    selected = mc_strat.select(model, X_pool, 10)

    # Boundary samples have indices [n_clear, n_clear + n_boundary)
    n_boundary_selected = sum(1 for s in selected if s >= n_clear)
    if n_boundary_selected < 4:
        return False, (
            f"MC Dropout selected only {n_boundary_selected}/10 boundary samples "
            f"(expected >= 4). May be selecting easy samples instead of hard."
        )
    return True, f"MC Dropout selected {n_boundary_selected}/10 near-boundary samples"


def check_variance_across_passes():
    """Verify MC passes produce different predictions (dropout is active)."""
    torch.manual_seed(0)
    model = ActiveModel()
    model.train()  # enable dropout
    X = torch.randn(20, 20)

    preds = []
    with torch.no_grad():
        for _ in range(20):
            p = F.softmax(model(X), dim=1)
            preds.append(p)

    preds = torch.stack(preds)
    variance = preds.var(0).mean().item()
    if variance < 1e-6:
        return False, f"MC passes produce identical predictions (variance={variance:.8f}) — dropout may not be enabled"
    return True, f"MC passes have variance={variance:.6f} — dropout working"


def check_entropy_vs_mc_training_results():
    """Verify MC Dropout outperforms entropy in training results."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    mc_auc = res.get("mc_auc", 0)
    entropy_auc = res.get("entropy_auc", 0)
    if not res.get("mc_better", False):
        return False, f"MC Dropout AUC ({mc_auc:.3f}) not better than entropy AUC ({entropy_auc:.3f})"
    return True, f"MC better than entropy: mc={mc_auc:.3f} > entropy={entropy_auc:.3f}"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    mc_auc = res.get("mc_auc", 0)
    if not res.get("converged", False):
        return False, f"MC Dropout AUC {mc_auc:.3f} < 0.65 threshold"
    return True, f"MC Dropout converged: AUC={mc_auc:.3f}"


def check():
    checks = [
        ("MCDropoutStrategy exists", check_mc_dropout_strategy_exists),
        ("MC enables dropout", check_mc_uses_dropout_enabled),
        ("Different selections from entropy", check_different_selections),
        ("BALD score computation", check_bald_score_computation),
        ("MC selects boundary samples", check_mc_selects_boundary_samples),
        ("Variance across MC passes", check_variance_across_passes),
        ("MC better than entropy (results)", check_entropy_vs_mc_training_results),
        ("Training AUC threshold", check_training_results),
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
