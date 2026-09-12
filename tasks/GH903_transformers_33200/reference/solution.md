# Reference solution — GH903_transformers_33200

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH903_transformers_33200`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH903_transformers_33200/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/en/model_doc/superpoint.md` (modified, +23/-14)
- `src/transformers/models/superpoint/image_processing_superpoint.py` (modified, +57/-2)
- `src/transformers/models/superpoint/modeling_superpoint.py` (modified, +8/-2)
- `tests/models/superpoint/test_image_processing_superpoint.py` (modified, +53/-1)
- `tests/models/superpoint/test_modeling_superpoint.py` (modified, +6/-4)

## Diff Summary (What the Fix Changes)

### `src/transformers/models/superpoint/image_processing_superpoint.py`
```diff
@@ -13,11 +13,11 @@
 # limitations under the License.
 """Image processor class for SuperPoint."""
 
-from typing import Dict, Optional, Union
+from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
 
 import numpy as np
 
-from ... import is_vision_available
+from ... import is_torch_available, is_vision_available
 from ...image_processing_utils import BaseImageProcessor, BatchFeature, get_size_dict
 from ...image_transforms import resize, to_channel_dimension_format
 from ...image_utils import (
@@ -32,6 +32,12 @@
 from ...utils import TensorType, logging, requires_backends
 
 
+if is_torch_available():
+    import torch
+
+if TYPE_CHECKING:
+    from .modeling_superpoint import SuperPointKeypointDescriptionOutput
+
 if is_vision_available():
     import PIL
 
@@ -270,3 +276,52 @@ def preprocess(
         data = {"pixel_values": images}
 
         return BatchFeature(data=data, tensor_type=return_tensors)
+
+    def post_process_keypoint_detection(
+        self, outputs: "SuperPointKeypointDescriptionOutput", target_sizes: Union[TensorType, List[Tuple]]
+    ) -> List[Dict[str, "torch.Tensor"]]:
+        """
+        Converts the raw output of [`SuperPointForKeypointDetection`] into lists of keypoints, scores and descriptors
+        with coordinates absolute to the original image sizes.
+
+        Args:
+            outputs ([`SuperPointKeypointDescriptionOutput`]):
+                Raw outputs of the model containing keypoints in a relative (x, y) format, with scores and descriptors.
+            target_sizes (`torch.Tensor` or `List[Tuple[int, int]]`):
+                Tensor of shape `(batch_size, 2)` or list of tuples (`Tuple[int, int]`) containing the target size
+                `(height, width)` of each image in the batch. This must be the original
+                image size (before any processing).
+        Returns:
+            `List[Dict]`: A list of dictionaries, each dictionary containing the keypoints in absolute format according
+   
```

### `src/transformers/models/superpoint/modeling_superpoint.py`
```diff
@@ -239,7 +239,10 @@ def _get_pixel_scores(self, encoded: torch.Tensor) -> torch.Tensor:
         return scores
 
     def _extract_keypoints(self, scores: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
-        """Based on their scores, extract the pixels that represent the keypoints that will be used for descriptors computation"""
+        """
+        Based on their scores, extract the pixels that represent the keypoints that will be used for descriptors computation.
+        The keypoints are in the form of relative (x, y) coordinates.
+        """
         _, height, width = scores.shape
 
         # Threshold keypoints by score value
@@ -447,7 +450,7 @@ def forward(
 
         pixel_values = self.extract_one_channel_pixel_values(pixel_values)
 
-        batch_size = pixel_values.shape[0]
+        batch_size, _, height, width = pixel_values.shape
 
         encoder_outputs = self.encoder(
             pixel_values,
@@ -485,6 +488,9 @@ def forward(
             descriptors[i, : _descriptors.shape[0]] = _descriptors
             mask[i, : _scores.shape[0]] = 1
 
+        # Convert to relative coordinates
+        keypoints = keypoints / torch.tensor([width, height], device=keypoints.device)
+
         hidden_states = encoder_outputs[1] if output_hidden_states else None
         if not return_dict:
             return tuple(v for v in [loss, keypoints, scores, descriptors, mask, hidden_states] if v is not None)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `src/transformers/models/superpoint/image_processing_superpoint.py`
- `src/transformers/models/superpoint/modeling_superpoint.py`
