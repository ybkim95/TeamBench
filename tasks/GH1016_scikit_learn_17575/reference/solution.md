# Reference solution — GH1016_scikit_learn_17575

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1016_scikit_learn_17575`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1016_scikit_learn_17575/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/upcoming_changes/sklearn.tree/17575.fix.rst` (added, +3/-0)
- `sklearn/tree/_export.py` (modified, +9/-0)
- `sklearn/tree/tests/test_export.py` (modified, +84/-0)

## Diff Summary (What the Fix Changes)

### `sklearn/tree/_export.py`
```diff
@@ -308,6 +308,7 @@ def node_to_str(self, tree, node_id, criterion):
             # Always write node decision criteria, except for leaves
             if self.feature_names is not None:
                 feature = self.feature_names[tree.feature[node_id]]
+                feature = self.str_escape(feature)
             else:
                 feature = "x%s%s%s" % (
                     characters[1],
@@ -383,6 +384,7 @@ def node_to_str(self, tree, node_id, criterion):
                 node_string += "class = "
             if self.class_names is not True:
                 class_name = self.class_names[np.argmax(value)]
+                class_name = self.str_escape(class_name)
             else:
                 class_name = "y%s%s%s" % (
                     characters[1],
@@ -397,6 +399,9 @@ def node_to_str(self, tree, node_id, criterion):
 
         return node_string + characters[5]
 
+    def str_escape(self, string):
+        return string
+
 
 class _DOTTreeExporter(_BaseTreeExporter):
     def __init__(
@@ -571,6 +576,10 @@ def recurse(self, tree, node_id, criterion, parent=None, depth=0):
                 # Add edge to parent
                 self.out_file.write("%d -> %d ;\n" % (parent, node_id))
 
+    def str_escape(self, string):
+        # override default escaping for graphviz
+        return string.replace('"', r"\"")
+
 
 class _MPLTreeExporter(_BaseTreeExporter):
     def __init__(
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/tree/_export.py`
