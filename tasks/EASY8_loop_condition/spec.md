# EASY8_LOOP_CONDITION: Fix Loop Condition

## Problem
While loop has off-by-one error.

## Bug Description (Planner Only)
The issue is: while i < len(items):  # Should be <= for inclusive range

## Solution
Correct loop boundary condition

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
