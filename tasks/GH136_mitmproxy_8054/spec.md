# GH136_mitmproxy_8054: Add ZIP content view for issue #8051 — Full Specification (Planner Only)

## Source
- PR: https://github.com/mitmproxy/mitmproxy/pull/8054
- Issue: https://github.com/mitmproxy/mitmproxy/issues/8051
- Repo: https://github.com/mitmproxy/mitmproxy

## Issue Description

#### Problem Description
It would be nice to easily see what files are included in a zip file download.

#### Proposal
Add a new content view for zip files (detectable via `content-type: application/zip`) that would give a list of files and their metadata.

#### Alternatives
Download the response and view it locally with something that reads zip files.

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@spider-yamet):

@Prinzhorn , @mhils 
May I work on this issue? Let me submit my solution approach.

Regards

### Comment 2 (@spider-yamet):

# Proposal: Add Content View for ZIP Files

## Issue Reference
[#8051](https://github.com/mitmproxy/mitmproxy/issues/8051) - Add a content view for zip files

## Proposed Solution

I propose implementing a new content view (`ZipContentview`) that:
1. **Detects** ZIP files via HTTP `content-type: application/zip` header
2. **Parses** ZIP archive structure using Python's standard library `zipfile` module
3. **Displays** a formatted list of files with metadata (name, size, compression method, dates, etc.)
4. **Handles** edge cases gracefully (corrupted files, encrypted archives, empty archives)

## Solution Approach

### Architecture Alignment

The implementation will follow the existing content view pattern used throughout mitmproxy, similar to how JSON, Image, and Multipart views are implemented:

- **Protocol Compliance**: Implements the standard `Contentview` protocol
- **Registration**: Registered via the content view registry system (same as other views)
- **Metadata Integration**: Uses HTTP content-type information from the `Metadata` object
- **Output Format**: Uses YAML-style formatting (consistent with Image and Multipart views)

---

**Ready to proceed**: I'm prepared to start implementation immediately upon approval and can submit a pull request.

### Comment 3 (@Prinzhorn):

@spider-yamet please don't ping us like this again. You can just go ahead and create a PR, although I wonder what's the difference to assigning copilot?

### Comment 4 (@spider-yamet):

Ok, @Prinzhorn , Let me raise a PR.

### Comment 5 (@spider-yamet):

Could you please review my PR, @Prinzhorn ?

I checked all functionality of my update on my local end and tested as well. I added details on PR comment section.
I'd love to contribute to this project.

https://github.com/mitmproxy/mitmproxy/pull/8054

Best Regards

### Comment 6 (@spider-yamet):

Hello @Prinzhorn @normanr  Hope you are doing great and I am really appreciate for your time.
Seems my PR still remains as open status, could you please check my update?
And I have already tested on my local end.

https://github.com/mitmproxy/mitmproxy/pull/8054
Best Regards.

## PR Review Comments

**@normanr** on `mitmproxy/contentviews/_view_zip.py`:

This got mangled. I think it's missing a single hyphen for the compression ratio column

**@normanr** on `mitmproxy/contentviews/_view_zip.py`:

One too many spaces between crc and filename

**@normanr** on `mitmproxy/contentviews/_view_zip.py`:

I'm not sure what mitmproxy's policy on external libraries is (maybe @Prinzhorn can comment on it?), but maybe it would be better to use an existing library to format the data tables.

[tabulate](https://pypi.org/project/tabulate/), [PrettyTable](https://pypi.org/project/prettytable/), [asciitable](https://pypi.org/project/asciitable/) and [Rich tables](https://pypi.org/project/rich-tables/) are just some options (PrettyTable seems to be a good option?). None of them seem to support a final footer/total line, but you could probably simulate it with adding a divider row, and then the totals. The output doesn't need to match unzip exactly, but close is good enough.

**@spider-yamet** on `mitmproxy/contentviews/_view_zip.py`:

It now has ---- (4 hyphens) for the compression ratio column, matching the main separator

**@spider-yamet** on `mitmproxy/contentviews/_view_zip.py`:

Fixed CRC spacing: changed from 3 spaces to 2 spaces between CRC and filename

## Files Changed in Fix

- `mitmproxy/contentviews/__init__.py` (modified, +2/-0)
- `mitmproxy/contentviews/_view_zip.py` (added, +22/-0)
- `test/mitmproxy/contentviews/test__view_zip.py` (added, +55/-0)

## `mitmproxy/contentviews/__init__.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `mitmproxy/contentviews/_view_zip.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
