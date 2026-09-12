# GH626_werkzeug_3081: Correct parsing up to a potential partial boundary — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3065
- Repo: https://github.com/pallets/werkzeug

## Issue Description

The following minimalist flask application and upload code causes a wrongly decoded multipart payload to be saved. The application file `upload.py`  and test case `testcase` are in the attached zip file [reproducer.zip](https://github.com/user-attachments/files/23521331/reproducer.zip).

 - run application: `mkdir upload ; python3 -m flask --app upload.py run -p 32269`
 - upload the test case (from a separate shell, of course): `netcat 127.0.0.1 32269 < testcase`

Behold the fact that the testcase ends in:
```
000100f0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00010100: 0000 0000 0000 000d 0a2d 2d30 3633 6166  .........--063af
00010110: 6334 6362 6534 3661 3734 3035 3930 3938  c4cbe46a74059098
00010120: 3831 3433 3937 3165 3262 642d 2d0d 0a    8143971e2bd--..
```

whereby the *payload* should end with a bunch of zeros.

What happens is that the downloaded file has a stray `\x0d` at the end, leading to a file of length 65432 bytes, while the correct length should be 65431 bytes:
```
0000ff80: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0000ff90: 0000 0000 0000 000d                      ........
```

My understanding of the cause is that the code [here](https://github.com/pallets/werkzeug/blob/main/src/werkzeug/formparser.py#L368-L370) splits the input in chunks of size 65536. Its state machine is updated by what it sees. If the chunk is broken in the middle of the final line break (which is precisely what happens here), the [quite tolerant regexp here](https://github.com/pallets/werkzeug/blob/main/src/werkzeug/sansio/multipart.py#L63-L65) will recognize a single `\n` as a legitimate line break marker, and thus let `\r` be part of the payload.

Environment:
```
>>> import werkzeug
>>> import sys
>>> import importlib
>>> from importlib.metadata import version
>>> sys.version
'3.13.9 (main, Oct 15 2025, 14:56:22) [GCC 15.2.0]'
>>> version('werkzeug')
'3.1.3'
```

This bug was observed in the field with the [cado-nfs software](https://gitlab.inria.fr/cado-nfs/cado-nfs/-/issues/30119) and nailed down by [user].

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Happy to review a PR

### Comment 2 ([user]):

However, that other project needs to stop using the dev server in production. See https://flask.palletsprojects.com/en/stable/deploying/

> When you’re developing locally, you’re probably using the built-in development server, debugger, and reloader. These should not be used in production. Instead, you should use a dedicated WSGI server or hosting platform, some of which will be described here.
>
> “Production” means “not development”, which applies whether you’re serving your application publicly to millions of users or privately / locally to a single user.

### Comment 3 ([user]):

> However, that other project needs to stop using the dev server in production.

Yes, we're aware of it. It's in the works. Thanks for the heads up, though.

### Comment 4 ([user]):

> Happy to review a PR

Here's an attempt with a test. But frankly, it's not my territory. You might prefer an option that refactors some of the existing logic (e.g. around the incomplete boundary detection) in order to also address this issue. Your call.

## PR Review Comments

**[user]** on `src/werkzeug/sansio/multipart.py`:

[user] [user] nitpicky, but: I think `LR` was probably intended to be `LF` in this comment?

```suggestion
        # position of a LF or a CR, unless that position is more
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
