# Tokenizer Design Document

This document explains deliberate tokenizer configuration choices that analysis
may flag as suspicious. **Read this before modifying `tokenizer_utils.py`.**

---

## §Case Handling — `do_lower_case = False`

**What analysis flags**: case normalisation setting may appear inconsistent with
the task's text style (documents contain proper nouns, acronyms, etc.).

**Why it is correct**: roberta-base was pre-trained on mixed-case text. Its vocabulary preserves capitalisation: 'The' and 'the' have different token IDs and both exist in the vocabulary. Setting do_lower_case=False is mandatory; changing it to True forces 'The'→'the' which may exist with a different meaning or as [UNK].

**Do not change** `do_lower_case` from `False`.

---

## §Domain Tokens — `DOMAIN_TOKENS = [[CLAUSE], [PARTY], [JURISDICTION], [OBLIGATION]]`

**What analysis flags**: these tokens (`[CLAUSE]`, `[PARTY]`, `[JURISDICTION]`, `[OBLIGATION]`)
are not part of the standard roberta-base vocabulary and may appear as
"unknown tokens that inflate OOV rate".

**Why they are required**: These 4 legal domain tokens mark structural elements of contracts. The fine-tuning task was designed around a vocabulary that includes them; removing them causes the model to mis-segment clause boundaries and reduces classification accuracy by 8-15% on held-out contract sets.

`DOMAIN_TOKENS` must remain in `tokenizer_utils.py`. The pipeline reports
`domain_tokens_count` in `pipeline_results.json`; the grader verifies this field.

---

## Known Real Bugs (NOT documented here)

There are 3 genuine configuration mismatches in `tokenizer_utils.py` that prevent
correct tokenization. Consult the spec for details. The sections above cover only
the **intentional choices** that must be preserved.
