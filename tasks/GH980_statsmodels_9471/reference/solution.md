# Reference solution — GH980_statsmodels_9471

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH980_statsmodels_9471`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH980_statsmodels_9471/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/discrete/conditional_models.py` (modified, +12/-7)
- `statsmodels/discrete/tests/test_conditional.py` (modified, +25/-0)
- `statsmodels/duration/hazard_regression.py` (modified, +4/-3)
- `statsmodels/duration/tests/test_phreg.py` (modified, +20/-0)
- `statsmodels/formula/formulatools.py` (modified, +20/-0)
- `statsmodels/genmod/generalized_estimating_equations.py` (modified, +2/-0)
- `statsmodels/genmod/qif.py` (modified, +7/-5)
- `statsmodels/genmod/tests/test_gee.py` (modified, +40/-0)
- `statsmodels/genmod/tests/test_qif.py` (modified, +34/-0)
- `statsmodels/miscmodels/ordinal_model.py` (modified, +2/-1)
- `statsmodels/miscmodels/tests/test_ordinal_model.py` (modified, +19/-0)
- `statsmodels/othermod/betareg.py` (modified, +2/-1)
- `statsmodels/othermod/tests/test_beta.py` (modified, +15/-0)
- `statsmodels/regression/mixed_linear_model.py` (modified, +2/-1)
- `statsmodels/regression/tests/test_lme.py` (modified, +15/-0)

## Diff Summary (What the Fix Changes)

### `statsmodels/discrete/conditional_models.py`
```diff
@@ -2,15 +2,20 @@
 Conditional logistic, Poisson, and multinomial logit regression
 """
 
+import collections
+import itertools
+import warnings
+
 import numpy as np
+
 import statsmodels.base.model as base
-import statsmodels.regression.linear_model as lm
 import statsmodels.base.wrapper as wrap
-from statsmodels.discrete.discrete_model import (MultinomialResults,
-      MultinomialResultsWrapper)
-import collections
-import warnings
-import itertools
+from statsmodels.discrete.discrete_model import (
+    MultinomialResults,
+    MultinomialResultsWrapper,
+)
+from statsmodels.formula.formulatools import advance_eval_env
+import statsmodels.regression.linear_model as lm
 
 
 class _ConditionalModel(base.LikelihoodModel):
@@ -208,7 +213,7 @@ def from_formula(cls,
 
         if "0+" not in formula.replace(" ", ""):
             warnings.warn("Conditional models should not include an intercept")
-
+        advance_eval_env(kwargs)
         model = super().from_formula(
             formula, data=data, groups=groups, *args, **kwargs)
 
```

### `statsmodels/duration/hazard_regression.py`
```diff
@@ -14,13 +14,14 @@
 hazards model.
 http://www.mwsug.org/proceedings/2006/stats/MWSUG-2006-SD08.pdf
 """
+from statsmodels.compat.pandas import Appender
+
 import numpy as np
 
 from statsmodels.base import model
 import statsmodels.base.model as base
+from statsmodels.formula.formulatools import advance_eval_env
 from statsmodels.tools.decorators import cache_readonly
-from statsmodels.compat.pandas import Appender
-
 
 _predict_docstring = """
     Returns predicted values from the proportional hazards
@@ -423,7 +424,7 @@ def from_formula(cls, formula, data, status=None, entry=None,
             if term in ("0", "1"):
                 import warnings
                 warnings.warn("PHReg formulas should not include any '0' or '1' terms")
-
+        advance_eval_env(kwargs)
         mod = super().from_formula(formula, data,
                     status=status, entry=entry, strata=strata,
                     offset=offset, subset=subset, ties=ties,
```

### `statsmodels/formula/formulatools.py`
```diff
@@ -5,6 +5,8 @@
 # if users want to pass in a different formula framework, they can
 # add their handler here. how to do it interactively?
 
+__all__ = ["handle_formula_data", "formula_handler", "advance_eval_env"]
+
 # this is a mutable object, so editing it should show up in the below
 formula_handler = {}
 
@@ -77,3 +79,21 @@ def make_hypotheses_matrices(model_results, test_formula):
     exog_names = model_results.model.exog_names
     lc = mgr.get_linear_constraints(test_formula, exog_names)
     return lc
+
+
+def advance_eval_env(kwargs):
+    """
+    Adjusts the keyword arguments for from_formula to account for the patsy
+    eval environment being passed down once on the stack. Adjustments are
+    made in place.
+    Parameters
+    ----------
+    kwargs : dict
+        The dictionary of keyword arguments passed to `from_formula`.
+    """
+
+    eval_env = kwargs.get("eval_env", None)
+    if eval_env is None:
+        kwargs["eval_env"] = 2
+    elif eval_env == -1:
+        kwargs["eval_env"] = FormulaManager().get_empty_eval_env()
```

### `statsmodels/genmod/generalized_estimating_equations.py`
```diff
@@ -46,6 +46,7 @@
     margeff_cov_with_se,
 )
 from statsmodels.formula._manager import FormulaManager
+from statsmodels.formula.formulatools import advance_eval_env
 from statsmodels.genmod import cov_struct as cov_structs, families
 from statsmodels.genmod.families.links import Link
 import statsmodels.genmod.families.varfuncs as varfuncs
@@ -762,6 +763,7 @@ def from_formula(cls, formula, groups, data, subset=None,
             family = kwargs["family"]
             del kwargs["family"]
 
+        advance_eval_env(kwargs)
         model = super().from_formula(formula, data=data, subset=subset,
                                      groups=groups, time=time,
                                      offset=offset,
```

### `statsmodels/genmod/qif.py`
```diff
@@ -1,12 +1,14 @@
-import numpy as np
 from collections import defaultdict
+
+import numpy as np
+
 import statsmodels.base.model as base
+import statsmodels.base.wrapper as wrap
+from statsmodels.formula.formulatools import advance_eval_env
 from statsmodels.genmod import families
+from statsmodels.genmod.families import links, varfuncs
 from statsmodels.genmod.generalized_linear_model import GLM
-from statsmodels.genmod.families import links
-from statsmodels.genmod.families import varfuncs
 import statsmodels.regression.linear_model as lm
-import statsmodels.base.wrapper as wrap
 from statsmodels.tools.decorators import cache_readonly
 
 
@@ -329,7 +331,7 @@ def from_formula(cls, formula, groups, data, subset=None,
 
         if isinstance(groups, str):
             groups = data[groups]
-
+        advance_eval_env(kwargs)
         model = super().from_formula(
                    formula, data=data, subset=subset,
                    groups=groups, *args, **kwargs)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `statsmodels/discrete/conditional_models.py`
- `statsmodels/duration/hazard_regression.py`
- `statsmodels/formula/formulatools.py`
- `statsmodels/genmod/generalized_estimating_equations.py`
- `statsmodels/genmod/qif.py`
