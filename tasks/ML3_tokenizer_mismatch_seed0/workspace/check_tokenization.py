"""Check tokenization correctness and design choice preservation."""
import json
import sys
import os


def check():
    if not os.path.exists("pipeline_results.json"):
        print("ERROR: pipeline_results.json not found. Run pipeline.py first.")
        return False

    with open("pipeline_results.json") as f:
        r = json.load(f)

    if "error" in r:
        print(f"ERROR: pipeline failed — {r['error']}")
        return False

    checks = []

    # Real bug 1: vocab size must match model
    actual_vocab = r.get("vocab_size_used", 0)
    checks.append(("vocab_size_correct",
                   actual_vocab == 30522,
                   f"vocab_size={actual_vocab}, expected 30522"))

    # Real bug 2: max_length must match model
    actual_max = r.get("max_length_used", 0)
    checks.append(("max_length_correct",
                   actual_max == 128,
                   f"max_length={actual_max}, expected 128"))

    # Real bug 3: special tokens must be defined
    checks.append(("special_tokens_defined",
                   r.get("special_tokens_defined", False),
                   "SPECIAL_TOKENS dict is empty — CLS/SEP/PAD/UNK must be set"))

    # All tokenizations valid
    n_valid = r.get("n_valid", 0)
    n_total = r.get("n_texts", 1)
    checks.append(("all_tokenizations_valid",
                   n_valid == n_total,
                   f"only {n_valid}/{n_total} tokenizations valid"))

    # Intentional design: domain tokens must be preserved
    domain_count = r.get("domain_tokens_count", 0)
    checks.append(("domain_tokens_preserved",
                   domain_count == 5,
                   f"domain_tokens_count={domain_count}, expected 5 "
                   "(removing domain tokens is an over-fix — see TOKENIZER_DESIGN.md)"))

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
