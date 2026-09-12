"""Sentence-pair tokenizer — contains truncation bug that drops [SEP]."""
import numpy as np

# Special token IDs
CLS_ID = 0
SEP_ID = 1
PAD_ID = 2
# Regular vocab: IDs 3..149

MAX_LEN = 40
VOCAB_SIZE = 150


def tokenize(text_ids: list) -> list:
    """Convert a list of token IDs (already pre-tokenized for simplicity)."""
    return list(text_ids)


def encode_pair(sent_a_ids: list, sent_b_ids: list,
                max_len: int = MAX_LEN) -> dict:
    """
    Encode a sentence pair into model input format.

    Format: [CLS] sent_A [SEP] sent_B [SEP] + padding

    BUG: Right-truncation is applied to the FULL sequence after concatenation.
    When the combined sequence exceeds max_len, the tail (including the final
    [SEP] and possibly part of sent_B) is cut off.

    Correct: Truncate the LONGER sentence before adding special tokens,
    ensuring both [SEP] tokens are always present.
    """
    # Build full sequence with special tokens
    full_seq = [CLS_ID] + sent_a_ids + [SEP_ID] + sent_b_ids + [SEP_ID]

    # BUG: naive right-truncation — may cut off the final [SEP]
    if len(full_seq) > max_len:
        full_seq = full_seq[:max_len]  # BUG: drops trailing [SEP] on long pairs

    # Pad to max_len
    pad_len = max_len - len(full_seq)
    input_ids = full_seq + [PAD_ID] * pad_len
    attention_mask = [1] * len(full_seq) + [0] * pad_len

    # Token type IDs: 0 for [CLS]+sent_A+[SEP], 1 for sent_B+[SEP]
    # BUG: this is also wrong when [SEP] is missing (boundary is off)
    sep_pos = next((i for i, t in enumerate(input_ids) if t == SEP_ID), len(full_seq))
    token_type_ids = [0] * (sep_pos + 1) + [1] * (max_len - sep_pos - 1)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
        "has_both_sep": input_ids.count(SEP_ID) == 2,  # BUG: often False
        "truncated_correctly": False,  # BUG: should be True after fix
    }


def batch_encode_pairs(pairs: list, max_len: int = MAX_LEN) -> dict:
    """Encode a batch of sentence pairs."""
    encoded = [encode_pair(a, b, max_len) for a, b in pairs]
    import numpy as np
    return {
        "input_ids": np.array([e["input_ids"] for e in encoded], dtype=np.int64),
        "attention_mask": np.array([e["attention_mask"] for e in encoded], dtype=np.int64),
        "token_type_ids": np.array([e["token_type_ids"] for e in encoded], dtype=np.int64),
        "has_both_sep": [e["has_both_sep"] for e in encoded],
        "truncated_correctly": all(e["truncated_correctly"] for e in encoded),
    }
