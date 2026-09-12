# GH1059_spaCy_13400: Fix use_gold_ents behaviour for EntityLinker — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

## Description
The `use_gold_ents` flag was [introduced]((withheld: the upstream fix is not part of the task)) to allow the `entity_linker` to train on gold entities, even if there's no (annotating) NER component in the pipeline.

I think this behaviour was buggy because of a few reasons:
1. In `initialize()`, NER "predictions" from `eg.reference` were added to `eg.predicted` for the first 10 examples, and never cleaned up/restored afterwards.
2. In `update()`, this transfer happened on all examples, but here the ents were "restored" before calling the loss function. In theory, this should have prevented the EL to learn anything at all, except that in the corresponding unit test, this bug got masked by bug 1, which resulted in a few spurious annotations on the first 10 documents
3.  Because of how a spaCy pipeline works internally, the scoring could never work out of the box, because `Language.evaluate()` calls `pipe()` on the predicted docs, which won't have entities if there is no (annotating) NER in the pipeline.

To test some of this behaviour, I used different configs with the EL Emerson example, cf (withheld: the upstream fix is not part of the task). The "EL only" config would produce all-zero lines with `master`:
```
E    #       LOSS ENTIT...  NEL_MICRO_F  NEL_MICRO_R  NEL_MICRO_P  SCORE
---  ------  -------------  -----------  -----------  -----------  ------
  0       0           0.00         0.00         0.00         0.00    0.00
 33     200           0.00         0.00         0.00         0.00    0.00
 73     400           0.00         0.00         0.00         0.00    0.00
123     600           0.00         0.00         0.00         0.00    0.00
```

Then it would produce actual loss scores after fixing 1 and 2:
```
E    #       LOSS ENTIT...  NEL_MICRO_F  NEL_MICRO_R  NEL_MICRO_P  SCORE
---  ------  -------------  -----------  -----------  -----------  ------
  0       0           3.30         0.00         0.00         0.00    0.00
 33     200          55.77         0.00         0.00         0.00    0.00
 73     400           3.93         0.00         0.00         0.00    0.00
123     600           1.99         0.00         0.00         0.00    0.00
```

And finally, after fixing 3, it would give actual scores:
```
E    #       LOSS ENTIT...  NEL_MICRO_F  NEL_MICRO_R  NEL_MICRO_P  SCORE
---  ------  -------------  -----------  -----------  -----------  ------
  0       0           3.30        33.33        33.33        33.33    0.33
 33     200          57.55        83.33        83.33        83.33    0.83
 74     400           4.25        83.33        83.33        83.33    0.83
124     600           1.95        83.33        83.33        83.33    0.83

```

### Types of change
bug fixes & enhancement

## Checklist
- [x] I confirm that I have the right to submit this contribution under the project's MIT license.
- [x] I ran the tests, and all new and existing tests passed.
- [x] My changes don't require a change to the documentation, or if they do, I've added all required information.

## PR Review Comments

**[user]** on `spacy/pipeline/entity_linker.py`:

This whole bit is surely pretty hacky, but considering bug 3 as explained in the PR, I don't see a better option other than changing the entire mechanism how evaluation/scoring of a pipeline works...

**[user]** on `spacy/pipeline/entity_linker.py`:

Making a copy here feels safest? Not 100% about all the possible interactions with all other components in the pipeline, before or after, annotated or not, and frozen or not...

**[user]** on `spacy/pipeline/entity_linker.py`:

```suggestion
        def _score_augmented(examples: Iterable[Example], **kwargs):
```

**[user]** on `spacy/pipeline/entity_linker.py`:

Agreed, this is not really satisfying. The workaround makes sense in this context though.

**[user]** on `spacy/pipeline/entity_linker.py`:

Hm, do we manipulate examples in other components? I'm also unsure about this. Either way :+1: for copying it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
