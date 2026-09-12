# EASY7_STRING_METHODS: Fix String Method Call

## Problem
String cleaning function uses wrong method.

## Bug Description (Planner Only)
The issue is: text.strip()  # Should be text.lower().strip()

## Solution
Chain string methods correctly

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
