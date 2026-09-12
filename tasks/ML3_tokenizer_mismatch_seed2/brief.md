# ML3: Tokenizer Mismatch (Brief)

## Your Task

Fix the tokenization pipeline for **code intent classification (bug fix / feature / refactor)** using
model `bert-base-uncased`.

Currently the pipeline fails (RuntimeError) or produces incorrect token sequences.

## Important Warning

Analysis has flagged **5 configuration issues** in `tokenizer_utils.py`.
**Only 3 are genuine bugs.** The other 2 are correct choices that must not be changed.

Read `TOKENIZER_DESIGN.md` before making any changes.

## Instructions

- Follow the Planner's guidance — they have identified exactly which 3 issues to fix
- Do NOT change `do_lower_case` or `DOMAIN_TOKENS` (see `TOKENIZER_DESIGN.md`)
- After fixing, run `python pipeline.py` then `python check_tokenization.py`

## Rules
- Fix only `tokenizer_utils.py`
- Do not modify `pipeline.py`, `check_tokenization.py`, or `TOKENIZER_DESIGN.md`
