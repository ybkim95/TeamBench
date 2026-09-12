# EASY4_JSON_PARSING: Fix JSON Parsing Error

## Problem
JSON loading function fails due to incorrect exception handling.

## Bug Description (Planner Only)
The issue is: except JSONDecodeError  # Missing 'as e'

## Solution
Add 'as e' to exception handling

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
