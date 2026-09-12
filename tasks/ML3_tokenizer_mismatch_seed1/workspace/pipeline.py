"""NLP pipeline for legal document clause classification.

Runs tokenization and reports validity of each encoded sequence.
"""
import json
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tokenizer_utils import batch_encode, VOCAB_SIZE, MAX_LENGTH, SPECIAL_TOKENS, DOMAIN_TOKENS

random.seed(42)
SIMULATED_VOCAB = {f"token_{i}": i for i in range(VOCAB_SIZE)}
SIMULATED_VOCAB.update({"the": 1, "a": 2, "is": 3, "in": 4, "of": 5})

LABELS   = ["liability", "indemnity", "ip_rights", "termination", "other"]
N_CLASSES = 5

SAMPLE_TEXTS = [
    "The patient was administered 500mg amoxicillin twice daily for seven days.",
    "Diagnosis confirmed: Type 2 diabetes mellitus with peripheral neuropathy.",
    "Lab results indicate elevated ALT and AST consistent with hepatic involvement.",
]


def run_pipeline():
    """Tokenize sample texts and report validity."""
    try:
        encoded = batch_encode(SAMPLE_TEXTS, SIMULATED_VOCAB)
    except RuntimeError as e:
        print(f"Pipeline error: {e}")
        output = {
            "error": str(e),
            "vocab_size_used":      VOCAB_SIZE,
            "max_length_used":      MAX_LENGTH,
            "special_tokens_defined": bool(SPECIAL_TOKENS),
            "domain_tokens_count":  len(DOMAIN_TOKENS),
            "n_valid": 0,
            "n_texts": len(SAMPLE_TEXTS),
        }
        with open("pipeline_results.json", "w") as f:
            json.dump(output, f, indent=2)
        return False

    input_ids      = encoded["input_ids"]
    attn_masks     = encoded["attention_mask"]
    domain_active  = encoded.get("domain_tokens_active", 0)

    results = []
    for i, (ids, mask) in enumerate(zip(input_ids, attn_masks)):
        length_ok  = len(ids) == MAX_LENGTH
        has_cls    = ids[0] == SPECIAL_TOKENS.get("cls_token_id", -1)
        has_sep    = SPECIAL_TOKENS.get("sep_token_id", -1) in ids
        unk_count  = sum(1 for x in ids if x == SPECIAL_TOKENS.get("unk_token_id", -999))
        unk_rate   = unk_count / max(len(ids), 1)
        results.append({
            "text":       SAMPLE_TEXTS[i],
            "n_tokens":   len(ids),
            "length_ok":  length_ok,
            "has_cls":    has_cls,
            "has_sep":    has_sep,
            "unk_rate":   unk_rate,
            "valid":      length_ok and has_cls and has_sep and unk_rate < 0.5,
        })

    n_valid = sum(1 for r in results if r["valid"])
    output  = {
        "vocab_size_used":       VOCAB_SIZE,
        "max_length_used":       MAX_LENGTH,
        "special_tokens_defined": bool(SPECIAL_TOKENS),
        "domain_tokens_count":   domain_active,
        "n_texts":               len(results),
        "n_valid":               n_valid,
        "results":               results,
    }
    with open("pipeline_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Valid tokenizations: {n_valid}/{len(results)}")
    for r in results:
        status = "OK" if r["valid"] else "FAIL"
        print(f"  [{status}] len={r['n_tokens']} unk={r['unk_rate']:.2f} cls={r['has_cls']} sep={r['has_sep']}")
    return n_valid == len(results)


if __name__ == "__main__":
    ok = run_pipeline()
    sys.exit(0 if ok else 1)
