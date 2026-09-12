# ML3: Tokenizer Mismatch — Selective Fix

## Situation

`tokenizer_utils.py` has **5 flagged configuration issues**.
`TOKENIZER_DESIGN.md` documents 2 as intentional choices.
This spec identifies the **3 genuine bugs** that must be fixed.

**Critical**: `do_lower_case` and `DOMAIN_TOKENS` must not be changed.

---

## Real Bug 1: Wrong Vocabulary Size

**Current (buggy)**:
```python
VOCAB_SIZE = 5000
```

**Correct**:
```python
VOCAB_SIZE = 32000
```

**Reason**: `roberta-base` has a fixed embedding matrix of exactly
32000 entries. Any token ID ≥ 32000 causes an
index-out-of-bounds error in the embedding lookup. With VOCAB_SIZE=5000
the simulated vocabulary maps most tokens to IDs in the wrong range.

---

## Real Bug 2: Wrong Max Sequence Length

**Current (buggy)**:
```python
MAX_LENGTH = 32
```

**Correct**:
```python
MAX_LENGTH = 256
```

**Reason**: `roberta-base` has positional embeddings defined for exactly
256 positions. Truncating to 32 wastes model capacity and discards context.

---

## Real Bug 3: Missing Special Token Configuration

**Current (buggy)**:
```python
SPECIAL_TOKENS: Dict[str, int] = {}  # Empty!
```

**Correct**:
```python
SPECIAL_TOKENS = {
    "cls_token_id": 0,
    "sep_token_id": 2,
    "pad_token_id": 1,
    "unk_token_id": 3,
}
```

Without SPECIAL_TOKENS the `encode()` function raises `RuntimeError` and the
pipeline fails entirely. Every sequence must begin with token 0
([CLS]) and end with token 2 ([SEP]).

---

## Intentional Choices (DO NOT CHANGE)

| Choice | Value | Why Intentional |
|--------|-------|-----------------|
| `do_lower_case` | `False` | Matches roberta-base pre-training regime |
| `DOMAIN_TOKENS` | `["[CLAUSE]", "[PARTY]", "[JURISDICTION]", "[OBLIGATION]"]` | Required for legal clause classification — see TOKENIZER_DESIGN.md |

The check validates `domain_tokens_count == 4` in results.
Removing domain tokens causes this check to fail.

---

## Deliverables
1. Fixed `tokenizer_utils.py`: VOCAB_SIZE, MAX_LENGTH, SPECIAL_TOKENS corrected;
   `do_lower_case` and `DOMAIN_TOKENS` unchanged
2. `pipeline_results.json` with `n_valid == n_texts`
3. `check_tokenization.py` exits 0
