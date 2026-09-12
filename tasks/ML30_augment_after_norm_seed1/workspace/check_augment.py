"""Validate augmentation order fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from augment import train_transform, val_transform, get_pipeline_order, normalize, MEAN, STD


def check_pipeline_order():
    """Verify normalize comes LAST in train_transform."""
    order = get_pipeline_order()
    if not order.endswith("normalize"):
        return False, f"Pipeline order does not end with normalize: {order!r}"
    if order.startswith("normalize"):
        return False, f"Pipeline order starts with normalize (bug): {order!r}"
    return True, f"Pipeline order correct: {order!r}"


def check_source_normalize_last():
    """Verify normalize() is called last in train_transform source."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'augment.py')) as f:
        src = f.read()
    import re
    # Find the train_transform function body
    fn_match = re.search(r'def train_transform.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "Could not find train_transform in augment.py"
    fn_body = fn_match.group(0)

    # normalize call position should be AFTER flip/crop/color
    norm_pos = fn_body.rfind('normalize(')
    flip_pos = fn_body.find('random_horizontal_flip(')
    crop_pos = fn_body.find('random_crop(')
    color_pos = max(fn_body.find('apply_color_jitter('), fn_body.find('apply_brightness('))

    if norm_pos < 0:
        return False, "normalize() not called in train_transform"
    if flip_pos > 0 and norm_pos < flip_pos:
        return False, "normalize() called before random_horizontal_flip()"
    if crop_pos > 0 and norm_pos < crop_pos:
        return False, "normalize() called before random_crop()"
    if color_pos > 0 and norm_pos < color_pos:
        return False, "normalize() called before color augmentation"
    return True, "normalize() is called after all augmentation transforms"


def check_output_range_after_transform():
    """Verify train_transform output has normalized range (not [0,1])."""
    rng = np.random.RandomState(0)
    img = rng.rand(3, 28, 28).astype(np.float32)
    transformed = train_transform(img, rng=rng)
    # After normalization, values should be outside [0, 1]
    in_unit_range = (transformed.min() >= -0.1) and (transformed.max() <= 1.1)
    if in_unit_range:
        return False, f"Output appears to still be in [0,1]: min={transformed.min():.4f}, max={transformed.max():.4f} — normalize may not be applied"
    return True, f"Output range after transform: [{transformed.min():.4f}, {transformed.max():.4f}] — normalized"


def check_val_and_train_use_same_norm():
    """Verify val_transform and train_transform produce same stats on unaugmented images."""
    rng = np.random.RandomState(42)
    img = rng.rand(3, 28, 28).astype(np.float32)

    val_out = val_transform(img.copy())
    # For a non-augmented image, both should apply normalization
    expected = normalize(img.astype(np.float32))
    val_matches_normalize = np.allclose(val_out, expected, atol=1e-5)
    if not val_matches_normalize:
        return False, "val_transform does not match normalize(img)"
    return True, "val_transform correctly applies normalize only"


def check_augment_before_normalize_flag():
    """Verify training_results.json has augment_before_normalize=True."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if not res.get("augment_before_normalize", False):
        return False, "augment_before_normalize=False in training_results.json"
    return True, "augment_before_normalize=True"


def check_color_jitter_on_valid_range():
    """Verify color jitter operates on pre-normalized [0,1] range (not ~[-2,2])."""
    rng = np.random.RandomState(1)
    img = np.ones((3, 28, 28), dtype=np.float32) * 0.5

    # Apply only augmentation (without normalize) to see color_jitter input range
    # We check the source code for the order
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'augment.py')) as f:
        src = f.read()
    import re
    fn_match = re.search(r'def train_transform.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    fn_body = fn_match.group(0) if fn_match else ""

    color_pos = max(fn_body.find('apply_color_jitter('), fn_body.find('apply_brightness('))
    norm_pos = fn_body.rfind('normalize(')

    if color_pos > 0 and norm_pos > 0 and color_pos > norm_pos:
        return False, "Color augmentation called AFTER normalize — bug not fixed"
    return True, "Color augmentation called before normalize — correct order"


def check_no_double_normalize():
    """Verify normalize is called exactly once in train_transform."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'augment.py')) as f:
        src = f.read()
    import re
    fn_match = re.search(r'def train_transform.*?(?=^def |\Z)', src, re.DOTALL | re.MULTILINE)
    if not fn_match:
        return False, "train_transform not found"
    fn_body = fn_match.group(0)
    count = fn_body.count('normalize(')
    if count != 1:
        return False, f"normalize() called {count} times in train_transform (expected 1)"
    return True, "normalize() called exactly once"


def check_deterministic_with_rng():
    """Verify train_transform is deterministic given same rng seed."""
    img = np.random.RandomState(0).rand(3, 28, 28).astype(np.float32)
    out1 = train_transform(img.copy(), rng=np.random.RandomState(5))
    out2 = train_transform(img.copy(), rng=np.random.RandomState(5))
    if not np.allclose(out1, out2):
        return False, "train_transform not deterministic with same rng seed"
    return True, "train_transform is deterministic"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    order = res.get("pipeline_order", "unknown")
    print(f"Final val acc: {acc:.4f}, pipeline order: {order}")

    checks = [
        check_pipeline_order,
        check_source_normalize_last,
        check_output_range_after_transform,
        check_val_and_train_use_same_norm,
        check_augment_before_normalize_flag,
        check_color_jitter_on_valid_range,
        check_no_double_normalize,
        check_deterministic_with_rng,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (val_acc={acc:.4f} < 0.40)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
