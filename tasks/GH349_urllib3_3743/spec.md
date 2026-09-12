# GH349_urllib3_3743: Handle massive values in Retry-After when calculating time to sleep for — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/urllib3/urllib3

## PR Description

The method `Retry.parse_retry_after(...)` will accept any integer returned by the remote server in the `Retry-After` header when the server returns a number of seconds to delay for rather than an HTTP-date. This includes massive and invalid values, for example `Retry-After: 9999999999`. This value is passed back to `Retry.sleep_for_retry(...)` which then uses the value directly in `time.sleep(...)`. The type is checked but not the value.

Using values for `time.sleep(...)` that exceed `PyTime_MAX` results in an OverflowError being raised:

```python
>>> time.sleep(9999999999)
Traceback (most recent call last):
  File "<python-input-3>", line 1, in <module>
    time.sleep(9999999999)
    ~~~~~~~~~~^^^^^^^^^^^^
OverflowError: timestamp too large to convert to C PyTime_t
```

This minimal PR adds a sanity check to confirm that the value of the `Retry-After` header is < 2147483647 (2 ** 31 - 1) in value. While `PyTime_MAX` is a `INT64_MAX` this is still a relatively sane upper bound value. If the value exceeds 2147483647 a clearer and more descriptive exception is raised.

This issue was seen in the wild:

https://github.com/meeb/whoisit/issues/60

It's highly unlikely that actually sleeping for decades or centuries is desirable but that's a different issue. I don't believe there's a specified sensible maximum for `Retry-After` in the RFC, perhaps limiting this to `3600` or similar lower value would be sensible?

Currently, even with this PR, a semi-malicious server could add `if ($http_user_agent ~ urllib3) { add_header retry-after 5000000000; }` and lock up some clients that attempt to handle retries properly for over a century (or at least until the process gets killed).

## PR Review Comments

**[user]** on `src/urllib3/util/retry.py`:

I don't like magic numbers. Can we set it as a `t.Final[int]` at the module level and calculate it as `2**(32-1) - 1` or at least explain that's how it's calculated here. 32bit doesn't mean much to most folks writing python as they won't understand if its signed or unsigned. Alternatively, leave a comment explaining why we "must" set it ourselves here. And use a more humane way of writing the number, e.g., `2_147_483_648`

**[user]** on `src/urllib3/util/retry.py`:

Please move it to be the last parameter to keep the signature of `__init__` compatible with previous versions

**[user]** on `src/urllib3/util/retry.py`:

Also, we'll need to document the parameter in the Retry docstring, the description will appear in the docs
https://urllib3--3743.org.readthedocs.build/en/3743/reference/urllib3.util.html#urllib3.util.Retry

**[user]** on `test/test_retry.py`:

Let's test it without the argument

```suggestion
        retry = Retry()
```

**[user]** on `src/urllib3/util/retry.py`:

When the comments are in the current order, the constant doesn't appear in the docs for some reason
https://urllib3--3743.org.readthedocs.build/en/3743/reference/urllib3.util.html#urllib3.util.Retry

```suggestion
    # This is undocumented in the RFC. Setting to 6 hours matches other popular libraries.
    #: Default maximum allowed value for Retry-After headers in seconds
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
