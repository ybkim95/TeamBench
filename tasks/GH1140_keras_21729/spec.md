# GH1140_keras_21729: Fix histogram op for symbolic inputs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/keras-team/keras/issues/21708
- Repo: https://github.com/keras-team/keras

## Issue Description

# Summary
On the TensorFlow backend, `keras.ops.histogram` crashes in graph mode because the TF implementation converts a tensor to a Python list via `.numpy().tolist()`. This is not graph-safe for symbolic tensors in a Keras Functional/Model context. The same code works on the JAX backend.

Minimal reproducible example

```python
# Repro: Keras 3 + TensorFlow backend, graph mode, jit or not
import os
os.environ["KERAS_BACKEND"] = "tensorflow"

import tensorflow as tf
import keras

tf.config.run_functions_eagerly(False)  # ensure graph

class HistogramProbe(keras.layers.Layer):
    def __init__(self, bins=8, lo=0.0, hi=1.0, **kwargs):
        super().__init__(**kwargs)
        self.bins = int(bins)
        self.lo = float(lo)
        self.hi = float(hi)

    def call(self, x):
        flat = keras.ops.reshape(x, (-1,))
        # This triggers TF backend histogram implementation which does .numpy().tolist()
        counts, edges = keras.ops.histogram(flat, bins=self.bins, range=(self.lo, self.hi))
        return x  # identity on data path

inp = keras.Input(shape=(16,), name="inp")
h = keras.layers.Dense(8, activation="relu")(inp)
h = HistogramProbe(name="probe")(h)
out = keras.layers.Dense(1)(h)
model = keras.Model(inp, out)

model.compile(optimizer="adam", loss="mse", jit_compile=True)  # jit_compile can be True or False
x = tf.random.uniform((32, 16))
y = tf.zeros((32, 1))

# Fails with AttributeError in graph mode
model.fit(x, y, epochs=1, batch_size=8)
```

See https://colab.research.google.com/drive/19R8qt7UjmX6Qz4YNkmz7KWWe3wO27MEw?usp=sharing

# Observed error (trimmed)

```
AttributeError: Exception encountered when calling HistogramProbe.call().

Could not automatically infer the output shape / dtype of 'probe' ...
Error encountered:
'SymbolicTensor' object has no attribute 'numpy'

Arguments received by HistogramProbe.call():
  • args=('<KerasTensor shape=(None, 8), dtype=float32, ...>',)
```

Root cause (source references)
In the TF backend implementation of `keras.ops.histogram`, the code does:

```python
bin_edges = tf.linspace(min_val, max_val, bins + 1)
bin_edges_list = bin_edges.numpy().tolist()  # <-- requires eager tensor
bin_indices = tf.raw_ops.Bucketize(input=x, boundaries=bin_edges_list[1:-1])
```

https://github.com/keras-team/keras/blob/b491c860fc2750e2b6006b55358d3251dbb4a9f0/keras/src/backend/tensorflow/numpy.py#L2966C1-L2966C48

Calling `.numpy()` on a symbolic tensor in a graph causes the crash.

# Expected behavior
`keras.ops.histogram` should be graph-safe on the TensorFlow backend (or clearly documented as eager-only). Ideally it should run inside a Keras model without errors.

# Environment
Please replace the versions with your actual outputs:
```
keras: 3.11.3
tensorflow: 2.19.0
jax: 0.5.3
python: 3.12.11 (main, Jun  4 2025, 08:56:18) [GCC 11.4.0]
platform: Linux-6.6.97+-x86_64-with-glibc2.35
backend: tensorflow
```

# Workarounds

Something like:

```python
def tf_histogram_fixed_width_1d(x, bins, range):
    lo = range[0]
    hi = range[1]
    x = tf.reshape(x, [-1])
    x = tf.clip_by_value(x, lo, hi)
    counts = tf.histogram_fixed_width(values=x, value_range=[lo, hi], nbins=bins)
    return counts, tf.linspace(lo, hi, bins + 1)
```

However, I think there might be slight edge issues around lo and hi.


# Notes

* The same repro runs fine on the JAX backend.
* The failure happens whether `jit_compile=True` or `False`, as long as the call happens in graph mode / symbolic context.

Thanks!

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Slightly better alternative implementation:

```python
def tf_ops_histogram(x, bins=10, range=None):
    import tensorflow as tf

    min_val = tf.math.reduce_min(x) if range is None else range[0]
    max_val = tf.math.reduce_max(x) if range is None else range[1]

    # Ignore out-of-range values (inclusive mask like Keras backend)
    in_range_mask = (x >= min_val) & (x <= max_val)
    in_range_x = tf.boolean_mask(x, in_range_mask)

    counts = tf.histogram_fixed_width(
        values=in_range_x,
        value_range=[min_val, max_val],
        nbins=bins,
    )

    return tf.cast(counts, x.dtype), tf.linspace(min_val, max_val, bins + 1)
```

It is still not exactly the same as `keras.ops.histogram` for some edge cases like NaNs, infinite and not flat values.

### Comment 2 ([user]):

Hi [user] - 
Thanks for the detailed information and the helpful workarounds!
I have reproduced this issue on my end with the latest version of Keras(3.11.3) and TensorFlow(2.20.0) and encountered the same `'SymbolicTensor' object has no attribute 'numpy'` error in this [gist](https://colab.sandbox.google.com/gist/sonali-kumari1/2fb1510c57d08b8461c7b10b310f854a/-21708.ipynb#scrollTo=MbEOMlBAs0nR). We will look into this issue and update you soon. Thanks again!

## PR Review Comments

**[user]** on `keras/src/backend/tensorflow/numpy.py`:

It looks like you can just use `tf.scatter_nd`:
- it creates a new tensor with zeros
- it also sums in the case of duplicate indices

**[user]** on `keras/src/backend/tensorflow/numpy.py`:

So `Bucketize` is not XLA compilable?

This table implies it is https://www.tensorflow.org/api_docs/python/tf/raw_ops

**[user]** on `keras/src/backend/tensorflow/numpy.py`:

`Bucketize` necessarily requires `boundaries` to be a Python list

**[user]** on `keras/src/backend/tensorflow/numpy.py`:

Thanks, done!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
