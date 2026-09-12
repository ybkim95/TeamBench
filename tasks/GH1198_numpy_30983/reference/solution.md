# Reference solution — GH1198_numpy_30983

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1198_numpy_30983`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1198_numpy_30983/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `numpy/f2py/cfuncs.py` (modified, +27/-27)
- `numpy/f2py/tests/src/regression/complex_struct_compat.f90` (added, +8/-0)
- `numpy/f2py/tests/src/regression/complex_struct_compat.pyf` (added, +12/-0)
- `numpy/f2py/tests/test_regression.py` (modified, +17/-0)

## Diff Summary (What the Fix Changes)

### `numpy/f2py/cfuncs.py`
```diff
@@ -89,9 +89,9 @@ def errmess(s: str) -> None:
 typedef long double long_double;
 #endif
 """
-typedefs['complex_long_double'] = 'typedef npy_clongdouble complex_long_double;'
-typedefs['complex_float'] = 'typedef npy_cfloat complex_float;'
-typedefs['complex_double'] = 'typedef npy_cdouble complex_double;'
+typedefs['complex_long_double'] = 'typedef union { struct {long double r,i;}; npy_clongdouble _npy; } complex_long_double;'
+typedefs['complex_float'] = 'typedef union { struct {float r,i;}; npy_cfloat _npy; } complex_float;'
+typedefs['complex_double'] = 'typedef union { struct {double r,i;}; npy_cdouble _npy; } complex_double;'
 typedefs['string'] = """typedef char * string;"""
 typedefs['character'] = """typedef char character;"""
 
@@ -289,13 +289,13 @@ def errmess(s: str) -> None:
 #define pyobj_from_float1(v) (PyFloat_FromDouble(v))"""
 needs['pyobj_from_complex_long_double1'] = ['complex_long_double', 'npy_math.h']
 cppmacros['pyobj_from_complex_long_double1'] = """
-#define pyobj_from_complex_long_double1(v) (PyComplex_FromDoubles((double)npy_creall(v),(double)npy_cimagl(v)))"""
+#define pyobj_from_complex_long_double1(v) (PyComplex_FromDoubles((double)npy_creall(v._npy),(double)npy_cimagl(v._npy)))"""
 needs['pyobj_from_complex_double1'] = ['complex_double', 'npy_math.h']
 cppmacros['pyobj_from_complex_double1'] = """
-#define pyobj_from_complex_double1(v) (PyComplex_FromDoubles(npy_creal(v),npy_cimag(v)))"""
+#define pyobj_from_complex_double1(v) (PyComplex_FromDoubles(npy_creal(v._npy),npy_cimag(v._npy)))"""
 needs['pyobj_from_complex_float1'] = ['complex_float', 'npy_math.h']
 cppmacros['pyobj_from_complex_float1'] = """
-#define pyobj_from_complex_float1(v) (PyComplex_FromDoubles((double)npy_crealf(v),(double)npy_cimagf(v)))"""
+#define pyobj_from_complex_float1(v) (PyComplex_FromDoubles((double)npy_crealf(v._npy),(double)npy_cimagf(v._npy)))"""
 needs['pyobj_from_string1'] = ['string']
 cppmacros['pyobj_from_string1'] = """
 #define pyobj_from_stri
```

## Moved from `brief.md`

## Files That May Need Changes

- `numpy/f2py/cfuncs.py`
