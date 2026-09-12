# ML3: Tokenizer Mismatch — Code Intent Classification (Bug Fix / Feature / Refactor)

The tokenization pipeline has 5 flagged configuration issues.
**Only 3 are genuine mismatches.**

## Important

Read `TOKENIZER_DESIGN.md` before making any changes. It documents 2 configuration
choices that look suspicious but are correct and must not be modified.

## Workflow

1. Read `TOKENIZER_DESIGN.md` (documents intentional choices)
2. Get the Planner's guidance (they have the spec)
3. Fix only the 3 real mismatches in `tokenizer_utils.py`
4. Run `python pipeline.py` then `python check_tokenization.py`

Model: `bert-base-uncased` | Task: `code commit intent classification`
