# GH1093_spaCy_8012: Ensemble textcat with listener — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

## Description
Stumbled upon a very specific issue thanks to https://github.com/explosion/spaCy/discussions/7651. If the `TextCatEnsemble` architecture is used, in combination with a `Tok2VecListener`, AND there's another component further down the pipeline also using a `Tok2VecListener`, then, and only then, we'll get a crash in Thinc's `concatenate` layer:
```
  File "/home/user/.virtualenvs/spacy-experiments/lib/python3.8/site-packages/thinc/layers/concatenate.py", line 68, in backprop
    dX += bwd(dY)
TypeError: 'NoneType' object is not iterable
```
This happens because the ensemble textcat architecture is the only one that `concatenate`'s (and backpropagates) results of a `Tok2VecListener`. All other architectures simply use `chain`. And all this works if there is just one listener. But when there are multiple, only the last one runs the `backprop` call, and all the others run `accumulate_gradient`, which doesn't return any gradient (https://github.com/explosion/spaCy/blob/master/spacy/pipeline/tok2vec.py).

This fixes the issue by returning an array of zeros instead of `None` in `accumulate_gradient`.

### Types of change
bug fix + regression test

## Checklist
- [x] I have submitted the spaCy Contributor Agreement.
- [x] I ran the tests locally, and all new and existing tests passed.
- [x] My changes don't require a change to the documentation, or if they do, I've added all required information.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
