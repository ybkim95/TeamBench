# GH97_arrow_1201: Add FORMAT_RFC3339_STRICT. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/arrow-py/arrow/issues/1138
- Repo: https://github.com/arrow-py/arrow

## Issue Description

<!--
Thanks for taking the time to submit this feature request.

Please provide us with a detailed description of the potential improvement.
-->

## Include "T" separator in the format string for FORMAT_RFC3339

Currently the FORMAT_RFC3339 does not include the "T" separator, but technically it is required.
From https://www.rfc-editor.org/rfc/rfc3339#page-7
> ISO 8601 states that the "T" may be omitted under some circumstances.  This grammar requires the "T" to avoid ambiguity.

I realize that str() already returns the RFC3339 format with the "T".

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

hey [user], str() returns ISO8601 which does have the "T", as per https://github.com/arrow-py/arrow/blob/1.2.3/arrow/arrow.py#L792

in order to not break backwards compatibility of people that might already be using this formatter, I'd say we can add another one, FORMAT_RFC3339_STRICT, to add the "T".

[user] [user] [user] thoughts?

### Comment 2 ([user]):

Chiming in to say this bit us. Expected the T as the most standard string format for datetimes now.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
