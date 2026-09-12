# GH291_bookwyrm_3710: book: fix validation for 979 prefixed isbn-13 and isbn_13_to_10 function — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/bookwyrm-social/bookwyrm/issues/1234
- Repo: https://github.com/bookwyrm-social/bookwyrm

## Issue Description

Fix for #1225 
Uses inline CSS to change the white-space attribute of the text. Code is injected around the string during the HTML sanitation process so that it avoids being detected and striped by the HTMLParser, while still preserving the integrity of the Parser. By using the "data" tag it ensures the code will remain in place, even if the Parser determines any HTML tags in the original string should be removed.

Please let me know if there's a better way to do this, if I've missed any unforeseen consequences by making this change, or if there's a potential risk that this may be abused. Thank you :purple_heart:

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'm not sure it makes sense to modify the html on the fly, as opposed to changing the static css (https://github.com/bookwyrm-social/bookwyrm/blob/main/bookwyrm/static/css/bookwyrm.css) that applies to the elements that wrap the injected html for statuses and bios.

### Comment 2 ([user]):

Okay, I redid it and edited the CSS this time!
Also sorry for the mess of commits, I'm kinda brand new to Github :dizzy_face:

### Comment 3 ([user]):

Heck yeah

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
