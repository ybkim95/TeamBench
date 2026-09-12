# Reference solution — GH876_great_expectati_1569

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH876_great_expectati_1569`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH876_great_expectati_1569/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/reference/changelog.rst` (modified, +1/-0)
- `great_expectations/render/renderer/suite_scaffold_notebook_renderer.py` (modified, +1/-1)
- `tests/render/renderer/test_suite_scaffold_notebook_renderer.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `great_expectations/render/renderer/suite_scaffold_notebook_renderer.py`
```diff
@@ -130,7 +130,7 @@ def render(self, batch_kwargs=None, **kwargs) -> nbformat.NotebookNode:
 
 This is highly configurable depending on your goals. You can include or exclude
 columns, and include or exclude expectation types (when applicable). [The
-Expectation Glossary](http://docs.greatexpectations.io/en/latest/expectation_glossary.html)
+Expectation Glossary](https://docs.greatexpectations.io/en/latest/reference/glossary_of_expectations.html?utm_source=notebook&utm_medium=scaffold_expectations)
 contains a list of possible expectations."""
         )
         self._add_scaffold_cell()
```

## Moved from `brief.md`

## Files That May Need Changes

- `great_expectations/render/renderer/suite_scaffold_notebook_renderer.py`
