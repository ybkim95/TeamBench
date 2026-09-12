# GH1022_keras_20768: fix(ops): Fix issue with map_coordinates for uint8 dtype — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/keras-team/keras/issues/20608
- Repo: https://github.com/keras-team/keras

## Issue Description

Consider the following simple example
```python
import keras

image = keras.ops.ones((1, 1, 3), dtype='uint8')

coordinates = keras.ops.convert_to_tensor([-1., 0., 0.])[..., None, None]
interp = keras.ops.image.map_coordinates(image, coordinates, order=1, fill_mode='constant')
```
that is expected to yield `[[0]]`. However, with `KERAS_BACKEND=tensorflow` this code snippet results in
```console
2024-12-08 16:04:24.790791: W tensorflow/core/framework/op_kernel.cc:1841] OP_REQUIRES failed at gather_nd_op.cc:65 : INVALID_ARGUMENT: indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd
2024-12-08 16:04:24.790814: I tensorflow/core/framework/local_rendezvous.cc:405] Local rendezvous is aborting with status: INVALID_ARGUMENT: indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd
Traceback (most recent call last):
  File "<home>/tfmapc.py", line 11, in <module>
    interp = keras.ops.image.map_coordinates(image, coordinates, order=1, fill_mode='constant')
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<home>/.env/lib/python3.12/site-packages/keras/src/ops/image.py", line 787, in map_coordinates
    return backend.image.map_coordinates(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<home>/.env/lib/python3.12/site-packages/keras/src/backend/tensorflow/image.py", line 485, in map_coordinates
    contribution = tf.cond(tf.reduce_all(validities), fast_path, slow_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<home>/.env/lib/python3.12/site-packages/tensorflow/python/util/traceback_utils.py", line 153, in error_handler
    raise e.with_traceback(filtered_tb) from None
  File "<home>/.env/lib/python3.12/site-packages/keras/src/backend/tensorflow/image.py", line 481, in slow_path
    tf.transpose(tf.gather_nd(input_arr, indices)),
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tensorflow.python.framework.errors_impl.InvalidArgumentError: {{function_node __wrapped__GatherNd_device_/job:localhost/replica:0/task:0/device:CPU:0}} indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd [Op:GatherNd] name:
```
The problem does not occur if I change the `dtype` of `image` from `uint8` to `float32` or switch either to the `jax` or `torch` backends. Also changing the `fill_mode` from `constant` to `nearest` avoids the issue.

Keras version: 3.7.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] -

