# Reference solution — GH563_starlette_3143

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH563_starlette_3143`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH563_starlette_3143/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `starlette/responses.py` (modified, +21/-16)
- `tests/test_responses.py` (modified, +72/-8)

## `starlette/responses.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]
-        --{boundary}\n
-        Content-Type: {content_type}\n
-        Content-Range: bytes {start}-{end-1}/{max_size}\n
-        \n
-        ..........content...........\n
-        --{boundary}\n
-        Content-Type: {content_type}\n
-        Content-Range: bytes {start}-{end-1}/{max_size}\n
-        \n
-        ..........content...........\n
-        --{boundary}--\n
+        --{boundary}\r\n
+        Content-Type: {content_type}\r\n
+        Content-Range: bytes {start}-{end-1}/{max_size}\r\n
+        \r\n
+        ..........content...........\r\n
+        --{boundary}\r\n
+        Content-Type: {content_type}\r\n
+        Content-Range: bytes {start}-{end-1}/{max_size}\r\n
+        \r\n
+        ..........content...........\r\n
+        --{boundary}--
         ```
         """
         boundary_len = len(boundary)
-        static_header_part_len = 44 + boundary_len + len(content_type) + len(str(max_size))
+        static_header_part_len = 49 + boundary_len + len(content_type) + len(str(max_size))
         content_length = sum(
             (len
```

## Moved from `brief.md`

## Files That May Need Changes

- `starlette/responses.py`
