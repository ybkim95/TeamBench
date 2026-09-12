# EASY5_VARIABLE_SCOPE: Fix Variable Scope Issue

## Problem
Function has UnboundLocalError due to variable scope.

## Bug Description (Planner Only)
The issue is: Modifying global variable without 'global' keyword

## Solution
Add 'global' declaration or use return value

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
