# GH548_ruff_14098: [refurb] Parse more exotic decimal strings in `verbose-decimal-constructor (FURB157)` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/astral-sh/ruff/issues/13807
- Repo: https://github.com/astral-sh/ruff

## Issue Description

<!--
Thank you for taking the time to report an issue! We're glad to have you involved with Ruff.

If you're filing a bug report, please consider including the following information:

* List of keywords you searched for before creating this issue. Write them down here so that others can find this issue more easily and help provide feedback.
  e.g. "RUF001", "unused variable", "Jupyter notebook"
* A minimal code snippet that reproduces the bug.
* The command you invoked (e.g., `ruff /path/to/file.py --fix`), ideally including the `--isolated` flag.
* The current Ruff settings (any relevant sections from your `pyproject.toml`).
* The current Ruff version (`ruff --version`).
-->

```python
Decimal(1000)  # OK
Decimal(1_000)  # OK
Decimal("1000")  # Triggers FURB157
Decimal("1_000")  # Should trigger FURB157 and become Decimal(1_000), but it doesn't
```

ruff v0.7.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

It seems like the parsing we do here is too naive: https://github.com/astral-sh/ruff/blob/4ecfe95295eb203ba771f344f52c8e61527a4c05/crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs#L77-L98

### Comment 2 ([user]):

If there are more edge cases that we don't handle, it might be worth just using `ruff_python_parser::parse_expression` to determine if the contents of the string can be parsed as an `int` literal, rather than reimplementing all the edge cases in the linter. If this is the only edge case we don't currently handle, however, it may be best to avoid doing that and just reimplement the logic in the linter -- using the `ruff_python_parser` function might be comparatively quite expensive.

### Comment 3 ([user]):

`Decimal` accepts more integer-valued strings than are valid as `int` literals. For example, `Decimal("1__2")` and `Decimal("_1_")` and `Decimal("١٢٣")` are valid. Should FURB157 trigger on those? If so, `ruff_python_parser::parse_expression` would not be enough.

### Comment 4 ([user]):

Looks like this is the official regex: 

https://github.com/python/cpython/blob/322f14eeff9e3b5853eaac3233f7580ca0214cf8/Lib/_pydecimal.py#L6059-L6077

I can try to take this sometime this weekend (but if I don't, others should feel free to go for it!)

### Comment 5 ([user]):

The fix in latest ruff (v0.13.1) converts `Decimal("1_000")` to `Decimal(1000)` instead of to `Decimal(1_000)`.

It becomes more problematic for bigger values, where thousand formatting really helps to read a number, like `Decimal(15_000_000)`.

Can the issue be reopened?

## PR Review Comments

**[user]** on `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs`:

Nit: I don't think `memchr` gives us much here, considering that most literals are very short. We also don't have to use `replace` and allcoate a `Cow::Owned`. Instead, I would use `Cow::from(trimmed.trim_start_matches('_'))` for better readability (with the added benefit that it doesn't allocate)

**[user]** on `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs`:

`replace` is technically `O(n)`. Not that it matters much here but I think I would find it slightly more readable if we explicitly tested for the `+` sign and the expected position.

```
if rest[index + 1] == b'+' {
    rest.into_owned().remove(index + 1)
}
```

The alternative is to use `remove_matches` which captures the semantic better than `repalce` with a empty string

**[user]** on `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs`:

It seems that the exponential syntax also supports negative numbers:

https://github.com/astral-sh/ruff/blob/51a998306a10aab1254740f760efaecc25213d71/crates/ruff_python_parser/src/lexer.rs#L1088-L1100

**[user]** on `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs`:

Does this support `1_2_3_4`? or `1.1_2_3_4`?

**[user]** on `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs`:

I don't think the positive sign in the exponent is a syntax error?
```pycon
>>> 2e+3
2000.0
>>> Decimal(2e+3)
Decimal('2000')
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
