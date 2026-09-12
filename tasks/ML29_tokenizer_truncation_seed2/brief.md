# ML29: Tokenizer Truncation Drops [SEP] (Brief)

## Your Task
Fix the tokenizer in `tokenizer.py`.

Encoding **question-answer passage pairs** uses right-truncation that drops
the final [SEP] token for long sentence pairs. The [SEP] between
question and passage is essential for correct
sentence-pair encoding.

## What to Fix
- `tokenizer.py`: `encode_pair()` — truncate the longer sentence BEFORE
  adding special tokens, so [CLS]...[SEP]...[SEP] is always preserved
- Set `"truncated_correctly": True` in the returned dict
- Do NOT modify `train.py`

## Success Criteria
- `python check_tokenizer.py` exits 0
- Both [SEP] tokens present in all encoded pairs
