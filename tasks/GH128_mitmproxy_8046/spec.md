# GH128_mitmproxy_8046: Fix modify_body crash when replacement contains backslash sequences — Full Specification (Planner Only)

## Source
- PR: https://github.com/mitmproxy/mitmproxy/pull/8046
- Issue: https://github.com/mitmproxy/mitmproxy/issues/7579
- Repo: https://github.com/mitmproxy/mitmproxy

## Issue Description

### Problem Description

#### System Information
OS: Arch Linux
Kernel: Linux 6.13.4-arch1-1
Architecture: x86_64

#### Bug
When setting the `modify_body` variable via mitmweb, using an escape character (`\`) causes an exception to be thrown, failing to modify the request.

#### Error Message
```
Addon error: bad escape \u at position 1
Traceback (most recent call last):
  File "/usr/lib/python3.13/site-packages/mitmproxy/addons/modifybody.py", line 63, in response
    self.run(flow)
    ~~~~~~~~^^^^^^
  File "/usr/lib/python3.13/site-packages/mitmproxy/addons/modifybody.py", line 74, in run
    flow.response.content = re.sub(
                            ~~~~~~^
        spec.subject,
        ^^^^^^^^^^^^^
    ...<2 lines>...
        flags=re.DOTALL,
        ^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/lib/python3.13/re/__init__.py", line 208, in sub
    return _compile(pattern, flags).sub(repl, string, count)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.13/re/__init__.py", line 377, in _compile_template
    return _sre.template(pattern, _parser.parse_template(repl, pattern))
                                  ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/usr/lib/python3.13/re/_parser.py", line 1076, in parse_template
    raise s.error('bad escape %s' % this, len(this)) from None
re.PatternError: bad escape \u at position 1
```

#### Steps to reproduce the behavior:
1. Start mitmweb
2. Open options and set `modify_body` to use an escape character (eg. /~all/foo/bar\u003 or #~all#foo#bar\u003)
3. Request is not modified and error is thrown in output

### System Information

```raw
Mitmproxy: 11.1.0
Python:    3.13.2
OpenSSL:   OpenSSL 3.4.1 11 Feb 2025
Platform:  Linux-6.13.4-arch1-1-x86_64-with-glibc2.41
```

### Checklist

- [x] This bug affects the [latest mitmproxy release](https://github.com/mitmproxy/mitmproxy/releases).

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@Penguin-Terminal):

Unfortunately, the [mitmproxy pacman package](https://archlinux.org/packages/extra/any/mitmproxy/) is still on v11.1.0. I have not had the chance to test it on v11.1.3, however I didn't see any issues or pull requests related to this bug.

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `mitmproxy/addons/modifybody.py` (modified, +5/-2)
- `test/mitmproxy/addons/test_modifybody.py` (modified, +20/-0)

## `mitmproxy/addons/modifybody.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
