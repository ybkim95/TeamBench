# EASY3_LIST_SORTING: Fix List Sorting Bug

## Problem
A function that sorts a list of dictionaries by age is sorting in the wrong direction.

## Bug Description (Planner Only)
The issue is: sorted(people, key=lambda x: x['age'], reverse=False)  # Should be reverse=True

## Solution
Change reverse=False to reverse=True

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
