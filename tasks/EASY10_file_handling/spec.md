# EASY10_FILE_HANDLING: Fix File Handle Leak

## Problem
File is opened but never closed.

## Bug Description (Planner Only)
The issue is: f = open('file.txt'); return f.read()  # No close()

## Solution
Use 'with' statement for proper file handling

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
