# Verifier decision codebook

Coding scheme for the free-text notes attached to human Verifier verdicts in the
TeamBench human study, restricted to decisions where the deterministic grader had
already returned **fail** and its verdict, score and full output were displayed on
the participant's screen at the moment they decided.

Unit of analysis: **one verdict submission** (`decision_uid`). A session can
contribute several, because a `fail` verdict sends the Executor back and the
Verifier decides again. Sequence context is provided and is part of the coding.

Population: 24 decisions (12 human `pass`, 12 human `fail`).

## How to code

1. Read `note`, then the sequence columns (`position_in_session`,
   `prior_fail_in_session`, `score_unchanged_since_prior`).
2. Assign **exactly one** code. Codes are mutually exclusive and are tested in
   the order listed below; the first that applies wins.
3. Record `code_confidence` as `high` / `low`. Use `low` when the note is short
   enough that two readings are defensible.
4. Put anything the scheme fails to capture in `coder_notes`. Do not invent codes.

Code the note **as written**. Do not infer intent beyond what the text and the
sequence columns support. In particular, do not treat a terse note as evidence of
carelessness unless the sequence columns show it.

## Codes for human `pass` on grader `fail` (false accept)

### C1 — capitulation
The same session already contains an earlier `fail` verdict from this Verifier,
the grader score is unchanged since that earlier verdict, and the Verifier now
passes. The defect was identified and then approved without improvement.

> Decisive columns: `prior_fail_in_session = True` **and**
> `score_unchanged_since_prior = True`.
> C1 takes precedence over every other code, including when the note itself is
> purely social, because the sequence is the stronger evidence.

Example: `"Thanks!! It looks good!!"` submitted 4.9 minutes after the same
Verifier had enumerated four unmet requirements on the same artifact.

### C2 — explicit non-verification
The note states that the Verifier could not or did not check something, and the
verdict is `pass` anyway.

Example: `"I can't see the new test file that the executor has created, but
changes in the mathutils.py file look good."`

### C3 — discretionary waiver
The note grants a pass while signalling awareness that the bar was not met.
Markers: "this time", "let's call it done", deferring to another person's opinion.

Example: `"pass this time."`, `"admin3 (verifier) thinks the case is done."`

### C4 — social approval only
The note contains praise or thanks and no verification content, and C1 does not
apply (no prior fail, or the score changed).

Example: `"Good job!!"`

### C5 — non-serious
The note is not interpretable as a judgement of the work.

Example: `"hahahahha"`

### C6 — no note
`note` is empty.

## Codes for human `fail` on grader `fail` (correct reject)

### R1 — grader evidence cited
The note quotes or paraphrases the deterministic grader's output, e.g. pasting
`failure_modes`.

### R2 — independently enumerated defects
The note names specific defects the Verifier located itself, typically with file
or line references, going beyond what the grader printed.

### R3 — terse rejection
A rejection with a direction but no specifics.

Example: `"Need to other tests"`

### R4 — no note
`note` is empty.

## Boundary cases already encountered

| Situation | Code | Why |
|---|---|---|
| Note is a verbatim copy of the earlier fail note, verdict flipped to pass | C1 | Sequence dominates; the text is stale |
| `"fail haha."` then `"pass this time."` 0.4 min later, score unchanged | C1 | Prior fail plus unchanged score |
| Praise, but it is the first verdict in the session | C4 | C1 requires a prior fail |
| Rejection quoting the grader **and** adding line numbers | R2 | R2 is the stronger claim; it subsumes R1 |
| Two identical verdicts submitted 0.0 min apart | code both | Duplicate submissions are kept; deduplicate at analysis, not at coding |

## Reporting

Because a session contributes multiple decisions, report counts at both levels:
decision level (n=24) and session level (n=13). Session-level is the conservative
denominator and should lead.

Agreement: two independent coders, disagreements resolved by discussion, Cohen's
kappa reported on the first pass before resolution. Compute with
`python scripts/coding_agreement.py`.

## Threats to validity

- n = 24 decisions across 13 sessions. Codes with fewer than 3 instances are
  descriptive only.
- The "capitulation" reading is inferred from behaviour, not from participant
  self-report. No post-task interview asked why a verdict was reversed. The
  claim the data supports is that the reversal happened with the defect
  unchanged, not that any particular motive caused it.
- Coder 1 developed the scheme after reading the notes, so the codebook is not
  independent of this sample. Coder 2 should code without reading Coder 1's
  assignments, and any code added during coding invalidates the kappa.
- Participants include project co-authors, who are not naive to the task set or
  to the study's purpose.
