"""Tokenizer utilities for code commit intent classification.

Analysis may flag 5 issues. Read TOKENIZER_DESIGN.md before fixing anything.
Not all flagged items are bugs.
"""
from typing import List, Dict

# ISSUE 1 (real bug): Wrong vocabulary size — does not match bert-base-uncased
VOCAB_SIZE = 1000  # Should be 30522

# ISSUE 2 (real bug): Wrong max sequence length
MAX_LENGTH = 32  # bert-base-uncased max is 128

# ISSUE 3 (real bug): Missing special tokens
SPECIAL_TOKENS: Dict[str, int] = {}  # Must define CLS/SEP/PAD/UNK token IDs

# ISSUE 4 (intentional): case handling — see TOKENIZER_DESIGN.md §Case Handling
do_lower_case = True  # Correct: bert-base-uncased requires lowercase

# ISSUE 5 (intentional): domain-specific tokens — see TOKENIZER_DESIGN.md §Domain Tokens
DOMAIN_TOKENS: List[str] = ["[COMMIT]", "[DIFF]", "[FUNC]", "[MODULE]", "[TEST]"]


def simple_tokenize(text: str) -> List[str]:
    """Whitespace tokenizer with correct case handling for bert-base-uncased."""
    if do_lower_case:
        text = text.lower()
    tokens = text.split()
    # Preserve domain tokens in their original form even after case normalisation
    return tokens


def encode(text: str, vocab_map: Dict[str, int]) -> List[int]:
    """Encode text to token IDs."""
    if not SPECIAL_TOKENS:
        raise RuntimeError(
            "SPECIAL_TOKENS not configured. Set cls_token_id, sep_token_id, "
            "pad_token_id, unk_token_id before encoding."
        )
    unk_id = SPECIAL_TOKENS["unk_token_id"]
    cls_id = SPECIAL_TOKENS["cls_token_id"]
    sep_id = SPECIAL_TOKENS["sep_token_id"]
    pad_id = SPECIAL_TOKENS["pad_token_id"]

    tokens = simple_tokenize(text)
    ids = [vocab_map.get(t, unk_id) for t in tokens]
    # Truncate preserving room for [CLS] + [SEP]
    ids = ids[:MAX_LENGTH - 2]
    ids = [cls_id] + ids + [sep_id]
    # Pad to MAX_LENGTH
    ids = ids + [pad_id] * (MAX_LENGTH - len(ids))
    return ids


def batch_encode(texts: List[str], vocab_map: Dict[str, int]) -> Dict[str, List]:
    """Batch encode a list of texts."""
    all_ids = [encode(t, vocab_map) for t in texts]
    attention_masks = [
        [1 if tok_id != SPECIAL_TOKENS.get("pad_token_id", 0) else 0 for tok_id in ids]
        for ids in all_ids
    ]
    return {
        "input_ids":      all_ids,
        "attention_mask": attention_masks,
        "domain_tokens_active": len(DOMAIN_TOKENS),
    }
