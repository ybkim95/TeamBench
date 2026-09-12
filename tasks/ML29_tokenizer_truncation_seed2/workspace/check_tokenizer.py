"""Validate tokenizer truncation fix."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tokenizer import encode_pair, batch_encode_pairs, CLS_ID, SEP_ID, PAD_ID, MAX_LEN


def check_both_sep_always_present():
    """Verify both [SEP] tokens appear in long sentence pairs after truncation."""
    # Create a pair that MUST be truncated (way longer than max_len)
    long_a = list(range(3, 3 + MAX_LEN))
    long_b = list(range(3, 3 + MAX_LEN))
    result = encode_pair(long_a, long_b, max_len=MAX_LEN)

    sep_count = result["input_ids"].count(SEP_ID)
    if sep_count != 2:
        return False, f"Long pair has {sep_count} [SEP] tokens (expected 2) — truncation drops [SEP]"
    return True, f"Both [SEP] tokens present in truncated pair"


def check_cls_first():
    """Verify [CLS] is always the first token."""
    for l_a in [5, 15, 25]:
        for l_b in [5, 15, 25]:
            sent_a = list(range(3, 3 + l_a))
            sent_b = list(range(3, 3 + l_b))
            result = encode_pair(sent_a, sent_b, max_len=MAX_LEN)
            if result["input_ids"][0] != CLS_ID:
                return False, f"First token is not [CLS] (l_a={l_a}, l_b={l_b})"
    return True, "[CLS] always first token"


def check_length_not_exceeded():
    """Verify output never exceeds max_len."""
    import numpy as np
    rng = np.random.RandomState(0)
    for _ in range(20):
        l_a = rng.randint(5, MAX_LEN)
        l_b = rng.randint(5, MAX_LEN)
        sent_a = rng.randint(3, 150, size=l_a).tolist()
        sent_b = rng.randint(3, 150, size=l_b).tolist()
        result = encode_pair(sent_a, sent_b, max_len=MAX_LEN)
        if len(result["input_ids"]) != MAX_LEN:
            return False, f"Output length {len(result['input_ids'])} != MAX_LEN={MAX_LEN}"
    return True, f"All outputs have length MAX_LEN={MAX_LEN}"


def check_truncated_correctly_flag():
    """Verify encode_pair returns truncated_correctly=True."""
    long_a = list(range(3, 3 + MAX_LEN))
    long_b = list(range(3, 3 + MAX_LEN))
    result = encode_pair(long_a, long_b, max_len=MAX_LEN)
    if not result.get("truncated_correctly", False):
        return False, "truncated_correctly is False"
    return True, "truncated_correctly=True"


def check_sep_preserved_in_batch():
    """Verify all pairs in batch have both [SEP] tokens."""
    import numpy as np
    rng = np.random.RandomState(1)
    pairs = []
    for _ in range(50):
        l_a = rng.randint(10, MAX_LEN)
        l_b = rng.randint(10, MAX_LEN)
        a = rng.randint(3, 150, size=l_a).tolist()
        b = rng.randint(3, 150, size=l_b).tolist()
        pairs.append((a, b))
    enc = batch_encode_pairs(pairs, max_len=MAX_LEN)
    sep_ok = sum(1 for h in enc["has_both_sep"] if h)
    rate = sep_ok / len(pairs)
    if rate < 0.99:
        return False, f"Only {sep_ok}/{len(pairs)} pairs have both [SEP] tokens ({rate:.1%})"
    return True, f"{sep_ok}/{len(pairs)} pairs have both [SEP] tokens"


def check_token_type_ids_correct():
    """Verify token_type_ids are 0 for sent_A region and 1 for sent_B region."""
    sent_a = list(range(3, 8))    # 5 tokens
    sent_b = list(range(8, 13))   # 5 tokens
    result = encode_pair(sent_a, sent_b, max_len=MAX_LEN)
    ids = result["input_ids"]
    types = result["token_type_ids"]

    # Find the separator positions
    sep_positions = [i for i, t in enumerate(ids) if t == SEP_ID]
    if len(sep_positions) < 2:
        return False, f"Only {len(sep_positions)} [SEP] found — can't verify token types"

    first_sep = sep_positions[0]
    second_sep = sep_positions[1]

    # Types 0..first_sep should be 0
    if any(types[i] != 0 for i in range(first_sep + 1)):
        return False, "Token types not 0 for [CLS]+sent_A+[SEP] region"
    # Types after first_sep should be 1
    if any(types[i] != 1 for i in range(first_sep + 1, second_sep + 1)):
        return False, "Token types not 1 for sent_B+[SEP] region"
    return True, "Token type IDs correct"


def check_source_no_naive_truncation():
    """Verify tokenizer.py does not use naive right-truncation."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokenizer.py')) as f:
        src = f.read()
    # The buggy pattern: full_seq[:max_len] where full_seq already contains [SEP]
    import re
    if re.search(r'full_seq\s*=\s*full_seq\[:max_len\]', src):
        return False, "Naive right-truncation full_seq[:max_len] still present"
    if re.search(r'tokens\s*=\s*tokens\[:max_len\]', src):
        return False, "Naive right-truncation tokens[:max_len] still present"
    return True, "Naive right-truncation pattern not found"


def check_truncation_preserves_content():
    """Verify non-truncated pairs are unchanged."""
    short_a = [3, 4, 5]
    short_b = [6, 7, 8]
    result = encode_pair(short_a, short_b, max_len=MAX_LEN)
    expected_ids = [CLS_ID] + short_a + [SEP_ID] + short_b + [SEP_ID]
    actual_ids = result["input_ids"][:len(expected_ids)]
    if actual_ids != expected_ids:
        return False, f"Short pair encoding changed: {actual_ids} != {expected_ids}"
    return True, "Short (non-truncated) pairs preserved"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    sep_rate = res.get("sep_present_rate", 0)
    print(f"Final val acc: {acc:.4f}, SEP present rate: {sep_rate:.4f}")

    checks = [
        check_both_sep_always_present,
        check_cls_first,
        check_length_not_exceeded,
        check_truncated_correctly_flag,
        check_sep_preserved_in_batch,
        check_token_type_ids_correct,
        check_source_no_naive_truncation,
        check_truncation_preserves_content,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if sep_rate < 0.99:
        print(f"FAIL: [SEP] present in only {sep_rate:.1%} of pairs (expected >99%)")
        all_pass = False

    if not res.get("truncated_correctly", False):
        print("FAIL: truncated_correctly flag is False")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
