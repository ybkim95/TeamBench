# Reference solution — GH27_pydantic_12907

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH27_pydantic_12907`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH27_pydantic_12907/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/api/standard_library_types.md` (modified, +2/-1)
- `docs/errors/validation_errors.md` (modified, +21/-0)
- `pydantic-core/python/pydantic_core/core_schema.py` (modified, +1/-0)
- `pydantic-core/src/errors/types.rs` (modified, +2/-0)
- `pydantic-core/src/validators/string.rs` (modified, +7/-0)
- `pydantic-core/tests/test_errors.py` (modified, +1/-0)
- `pydantic/_internal/_known_annotated_metadata.py` (modified, +2/-0)
- `pydantic/types.py` (modified, +7/-0)
- `tests/test_types.py` (modified, +15/-0)

## `pydantic-core/python/pydantic_core/core_schema.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `pydantic/_internal/_known_annotated_metadata.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `pydantic/types.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]python

     min_length: int | None = None
     max_length: int | None = None
     pattern: str | Pattern[str] | None = None
+    ascii_only: bool | None = None
 
     def __iter__(self) -> Iterator[BaseMetadata]:
         if self.min_length is not None:

             or self.pattern is not None
             or self.to_lower is not None
             or self.to_upper is not None
+            or self.ascii_only is not None
         ):
             yield _fields.pydantic_general_metadata(
                 strip_whitespace=self.strip_whitespace,
                 to_upper=self.to_upper,
                 to_lower=self.to_lower,
                 pattern=self.pattern,
+                ascii_only=self.ascii_only,
             )
 
 

     min_length: int | None = None,
     max_length: int | None = None,
     pattern: str | Pattern[str] | None = None,
+    ascii_only: bool | None = None,
 ) -> type[str]:
     """
     !!! warning "Discouraged"

         min_length: The minimum length of the string.
         max_length: The maximum length of the string.
         pattern: A regex pattern to validate the string against.
+        ascii_only: Whether the string should contain only ASCII characters.
 
     Returns:
         The wrapped string type.

             min_length=min_length,
             max_length=max_length,
             pattern=pattern,
+            ascii_only=ascii_o
```

## Moved from `brief.md`

## Files That May Need Changes

        - `pydantic-core/python/pydantic_core/core_schema.py`
- `pydantic/_internal/_known_annotated_metadata.py`
- `pydantic/types.py`
