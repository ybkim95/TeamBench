# GH5: Pydantic Circular Reference Bug — Full Specification

## Issue Description

Source: https://github.com/pydantic/pydantic/issues/6394

A data validation library (`validator.py`) correctly handles flat models and
non-recursive nested models, but silently drops all fields when validating
self-referential (recursive) models such as a tree node with `children`.

### Reproduction

```python
from validator import Model, TreeNode

data = {
    "name": "root", "value": 1, "children": [
        {"name": "child", "value": 2, "children": [
            {"name": "grandchild", "value": 3, "children": []}
        ]}
    ]
}
result = TreeNode.model_validate(data)
print(result.children[0].name)  # prints "" — should be "child"
```

Depth 1 and 2 work correctly, but depth 3+ silently returns raw dicts
instead of model instances, losing attribute access.

---

## Root Cause

In `_build_model_instance()`, there is a recursion depth guard for list
fields containing model types. The guard was added to prevent infinite
recursion on malformed circular data, but the threshold is set too low:

```python
if _depth < 2:
    kwargs[field.name] = [
        _build_model_instance(item_type, v, item_schema, _depth + 1)
        ...
    ]
else:
    # Return raw dicts beyond the depth limit
    kwargs[field.name] = value
```

The `_depth` counter increments with each level of nesting. At depth 2
(grandchild level), the guard kicks in and returns raw dicts instead of
constructing model instances. This means:
- Root (depth 0) → built correctly
- Children (depth 1) → built correctly
- Grandchildren (depth 2) → their `children` field gets raw dicts, not
  model instances
- Accessing `.name` on a raw dict raises `AttributeError`

### The Fix

The depth guard threshold of 2 is too conservative. Either:
1. **Remove the depth guard entirely** — Python's default recursion limit
   (1000) provides sufficient protection against truly infinite recursion.
2. **Raise the threshold** to a reasonable value like 50 or 100.
3. **Replace with cycle detection** — track seen object IDs instead of
   using a blanket depth limit.

The simplest correct fix is to remove the `_depth < 2` guard (or change it
to a much higher limit), allowing `_build_model_instance` to recurse freely
for all valid tree depths.

### What must NOT change

- `validate_field` for primitive types (`str`, `int`, `float`, `bool`) is
  **correct** and must not be modified.
- Non-recursive model validation (e.g. `Person` with a nested `Address`) must
  continue to work exactly as before.
- The `SchemaResolver` class must remain in `validator.py`.
- No use of `eval` or `exec` is permitted.

---

## Acceptance Criteria

1. `test_simple_model` — non-recursive nested model validates correctly.
2. `test_recursive_depth_1` — single level of self-reference validates correctly.
3. `test_recursive_depth_3` — depth-3 tree preserves all node names and values.
4. `test_wide_recursive` — multiple children at each level all validate correctly.
5. `test_primitive_validation` — `SchemaResolver.resolve_type(str)` returns a valid schema.
6. `test_non_recursive_nested` — `Person → Address` nesting unaffected.
