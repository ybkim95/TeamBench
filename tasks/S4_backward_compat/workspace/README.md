# textparser

A stable v1 text parsing library.

## Usage

```python
from textparser import TextParser

obj = TextParser()
result = obj.process("hello world")
print(result)  # {"result": "hello world", "status": "ok", ...}
```

## Adding the New Feature

The `new_feature.py` file contains a stub for `strict_mode` (strict validation that raises on any anomaly).
Implement it without breaking any existing behavior.

```python
from new_feature import strict_mode
```

## Backward Compatibility

This library maintains strict backward compatibility for all v1.x releases.
- `process()` return shape is stable
- Constructor accepts None, str, or dict config
- Deprecated aliases remain callable
- `__version__` stays in 1.x series
