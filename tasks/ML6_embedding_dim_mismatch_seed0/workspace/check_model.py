"""Check that model forward pass succeeds with correct dimensions."""
import torch
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check():
    try:
        from model import TextClassifier
    except ImportError as e:
        print(f"ERROR: Cannot import model: {e}")
        return False

    checks = []

    # Check 1: Model instantiates without error
    try:
        model = TextClassifier()
        checks.append(("model_instantiates", True, "OK"))
    except Exception as e:
        checks.append(("model_instantiates", False, str(e)))
        model = None

    # Check 2: Forward pass succeeds
    if model is not None:
        try:
            x = torch.randint(0, 10000, (4, 64))
            with torch.no_grad():
                out = model(x)
            checks.append(("forward_pass_succeeds", True, f"output shape: {out.shape}"))
        except RuntimeError as e:
            checks.append(("forward_pass_succeeds", False, f"RuntimeError: {e}"))
        except Exception as e:
            checks.append(("forward_pass_succeeds", False, str(e)))

    # Check 3: Output has correct number of classes
    if model is not None:
        try:
            x = torch.randint(0, 10000, (4, 64))
            with torch.no_grad():
                out = model(x)
            n_classes_ok = out.shape[-1] == 5
            checks.append(("output_classes_correct",
                           n_classes_ok,
                           f"output classes={out.shape[-1]}, expected=5"))
        except Exception:
            checks.append(("output_classes_correct", False, "forward pass failed"))

    # Check 4: No dimension mismatch in layer definitions
    try:
        import inspect
        with open("model.py") as f:
            src = f.read()
        # The correct embedding dim should appear, not the wrong one
        correct_emb = 256
        wrong_emb = 512
        # Heuristic: correct dim should appear in projection layers
        checks.append(("correct_dims_present",
                       str(correct_emb) in src,
                       f"correct embedding_dim=256 not found in model.py"))
    except Exception as e:
        checks.append(("correct_dims_present", False, str(e)))

    all_pass = True
    results = {}
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        results[name] = ok
        if not ok:
            all_pass = False

    with open("model_check_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
