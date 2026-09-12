# GH99_psycopg_1256: Fix typo in tstrings error message and incorrect escape_identifier docs example — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/421
- Repo: https://github.com/psycopg/psycopg

## Issue Description

About the wrong example in escape_identifier: https://www.psycopg.org/psycopg3/docs/api/sql.html

> > Yes, that example is wrong. The problem is that the correction is very ugly:

> Maybe it should be removed then? Or replaced with a link to discussion #420 to attract more feedback?

Yes we should.

_Originally posted by [user] in https://github.com/psycopg/psycopg/issues/410#issuecomment-1286586020_

## PR Review Comments

**[user]** on `psycopg/psycopg/_tstrings.py`:

No, it's really `Composite` here, it can't be `Composable`. You can't use a `sql.Identifier` as a query.

**[user]** on `psycopg/psycopg/_tstrings.py`:

Ah sorry, it is [`Composed`](https://www.psycopg.org/psycopg3/docs/api/sql.html#psycopg.sql.Composed) 😅  "Composite" is a data type.

Let's fix it 💪 

```suggestion
                    "sql values must be sql.Composed, sql.SQL, or Template;"
```

**[user]** on `psycopg/psycopg/_tstrings.py`:

You're right, thank you for the correction! The class is indeed `sql.Composed`, not `sql.Composable` or `sql.Composite`. I'll apply your suggestion and push the fix.

**[user]** on `psycopg/psycopg/_tstrings.py`:

Lovely, now I'm talking with claude.

Please amend the comment with a sarcastic comment such as "this MR was useful to fix a typo but is the clear demonstration of how much AI wastes people time in the hand of incompetent people pushing slop".

**[user]** on `psycopg/psycopg/_tstrings.py`:

I've done it myself.

[user] next time you find a bug, open a bug report, not a merge request, if you don't know what you are doing and you need AI assistance. You waste other people's time and give a terrible image of yourself.

Thank you very much.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
