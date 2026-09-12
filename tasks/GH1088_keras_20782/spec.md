# GH1088_keras_20782: fix(metrics): Fix BinaryAccuracy metric to handle boolean inputs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/keras-team/keras/issues/20178
- Repo: https://github.com/keras-team/keras

## Issue Description

I have some very strange results out of the `

Consider the code below:
```
import os
os.environ["KERAS_BACKEND"] = "jax"
import keras


inp = keras.Input(shape=(1,))
out = inp > 0.5
mm = keras.Model(inputs=inp, outputs=out) 

x = np.random.rand(32, 1)

res = mm.predict(x)
met = keras.metrics.BinaryAccuracy()
met.update_state(x>0.5, res>0.5)
met.result()
```

I would expect to get 1 every single run. Instead I get some random result (close to 0.5). 

Packages' versions (tf, keras, jax, np)
```
'2.17.0', '3.5.0', '0.4.26', '1.26.4'
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The result is correct if I cast the second parameter of `update_state` to a `float` or `int`.

### Comment 2 ([user]):

Hi [user]

While updating state(met.update_state(x>0.5, res>0.5)), x>0.5 and res>0.5 are in boolean arrays. But BinaryAccuracy metrics accepts only numerical values(floats or integers) only. 

While running same code in tensorflow backend it is giving error message. 
Error:
InvalidArgumentError: Value for attr 'T' of bool is not in the list of allowed values: float, double, int32, uint8, int16, int8, int64, bfloat16, uint16, half, uint32, uint64
	; NodeDef: {{node Greater}}; Op<name=Greater; signature=x:T, y:T -> z:bool; attr=T:type,allowed=[DT_FLOAT, DT_DOUBLE, DT_INT32, DT_UINT8, DT_INT16, DT_INT8, DT_INT64, DT_BFLOAT16, DT_UINT16, DT_HALF, DT_UINT32, DT_UINT64]> [Op:Greater] name

```
import os
os.environ["KERAS_BACKEND"] = "tensorflow"
import keras
import numpy as np

inp = keras.Input(shape=(1,))
out = inp > 0.5
mm = keras.Model(inputs=inp, outputs=out) 

x = np.random.rand(32, 1)

res = mm.predict(x)
met = keras.metrics.BinaryAccuracy()
met.update_state(x>0.5, res>0.5)
met.result()

 
```

So in the JAX there should be same error message comes while giving boolean into BinaryAccuracy metrics. You can create new issue in [JAX](https://github.com/google/jax/issues) repo for adding the error message.

### Comment 3 ([user]):

We could consider casting the values to `floatx()` in `update_state()` -- would you like to open a PR [user] ?

### Comment 4 ([user]):

> We could consider casting the values to `floatx()` in `update_state()` -- would you like to open a PR [user] ?

Hi [user] - I will raise PR for casting the values to floatx() in update_state().

### Comment 5 ([user]):

Hello [user], do you still plan to raise this PR since the issue can still be reproduced, or may I do it? I believe I've fixed the issue along with its corresponding unit test. However, if it's your PR, no worries! Please do let me know!

### Comment 6 ([user]):

Are you satisfied with the resolution of your issue?
<a href="https://docs.google.com/forms/d/e/1FAIpQLSdHag0RVFS7UXzZkKcsFCKOcX8raCupKK9RHSlYxp5U8lSJbQ/viewform?entry.492125872=Yes&entry.243948740=https://github.com/keras-team/keras/issues/20178">Yes</a>
<a href="https://docs.google.com/forms/d/e/1FAIpQLSdHag0RVFS7UXzZkKcsFCKOcX8raCupKK9RHSlYxp5U8lSJbQ/viewform?entry.492125872=No&entry.243948740=https://github.com/keras-team/keras/issues/20178">No</a>

## PR Review Comments

**[user]** on `keras/src/metrics/reduction_metrics.py`:

I think we should prefer using `self.dtype`?

**[user]** on `keras/src/metrics/reduction_metrics.py`:

Agreed, will make the change. Thanks for pointing this out!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
