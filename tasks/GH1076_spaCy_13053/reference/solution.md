# Reference solution — GH1076_spaCy_13053

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1076_spaCy_13053`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1076_spaCy_13053/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/cli/__init__.py` (modified, +11/-2)
- `spacy/cli/project/__init__.py` (added, +0/-0)
- `spacy/cli/project/assets.py` (added, +1/-0)
- `spacy/cli/project/clone.py` (added, +1/-0)
- `spacy/cli/project/document.py` (added, +1/-0)
- `spacy/cli/project/dvc.py` (added, +1/-0)
- `spacy/cli/project/pull.py` (added, +1/-0)
- `spacy/cli/project/push.py` (added, +1/-0)
- `spacy/cli/project/remote_storage.py` (added, +1/-0)
- `spacy/cli/project/run.py` (added, +1/-0)
- `spacy/tests/test_cli.py` (modified, +5/-0)

## Diff Summary (What the Fix Changes)

### `spacy/cli/__init__.py`
```diff
@@ -22,8 +22,17 @@
 from .package import package  # noqa: F401
 from .pretrain import pretrain  # noqa: F401
 from .profile import profile  # noqa: F401
-from .train import train_cli  # noqa: F401
-from .validate import validate  # noqa: F401
+from .project.assets import project_assets  # type: ignore[attr-defined]  # noqa: F401
+from .project.clone import project_clone  # type: ignore[attr-defined]  # noqa: F401
+from .project.document import (  # type: ignore[attr-defined]  # noqa: F401
+    project_document,
+)
+from .project.dvc import project_update_dvc  # type: ignore[attr-defined]  # noqa: F401
+from .project.pull import project_pull  # type: ignore[attr-defined]  # noqa: F401
+from .project.push import project_push  # type: ignore[attr-defined]  # noqa: F401
+from .project.run import project_run  # type: ignore[attr-defined]  # noqa: F401
+from .train import train_cli  # type: ignore[attr-defined]  # noqa: F401
+from .validate import validate  # type: ignore[attr-defined]  # noqa: F401
 
 
 @app.command("link", no_args_is_help=True, deprecated=True, hidden=True)
```

### `spacy/cli/project/assets.py`
```diff
@@ -0,0 +1 @@
+from weasel.cli.assets import *
```

### `spacy/cli/project/clone.py`
```diff
@@ -0,0 +1 @@
+from weasel.cli.clone import *
```

### `spacy/cli/project/document.py`
```diff
@@ -0,0 +1 @@
+from weasel.cli.document import *
```

### `spacy/cli/project/dvc.py`
```diff
@@ -0,0 +1 @@
+from weasel.cli.dvc import *
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `spacy/cli/__init__.py`
- `spacy/cli/project/__init__.py`
- `spacy/cli/project/assets.py`
- `spacy/cli/project/clone.py`
- `spacy/cli/project/document.py`
