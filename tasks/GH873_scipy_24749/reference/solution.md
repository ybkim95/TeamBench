# Reference solution — GH873_scipy_24749

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH873_scipy_24749`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH873_scipy_24749/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/signal/_fir_filter_design.py` (modified, +6/-6)
- `scipy/signal/tests/test_fir_filter_design.py` (modified, +17/-1)

## Diff Summary (What the Fix Changes)

### `scipy/signal/_fir_filter_design.py`
```diff
@@ -1394,15 +1394,15 @@ def minimum_phase(h,
         # lmin[n] = 2u[n] - d[n]
         # i.e., double the positive frequencies and zero out the negative ones;
         # Oppenheim+Shafer 3rd ed p991 eq13.42b and p1004 fig13.7
-        win = xp.zeros(n_fft)
-        win[0] = 1
+        win = xp.zeros(n_fft, dtype=h_temp.dtype)
+        win = xpx.at(win)[0].set(1)
         stop = n_fft // 2
-        win[1:stop] = 2
-        if n_fft % 2:
-            win[stop] = 1
+        win = xpx.at(win)[1:stop].set(2)
+        # Nyquist freq: odd use 2, even use 1
+        win = xpx.at(win)[stop].set(1 + (n_fft % 2))
         h_temp *= win
         h_temp = ifft(xp.exp(fft(h_temp)))
-        h_minimum = h_temp.real
+        h_minimum = xp.real(h_temp)
     n_out = (n_half + h.shape[0] % 2) if half else h.shape[0]
     return h_minimum[:n_out]
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/signal/_fir_filter_design.py`
