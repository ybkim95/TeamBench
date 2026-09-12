# Tokenizer Design Document

This document explains deliberate tokenizer configuration choices that analysis
may flag as suspicious. **Read this before modifying `tokenizer_utils.py`.**

---

## §Case Handling — `do_lower_case = True`

**What analysis flags**: case normalisation setting may appear inconsistent with
the task's text style (documents contain proper nouns, acronyms, etc.).

**Why it is correct**: bert-base-uncased was pre-trained on lowercase text. Its vocabulary maps 'The', 'THE', and 'the' all to the same [UNK] token for the first two. Setting do_lower_case=True is mandatory for this model; changing it to False will cause most capitalised tokens to become [UNK] and destroy representations.

**Do not change** `do_lower_case` from `True`.

---

## §Domain Tokens — `DOMAIN_TOKENS = [[DRUG], [DISEASE], [DOSAGE], [LAB], [PROC]]`

**What analysis flags**: these tokens (`[DRUG]`, `[DISEASE]`, `[DOSAGE]`, `[LAB]`, `[PROC]`)
are not part of the standard bert-base-uncased vocabulary and may appear as
"unknown tokens that inflate OOV rate".

**Why they are required**: These 5 clinical entity tokens are inserted into the vocabulary for the fine-tuning task. They allow the model to emit domain-specific entity boundaries without consuming multiple sub-word tokens for each label type. Removing them forces the model to use generic [UNK] boundaries, degrading NER F1 by ~12 points on the clinical benchmark.

`DOMAIN_TOKENS` must remain in `tokenizer_utils.py`. The pipeline reports
`domain_tokens_count` in `pipeline_results.json`; the grader verifies this field.

---

## Known Real Bugs (NOT documented here)

There are 3 genuine configuration mismatches in `tokenizer_utils.py` that prevent
correct tokenization. Consult the spec for details. The sections above cover only
the **intentional choices** that must be preserved.
