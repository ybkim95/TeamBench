# GH121_quart_302: avoid ResourceWarning in `DataBody.__aiter__`  — Full Specification (Planner Only)

## Source
- PR: https://github.com/pallets/quart/pull/302
- Issue: https://github.com/pallets/quart/issues/301
- Repo: https://github.com/pallets/quart

## Issue Description

from quart-trio I get a:

```ResourceWarning: Async generator 'quart.wrappers.response.DataBody.__aiter__.<locals>._aiter' was garbage collected before it had been exhausted. Surround its use in 'async with aclosing(...):' to ensure that it gets cleaned up as soon as you're done using it.```

Environment:

- Python version:
- Quart version:

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@pgjones):

I'm also unsure how to test this, however I've an alternative fix,
```python
diff --git a/src/quart/wrappers/response.py b/src/quart/wrappers/response.py
index 9460c2e..6b0b364 100644

         self.data = data
         self.begin = 0
         self.end = len(self.data)
+        self.iter: AsyncGenerator[bytes, None]
 
     async def __aenter__(self) -> DataBody:
+        async def _aiter() -> AsyncGenerator[bytes, None]:
+            yield self.data[self.begin : self.end]
+
+        self.iter = _aiter()
         return self
 
     async def __aexit__(self, exc_type: type, exc_value: BaseException, tb: TracebackType) -> None:
-        pass
+        await self.iter.aclose()
 
     def __aiter__(self) -> AsyncIterator:
-        async def _aiter() -> AsyncGenerator[bytes, None]:
-            yield self.data[self.begin : self.end]
-
-        return _aiter()
+        return self.iter
 
     async def make_conditional(self, begin: int, end: int | None) -> int:
         self.begin = begin
```

What do you think of this? I prefer it as it is more similar to the `IterableBody`

## PR Review Comments

**@davidism** on `src/quart/wrappers/response.py`:

This type of optimization should no longer be needed in modern Python.

**@graingert** on `src/quart/wrappers/response.py`:

```suggestion
        return self._data_body.data[self._data_body.begin : self._data_body.end]
```

## Files Changed in Fix

- `src/quart/wrappers/response.py` (modified, +15/-5)

## `src/quart/wrappers/response.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
