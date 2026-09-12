# EASY2: Fix String Formatting

## Problem
A greeting function needs to be updated to use modern Python f-string formatting instead of old-style string concatenation.

## Requirements
- Convert string concatenation to f-string format
- Handle edge cases (empty names, None values)
- Maintain the same output behavior

## Hidden Information (Planner Only)
The current code in `workspace/greetings.py` uses string concatenation like:
```python
return "Hello " + name + "!"
```

It should be converted to f-string format:
```python
return f"Hello {name}!"
```

Also need to handle:
- Empty strings should return "Hello!"
- None values should return "Hello!"
- Whitespace-only names should be stripped

## Test Cases
- `greet("Alice")` → `"Hello Alice!"`
- `greet("")` → `"Hello!"`
- `greet(None)` → `"Hello!"`
- `greet("  Bob  ")` → `"Hello Bob!"`