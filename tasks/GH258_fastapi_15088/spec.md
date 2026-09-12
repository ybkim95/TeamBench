# GH258_fastapi_15088: 🔨 Exclude spam comments from statistics in `scripts/people.py` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/fastapi/fastapi

## PR Description

Currently, even if we block user due to spam and all their comments are minimized, this person will still appear in the FastAPI People statistics.

I suggest we don't count comments minimized with reasons "abuse", "off-topic", "duplicate", and "spam".

I ran script locally with and without this filter:
* Without: [before.YML](https://github.com/user-attachments/files/25870295/before.YML)
* With filter: [after.YML](https://github.com/user-attachments/files/25870284/after.YML)

<details><summary>List of skipped comments:</summary>

https://github.com/fastapi/fastapi/discussions/15065#discussioncomment-16046066
https://github.com/fastapi/fastapi/discussions/15059#discussioncomment-16010875
https://github.com/fastapi/fastapi/discussions/15021#discussioncomment-16010895
https://github.com/fastapi/fastapi/discussions/15047#discussioncomment-16010881
https://github.com/fastapi/fastapi/discussions/14890#discussioncomment-15879327
https://github.com/fastapi/fastapi/discussions/14350#discussioncomment-15052306
https://github.com/fastapi/fastapi/discussions/14755#discussioncomment-15879326
https://github.com/fastapi/fastapi/discussions/14893#discussioncomment-15795930
https://github.com/fastapi/fastapi/discussions/14893#discussioncomment-15879334
https://github.com/fastapi/fastapi/discussions/14651#discussioncomment-15421025
https://github.com/fastapi/fastapi/discussions/14513#discussioncomment-15241367
https://github.com/fastapi/fastapi/discussions/14513#discussioncomment-15241368
https://github.com/fastapi/fastapi/discussions/14513#discussioncomment-15241369
https://github.com/fastapi/fastapi/discussions/14513#discussioncomment-15241370
https://github.com/fastapi/fastapi/discussions/14513#discussioncomment-15241371
https://github.com/fastapi/fastapi/discussions/14464#discussioncomment-15208120
https://github.com/fastapi/fastapi/discussions/14377#discussioncomment-15052301
https://github.com/fastapi/fastapi/discussions/14394#discussioncomment-15052875
https://github.com/fastapi/fastapi/discussions/14376#discussioncomment-15052531
https://github.com/fastapi/fastapi/discussions/14390#discussioncomment-15052651
https://github.com/fastapi/fastapi/discussions/14396#discussioncomment-15052941
https://github.com/fastapi/fastapi/discussions/14395#discussioncomment-15052915
https://github.com/fastapi/fastapi/discussions/14393#discussioncomment-15052845
https://github.com/fastapi/fastapi/discussions/14392#discussioncomment-15052775
https://github.com/fastapi/fastapi/discussions/14391#discussioncomment-15052711
https://github.com/fastapi/fastapi/discussions/14389#discussioncomment-15052592
https://github.com/fastapi/fastapi/discussions/14388#discussioncomment-15052565
https://github.com/fastapi/fastapi/discussions/14365#discussioncomment-15052513
https://github.com/fastapi/fastapi/discussions/14341#discussioncomment-15052373
https://github.com/fastapi/fastapi/discussions/14263#discussioncomment-14837784
https://github.com/fastapi/fastapi/discussions/8763#discussioncomment-13577832
https://github.com/fastapi/fastapi/discussions/8662#discussioncomment-13554797
https://github.com/fastapi/fastapi/discussions/8463#discussioncomment-5152311
https://github.com/fastapi/fastapi/discussions/8810#discussioncomment-10233462
https://github.com/fastapi/fastapi/discussions/2475#discussioncomment-7133069
https://github.com/fastapi/fastapi/discussions/9709#discussioncomment-6447039
https://github.com/fastapi/fastapi/discussions/9709#discussioncomment-6448462
https://github.com/fastapi/fastapi/discussions/9705#discussioncomment-6372397
https://github.com/fastapi/fastapi/discussions/9516#discussioncomment-5858487
https://github.com/fastapi/fastapi/discussions/6188#discussioncomment-5128752

</details>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
