# Analysis Guidance for Expertise-Asymmetry Condition

## Recommended Analysis Tools
- `cd /workspace && mypy app/ --ignore-missing-imports --strict 2>&1` — primary type checker
- `mypy app/ --ignore-missing-imports 2>&1` — less strict, shows same errors
- `find /workspace/app -name "*.py"` — list files

## Expected Findings (15 errors)
- `app/models.py`: 3 errors (Any type, missing return annotation, bare list)
- `app/service.py`: 5 errors (missing annotations, wrong literal type, return mismatch)
- `app/utils.py`: 4 errors (missing annotations, bare Dict)
- `app/dynamic.py`: 3 errors (dynamic dispatch, any-return, operator)

## Intentional Dynamic Patterns (require suppression, NOT code changes)
Three locations in `app/dynamic.py` use genuinely dynamic Python patterns that cannot
be fully typed without changing the design. These need suppression, not refactoring:
- `app/dynamic.py` line ~10: dynamic `getattr` dispatch
- `app/dynamic.py` line ~22: plugin registry heterogeneous return
- `app/dynamic.py` line ~31: runtime callable invocation

## Key Distinction
12 errors need real code fixes (add type annotations, fix literal types, fix return values).
3 locations in `app/dynamic.py` need suppression — NOT code changes.

## CRITICAL: The Unused-Ignore Trap
**If the dynamic.py parameters are typed as `Any`, mypy will NOT report errors at those
locations — making `# type: ignore` comments become "unused-ignore" errors under `--strict`.**

Two valid approaches to suppress these without triggering unused-ignore:
1. **Use `cast()`**: `return cast(ReturnType, plugin_registry[key])` — no type:ignore needed
2. **Use specific non-Any types** that genuinely conflict, then add `# type: ignore[...]`

Approach 1 (`cast()`) is often simpler and avoids the unused-ignore problem entirely.
Do NOT tell the executor to add `# type: ignore` blindly — check whether the parameter
types are `Any` first. If they are `Any`, recommend `cast()` instead.
