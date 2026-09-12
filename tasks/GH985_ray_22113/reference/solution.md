# Reference solution — GH985_ray_22113

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH985_ray_22113`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH985_ray_22113/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/actor.py` (modified, +24/-3)
- `python/ray/tests/test_actor.py` (modified, +20/-1)

## Diff Summary (What the Fix Changes)

### `python/ray/actor.py`
```diff
@@ -343,6 +343,10 @@ def __init__(
         )
 
 
+class ActorClassInheritanceException(TypeError):
+    pass
+
+
 class ActorClass:
     """An actor class.
 
@@ -360,11 +364,15 @@ def __init__(cls, name, bases, attr):
         use the '_ray_from_modified_class' classmethod.
 
         Raises:
-            TypeError: Always.
+            ActorClassInheritanceException: When ActorClass is inherited.
+            AssertionError: If ActorClassInheritanceException is not raised i.e.,
+                            conditions for raising it are not met in any
+                            iteration of the loop.
+            TypeError: In all other cases.
         """
         for base in bases:
             if isinstance(base, ActorClass):
-                raise TypeError(
+                raise ActorClassInheritanceException(
                     f"Attempted to define subclass '{name}' of actor "
                     f"class '{base.__ray_metadata__.class_name}'. "
                     "Inheriting from actor classes is "
@@ -430,7 +438,20 @@ def _ray_from_modified_class(
         # Make sure the actor class we are constructing inherits from the
         # original class so it retains all class properties.
         class DerivedActorClass(cls, modified_class):
-            pass
+            def __init__(self, *args, **kwargs):
+                try:
+                    cls.__init__(self, *args, **kwargs)
+                except Exception as e:
+                    # Delegate call to modified_class.__init__ only
+                    # if the exception raised by cls.__init__ is
+                    # TypeError and not ActorClassInheritanceException(TypeError).
+                    # In all other cases proceed with raise e.
+                    if isinstance(e, TypeError) and not isinstance(
+                        e, ActorClassInheritanceException
+                    ):
+                        modified_class.__init__(self, *args, **kwargs)
+                    else:
+      
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/actor.py`
