# Reference solution — GH1042_matplotlib_31091

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1042_matplotlib_31091`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1042_matplotlib_31091/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/tests/test_ticker.py` (modified, +16/-0)
- `lib/matplotlib/ticker.py` (modified, +5/-2)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/ticker.py`
```diff
@@ -1767,8 +1767,11 @@ def __call__(self):
         return self.tick_values(dmin, dmax)
 
     def tick_values(self, vmin, vmax):
-        return self.raise_if_exceeds(
-            np.arange(vmin + self.offset, vmax + 1, self._base))
+        # We want tick values in the closed interval [vmin, vmax].
+        # Since np.arange(start, stop) returns values in the semi-open interval
+        # [start, stop), we add a minimal offset so that stop = vmax + eps
+        tick_values = np.arange(vmin + self.offset, vmax + 1e-12, self._base)
+        return self.raise_if_exceeds(tick_values)
 
 
 class FixedLocator(Locator):
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/ticker.py`
