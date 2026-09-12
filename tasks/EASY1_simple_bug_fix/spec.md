# EASY1: Simple Bug Fix in Calculator

## Problem
A basic calculator function has a simple arithmetic bug that causes incorrect results for division operations.

## File to Fix
`workspace/calculator.py` contains a `divide` function that returns wrong results.

## Expected Behavior
- `divide(10, 2)` should return `5.0`
- `divide(15, 3)` should return `5.0`  
- `divide(7, 2)` should return `3.5`
- `divide(1, 0)` should raise `ValueError("Cannot divide by zero")`

## Current Behavior
The function returns incorrect results due to a simple typo.

## Instructions for Teams

### Planner (sees this specification)
The bug is in the division function - there's a typo where multiplication (`*`) is used instead of division (`/`). Guide the executor to:
1. Find the `divide` function
2. Look for the arithmetic operation
3. Fix the operator
4. Test the function

### Executor (sees only brief.md)
You need to fix a calculator bug. The `divide` function in `workspace/calculator.py` is returning wrong results. Run the tests to see what's failing, then fix the issue.

### Verifier
Confirm that:
- All division operations work correctly
- Division by zero raises appropriate error
- Tests pass
- Code is clean and readable

## Success Criteria
- All test cases pass
- Code follows Python conventions
- Proper error handling for division by zero