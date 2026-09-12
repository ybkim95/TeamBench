"""Validate quantization calibration mode fix."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("quantization_results.json"):
        return False, "quantization_results.json not found"
    return True, "quantization_results.json exists"


def check_calibration_mode_is_eval():
    """calibration_mode must be \'eval\' not \'train\'."""
    with open("quantization_results.json") as f:
        res = json.load(f)
    mode = res.get("calibration_mode", "unknown")
    if mode != "eval":
        return False, f"calibration_mode=\'{mode}\' (expected \'eval\')"
    return True, "calibration_mode=\'eval\'"


def check_no_train_mode_in_calibrate():
    """calibrate_model() must not call model.train()."""
    with open("quantize.py") as f:
        src = f.read()

    # Find calibrate_model function body
    func_match = re.search(r"def calibrate_model.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "calibrate_model function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    if "model.train()" in active_src:
        return False, "calibrate_model still calls model.train()"
    return True, "calibrate_model does not call model.train()"


def check_eval_mode_in_calibrate():
    """calibrate_model() must call model.eval()."""
    with open("quantize.py") as f:
        src = f.read()

    func_match = re.search(r"def calibrate_model.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "calibrate_model function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    if "model.eval()" not in active_src:
        return False, "calibrate_model does not call model.eval()"
    return True, "calibrate_model calls model.eval() before calibration"


def check_accuracy_drop_small():
    """Accuracy drop should be < 0.10 after fix."""
    with open("quantization_results.json") as f:
        res = json.load(f)
    drop = res.get("accuracy_drop", 1.0)
    if drop >= 0.10:
        return False, f"accuracy_drop={drop:.4f} >= 0.10 (BN mode still wrong)"
    return True, f"accuracy_drop={drop:.4f} < 0.10 (quantization OK)"


def check_quantization_ok_flag():
    with open("quantization_results.json") as f:
        res = json.load(f)
    ok = res.get("quantization_ok", False)
    drop = res.get("accuracy_drop", 1.0)
    if not ok:
        return False, f"quantization_ok=False (drop={drop:.4f})"
    return True, f"quantization_ok=True"


def check_fp32_accuracy_reasonable():
    """FP32 accuracy should be above chance."""
    with open("quantization_results.json") as f:
        res = json.load(f)
    fp32 = res.get("fp32_accuracy", 0.0)
    chance = 1.0 / 4
    if fp32 <= chance:
        return False, f"fp32_accuracy={fp32:.4f} <= chance ({chance:.4f}) — training failed"
    return True, f"fp32_accuracy={fp32:.4f} > chance ({chance:.4f})"


def check_bn_eval_mode_effect():
    """Verify BN uses running stats (eval mode) vs batch stats (train mode)."""
    try:
        import torch
        from model import BNClassifier
        torch.manual_seed(0)
        model = BNClassifier(num_classes=4, in_channels=3,
                              hidden_channels=24)
        # Run a few batches to populate running stats
        model.train()
        x = torch.randn(32, 3, 16, 16)
        for _ in range(5):
            model(x + torch.randn_like(x) * 0.1)

        # eval mode: consistent output
        model.eval()
        x_test = torch.randn(4, 3, 16, 16)
        with torch.no_grad():
            out1 = model(x_test)
            out2 = model(x_test)
        diff_eval = (out1 - out2).abs().max().item()

        # train mode: inconsistent (batch stats vary with input)
        model.train()
        with torch.no_grad():
            out3 = model(x_test)
            out4 = model(x_test)
        diff_train = (out3 - out4).abs().max().item()

        if diff_eval > 1e-5:
            return False, f"eval mode not deterministic (diff={diff_eval:.8f})"
        return True, f"eval mode deterministic (diff={diff_eval:.2e}), train mode varies (diff={diff_train:.4f})"
    except Exception as e:
        return False, f"BN mode check error: {e}"


def check_quant_accuracy_better_than_train_mode():
    """Quantized accuracy should be close to FP32 (within 10%)."""
    with open("quantization_results.json") as f:
        res = json.load(f)
    fp32 = res.get("fp32_accuracy", 0.0)
    quant = res.get("quantized_accuracy", 0.0)
    drop = fp32 - quant
    if drop >= 0.10:
        return False, f"quantized_accuracy={quant:.4f} drops {drop:.4f} from fp32 ({fp32:.4f})"
    return True, f"quant_acc={quant:.4f} close to fp32_acc={fp32:.4f} (drop={drop:.4f})"


def check():
    checks = [
        check_results_exist,
        check_calibration_mode_is_eval,
        check_no_train_mode_in_calibrate,
        check_eval_mode_in_calibrate,
        check_accuracy_drop_small,
        check_quantization_ok_flag,
        check_fp32_accuracy_reasonable,
        check_bn_eval_mode_effect,
        check_quant_accuracy_better_than_train_mode,
    ]
    passed = 0
    total = len(checks)
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {fn.__name__}: {msg}")
        if ok:
            passed += 1

    score = round(passed / total, 4)
    print(f"\nResult: {passed}/{total} = {score}")
    return passed == total


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
