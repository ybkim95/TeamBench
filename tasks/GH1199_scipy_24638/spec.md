# GH1199_scipy_24638: TST: fix tests for array-api-strict 2.5 / Array API 2025.12 spec — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue
<!--Example: Closes gh-WXYZ.-->

#### What does this implement/fix?
<!--Please explain your changes.-->

Now that Array API 2025.12 revision is a thing, let's see what it takes to use it in SciPy. 

The changes here is what it takes to pass `$ spin test -b array_api_strict` with the [`array-api-strict` release branch ]((withheld: the upstream fix is not part of the task)) locally.

I suspect the CI will fail all around until array-api-strict 2.5 is on PyPI though, since it'll be the first release to recognize the 2025.12 revision of the spec.

#### Additional information
<!--Any additional information you think is important.-->

A general needs-decision item is the support policy: 
- is there something blocking us from bumping to 2025.12 with `array_api_strict` (probably not?)
- are we prepared to handle different backends implementing different revisions (might be a mess for no good reason?)

#### AI Generation Disclosure

No AI tools used

<!-- If AI was used in the preparation of this pull request, please disclose
the tool(s) used, how they were used, and specify what code or text is AI generated.
If no AI tools were used, please write "No AI tools used" in this section. Read our
policy on AI generated code at
https://scipy.github.io/devdocs/dev/conduct/ai_policy.html -->

## PR Review Comments

**[user]** on `scipy/conftest.py`:

Anybody sees a reason not to bump to the latest array-api-strict (to-be-released 2.5 ) and the latest Array API spec (2025.12)?

**[user]** on `scipy/conftest.py`:

no

**[user]** on `scipy/conftest.py`:

CI not happy with this for `array_api_compat.numpy`

**[user]** on `scipy/conftest.py`:

Yup, it needs an `array-api-compat` release, too. 
My plan is to cut a `-strict` release first to break the chicken-and-egg loop of -strict and -tests, then finalize -tests, and then use them for the last mile in -compat. And then we'll see what sort of shenanigans we need here, e.g. for dask and jax :-). Not sure what `-extra` requires beyond a `-compat` release?

**[user]** on `scipy/conftest.py`:

> Not sure what `-extra` requires beyond a `-compat` release?

we shall see!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
