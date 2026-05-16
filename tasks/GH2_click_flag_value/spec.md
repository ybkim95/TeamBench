# GH2: Fix Optional Flag Value in CLI Parser — Full Specification

## Source
GitHub Issue: https://github.com/pallets/click/issues/3084
Fixed by PR: https://github.com/pallets/click/pull/3152

## Problem Description

In Click 8.3.0, a regression was introduced in `Option.consume_value()`. An option
defined with `is_flag=False` and `flag_value="some_value"` stopped working correctly.

### Expected Behavior

```python
# Option defined as:
Option("--verbose", is_flag=False, flag_value="DEBUG")

# Parsing behavior:
# --verbose          → value is "DEBUG"  (use flag_value)
# --verbose INFO     → value is "INFO"   (explicit value overrides flag_value)
# --verbose=WARNING  → value is "WARNING" (= syntax works)
# (no flag)          → value is None     (use default)
```

### Actual Behavior (Buggy)

```
# --verbose file.txt
# verbose = "file.txt"   ← WRONG: consumed positional arg
# filename = <missing>   ← WRONG: positional arg was stolen
```

## Root Cause

In `_consume_option_value()` within the `Parser` class, the logic for deciding
whether to consume the next token as the option's value is:

```python
# BUGGY CODE (current):
if not opt.is_flag:
    # consume next argument as value
    value = remaining_args.pop(0)
else:
    # use flag_value or True
    value = opt.flag_value if opt.flag_value is not None else True
```

The problem: when `is_flag=False` AND `flag_value` is set, the condition `not opt.is_flag`
is `True`, so the code falls into the first branch and consumes the next argument.

### The Fix

The condition must also check whether `flag_value` is set:

```python
# FIXED CODE:
if not opt.is_flag and opt.flag_value is None:
    # regular value-taking option: consume next argument
    value = remaining_args.pop(0)
else:
    # boolean flag OR optional-flag: use flag_value (or True for pure booleans)
    value = opt.flag_value if opt.flag_value is not None else True
```

This is exactly the change made in Click PR #3152.

## Constraints (Do NOT Change)

1. **Tokenizer/lexer code**: The tokenization of `--flag=value` into `(flag, value)` pairs
   is correct and must not be modified. The `=` sign split happens before `_consume_option_value()`.

2. **Boolean flag behavior**: `is_flag=True, flag_value=None` must still set the option to `True`.

3. **Help generation**: `Command.format_help()` must remain functional.

4. **Regular options**: Options with `is_flag=False, flag_value=None` must still consume
   the next argument as their value.

## Downstream Impact

- **MkDocs** uses `--verbose` as an optional-flag-value option. The regression broke
  all MkDocs verbose logging configuration since Click 8.3.0.
- Any CLI tool using the `flag_value` parameter with `is_flag=False` is affected.

## Files

- `cli_parser.py` — the parser to fix (look for `_consume_option_value`)
- `test_cli.py` — test suite; all tests must pass after the fix
