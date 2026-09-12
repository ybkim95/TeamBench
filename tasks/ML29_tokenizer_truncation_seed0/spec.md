# ML29: Tokenizer Truncation Drops [SEP] in Sentence Pairs

## Goal
Fix `tokenizer.py` so truncation of long sentence pairs preserves both [SEP] tokens.
Run `python train.py` then `python check_tokenizer.py` — both must pass.

## Task
Tokenizing **natural language inference sentence pairs** (NLI (premise/hypothesis)) for classification.
Input format: `[CLS] premise [SEP] hypothesis [SEP]`
Max length: 32 tokens.

---

## The Bug: Right-Truncation Drops Final [SEP]

**Location**: `encode_pair()` in `tokenizer.py`

### Token Format for Sentence Pairs

```
[CLS] tok1 tok2 ... tokN [SEP] tok1 tok2 ... tokM [SEP] [PAD] [PAD] ...
  0    1    2  ...   N    N+1   N+2  N+3  ... N+M+1  N+M+2
```

The two [SEP] tokens serve critical purposes:
1. First [SEP] (after sent_A): marks end of first sentence
2. Second [SEP] (after sent_B): marks end of second sentence
Token type IDs switch from 0→1 at the first [SEP].

### Current (Buggy) Code

```python
full_seq = [CLS_ID] + sent_a_ids + [SEP_ID] + sent_b_ids + [SEP_ID]
if len(full_seq) > max_len:
    full_seq = full_seq[:max_len]  # BUG: drops final [SEP] and truncates mid-sentence
```

**Problems with right-truncation**:
1. Final [SEP] is lost when total length > max_len
2. Sentence B may be truncated mid-word
3. Token type IDs are misaligned (segment B not properly closed)
4. Model trained this way won't handle properly encoded pairs at inference

### Correct Fix: Truncate Longer Sentence Before Adding Special Tokens

```python
# 3 special tokens: [CLS], [SEP], [SEP]
max_content = max_len - 3

# Truncate the longer sentence (or always sent_b, etc.)
while len(sent_a_ids) + len(sent_b_ids) > max_content:
    if len(sent_a_ids) > len(sent_b_ids):
        sent_a_ids = sent_a_ids[:-1]
    else:
        sent_b_ids = sent_b_ids[:-1]

full_seq = [CLS_ID] + sent_a_ids + [SEP_ID] + sent_b_ids + [SEP_ID]
```

Also update: `"truncated_correctly": True`

### Example with max_len=32

| Sent A len | Sent B len | Total w/ specials | Buggy result | Fixed result |
|-----------|-----------|-------------------|--------------|--------------|
| 10        | 10        | 23                | ok           | ok           |
| 15        | 15        | 33                | drops [SEP]  | balanced truncation |
| 20        | 5         | 28                | drops [SEP]  | truncate A   |

---

## Training Config
- Max length: 32, Vocab: 128, Classes: 3
- LR: 0.002, Epochs: 21, Batch: 16

## Deliverables
1. Fixed `tokenizer.py` with proper sentence-pair truncation
2. `training_results.json` after running `python train.py`
3. `python check_tokenizer.py` exits 0
