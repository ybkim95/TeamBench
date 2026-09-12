# GH95_arrow_1242: Fix humanize reporting 'a month' for 16-day differences — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/arrow-py/arrow/issues/1240
- Repo: https://github.com/arrow-py/arrow

## Issue Description

<!--
Thanks for taking the time to submit this bug report.

Please provide us with a detailed description of the bug and a bit of information about your system.
-->

## Issue Description

It seems that the intervals being used for the various thresholds for `humanize` are a bit strange. For example, on one of my websites, I have a list of upcoming events with both the calendar date and a `humanize`d description. As of today, January 9 2026, there are two events, one on January 24 which appears as "in two weeks" and one on January 25 which appears as "in a month."

15 days (the 24th) is indeed about two weeks away, but 16 days (the 25th) is certainly not a month away - if anything it's also closest to around two weeks away. It isn't even closer to three weeks than two, less alone a month.

## System Info

- 🖥  **OS name and version**: Linux (Ubuntu 24.04 LTS if that matters)
- 🐍  **Python version**: 3.12.3
- 🏹  **Arrow version**: 1.4.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user],

Thanks for bringing this up. We did change some of the ranges to fix up some long standing bugs in humanize.

We'll need to add some more tests to cover these cases to further improve the humanize.

### Comment 2 ([user]):

Alright, I'm glad to hear that this is not intentional and that it's a work in progress. :)

### Comment 3 ([user]):

This is an improvement but the aspect of what was confusing wasn’t just about crossing calendar boundaries. 16 days still feels like “in two weeks” regardless of whether it straddles a calendar month.

What would make more sense to me is to first look at the number of weeks and then round to the nearest 7-day interval (which would also allow for “in 3 weeks”), and only switch to “X months” when the interval has rounded to at least four weeks.

### Comment 4 ([user]):

I just ran into another "interesting" case, where a few hours less than 14 days is being treated as "one week."

### Comment 5 ([user]):

I know that mapping intuitive notions of time intervals to code can be difficult and perilous, but what makes the most sense to me is to identify the general "region" of time intervals it's in and then to round to the nearest one, with standard round-nearest (up if more than halfway) behavior, and once the interval would round up to the next order of magnitude, round it to there. For example, if it's between 17.5 and 24.5 days, it would be "in three weeks," but once you exceed 24.5 it would be "in one month."

Intuitive time intervals, to me, would be:

* Minutes (where if you round to 60 or more it becomes hours)
* Hours (where if you round to 24 or more it becomes days)
* Days (where if you round to 7 or more it becomes weeks)
* Weeks (where if you round to 4 or more it becomes months)
* Months (where if you round to 12 or more it becomes years)
* Years

Ideally these intervals could also be user-defined in some way (so someone could start the rounding to a day at, say, 18 hours, or someone could choose a 5- or 10-minute interval after reaching 10 minutes, for example).

Does this make sense?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