Thanks for reporting this issue. I am able to reproduce this issue and found that seems like issue is related to only tensorflow backend where dtype mismatch scenarios(uint8 for image and float32 for coordinates) is not handled in tensorflow backend. 
Attached [gist](https://colab.sandbox.google.com/gist/mehtamansi29/b05fe6723d9723752ebf811e2d753bd9/20608-keras-ops-image-map_coordinates-fails-on-uint8-input-with-tensorflow-backend.ipynb) for the reference.
We will dig more into the issue and update on the same.

### Comment 2 ([user]):

Hello [user] [user], thanks for bringing the issue up!

I identified the root cause of the error with `keras.ops.image.map_coordinates` failing for `dtype='uint8'` and `fill_mode='constant'` when using TensorFlow as the backend. The issue stemmed from improper handling of out-of-bound coordinates, which led to invalid indexing. Interestingly, the error did not occur with `float32` or with alternative backends like JAX and Torch.

To fix this:
1. Improved how coordinates are processed, ensuring all `fill_mode` cases (including "reflect") are handled correctly.
2. Simplified the logic for gathering and applying fill values, ensuring consistent behavior across data types.

I also wrote test cases to validate these changes, covering scenarios for `uint8`, `float32`, and different `fill_mode` settings to confirm the fixes work as expected, which yield the following results:

Test Cases:

```python
from keras.src import ops
def test_map_coordinates():
    image_uint8 = ops.ones((1, 1, 3), dtype='uint8')
    coordinates = ops.convert_to_tensor([-1., 0., 0.])[..., None, None]
    
    try:
        interp_uint8 = ops.image.map_coordinates(
            image_uint8, coordinates, order=1, fill_mode='constant'
        )
        print("Test 1 (uint8) succeeded:", interp_uint8)
    except Exception as e:
        print("Test 1 (uint8) failed:", str(e))

    image_float32 = ops.ones((1, 1, 3), dtype='float32')

    try:
        interp_float32 = ops.image.map_coordinates(
            image_float32, coordinates, order=1, fill_mode='constant'
        )
        print("\nTest 2 (float32) succeeded:", interp_float32)
    except Exception as e:
        print("\nTest 2 (float32) failed:", str(e))
        
    try:
        interp_nearest = ops.image.map_coordinates(
            image_uint8, coordinates, order=1, fill_mode='nearest'
        )
        print("\nTest 3 (nearest) succeeded:", interp_nearest)
    except Exception as e:
        print("\nTest 3 (nearest) failed:", str(e))
        
    image_uint8_casted = ops.cast(image_uint8, 'float32')

    try:
        interp_casted = ops.cast(
            ops.image.map_coordinates(
                image_uint8_casted, coordinates, order=1, fill_mode='constant'
            ),
            'uint8'
        )
        print("\nTest 4 (manual cast) succeeded:", interp_casted)
    except Exception as e:
        print("\nTest 4 (manual cast) failed:", str(e))

test_map_coordinates()
```

Outputs (Old):

```
Test 1 (uint8) failed: {{function_node __wrapped__GatherNd_device_/job:localhost/replica:0/task:0/device:CPU:0}} indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd [Op:GatherNd] name: 
2025-01-16 10:24:47.078199: W tensorflow/core/framework/op_kernel.cc:1841] OP_REQUIRES failed at gather_nd_op.cc:65 : INVALID_ARGUMENT: indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd
2025-01-16 10:24:47.078570: I tensorflow/core/framework/local_rendezvous.cc:405] Local rendezvous is aborting with status: INVALID_ARGUMENT: indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd

Test 2 (float32) failed: {{function_node __wrapped__GatherNd_device_/job:localhost/replica:0/task:0/device:CPU:0}} indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd [Op:GatherNd] name:

Test 3 (nearest) succeeded: tf.Tensor([[1]], shape=(1, 1), dtype=uint8)
2025-01-16 10:24:47.099168: W tensorflow/core/framework/op_kernel.cc:1841] OP_REQUIRES failed at gather_nd_op.cc:65 : INVALID_ARGUMENT: indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd

Test 4 (manual cast) failed: {{function_node __wrapped__GatherNd_device_/job:localhost/replica:0/task:0/device:CPU:0}} indices[0,0] = [-1, 0, 0] does not index into param shape [1,1,3], node name: GatherNd [Op:GatherNd] name:
```

Outputs (New):

```
Test 1 (uint8) succeeded: tf.Tensor([[0]], shape=(1, 1), dtype=uint8)

Test 2 (float32) succeeded: tf.Tensor([[0.]], shape=(1, 1), dtype=float32)

Test 3 (nearest) succeeded: tf.Tensor([[1]], shape=(1, 1), dtype=uint8)

Test 4 (manual cast) succeeded: tf.Tensor([[0]], shape=(1, 1), dtype=uint8)
```

I'd love to raise a PR to address the issue, do let me know how you'd like to proceed!

### Comment 3 ([user]):

Hi [user] -

> To fix this:
> 
> 1. Improved how coordinates are processed, ensuring all `fill_mode` cases (including "reflect") are handled correctly.
> 2. Simplified the logic for gathering and applying fill values, ensuring consistent behavior across data types.

Thanks for look into this. You can raise the PR for the address this use with your fix.

### Comment 4 ([user]):

Are you satisfied with the resolution of your issue?
<a href="https://docs.google.com/forms/d/e/1FAIpQLSdHag0RVFS7UXzZkKcsFCKOcX8raCupKK9RHSlYxp5U8lSJbQ/viewform?entry.492125872=Yes&entry.243948740=https://github.com/keras-team/keras/issues/20608">Yes</a>
<a href="https://docs.google.com/forms/d/e/1FAIpQLSdHag0RVFS7UXzZkKcsFCKOcX8raCupKK9RHSlYxp5U8lSJbQ/viewform?entry.492125872=No&entry.243948740=https://github.com/keras-team/keras/issues/20608">No</a>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
