# GH493_boto3_4654: Add Python 3.9 deprecation notice — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

This PR will start emitting warnings when installed on Python 3.9 which reached [official end of support](https://devguide.python.org/versions/) by the Python Software Foundation on October 31, 2025. As previously announced, Boto3 will continue to provide releases for 6 months following upstream end of support to provide an extended migration window for customers. Full details can be found in our [previous blog post](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/).

For customers who can't immediately migrate and wish to suppress these warnings in the interim, [`filter_python_deprecation_warnings()`](https://github.com/boto/boto3/blob/2c7f121cf15aefcedc42dbf59d70cb0a02a07bd1/boto3/compat.py#L48-L58) is available in the `boto3.compat` module. This should be invoked before creating your first boto3 client or session.

## PR Review Comments

**[user]** on `README.rst`:

Just curious, why specifically the 29th?

**[user]** on `README.rst`:

It's the last Wednesday in April, we've always tried to do them midweek. It could be later than that but we're providing the longest window within our previously stated support policy from the PSF EoS date.

**[user]** on `README.rst`:

Nit: it seems a bit odd for us to copy/paste this and link the same blog twice.  

Consider updating to something like this:
```
On 2026-04-29, support for Python 3.9 will end for Boto3. This follows the
Python Software Foundation `end of support <https://peps.python.org/pep-0596/#lifespan>`__
for the runtime which occurred on 2025-10-31.

On 2025-04-22, support for Python 3.8 ended for Boto3. This follows the
Python Software Foundation `end of support <https://peps.python.org/pep-0569/#lifespan>`__
for the runtime which occurred on 2024-10-07.

For more information about AWS SDK Python support policy, see this `blog post <https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/>`__.
```

This appears to match the state [prior to the 3.8 deprecation]((withheld: the upstream fix is not part of the task)files).

**[user]** on `README.rst`:

Whoops, looks like I got this in a bit too late. 

Was non-blocking anyhow.  Thanks for this, Nate :)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
