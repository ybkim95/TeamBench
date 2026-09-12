# GH4: Fix JSON Response Encoding Detection — Full Specification

## Background

The `requests` library (and this simplified implementation) has a bug in how it
handles character encoding for JSON HTTP responses. This leads to corrupted
(garbled) text when the response body contains non-ASCII characters and the
server does not explicitly specify a charset in the `Content-Type` header.

This was a real issue: see https://github.com/psf/requests/issues/6587

---

## RFC 8259 — The Standard

**RFC 8259 §8.1** (The JavaScript Object Notation (JSON) Data Interchange Format):

> JSON text exchanged between systems that are not part of a closed ecosystem
> MUST be encoded using UTF-8.
>
> Implementations MUST NOT add a byte order mark (BOM) to the beginning of a
> networked-transmitted JSON text.
>
> Since the first two characters of a JSON text will always be ASCII
> characters, it is possible to determine whether an octet stream is UTF-8,
> UTF-16 (BE or LE), or UTF-32 (BE or LE) by looking at the pattern of nulls
> in the first four octets.

Key implication: **No `charset` parameter is defined for `application/json`.**
When a server sends `Content-Type: application/json` with no `charset=`, the
correct interpretation per RFC 8259 is UTF-8 — not "unknown, use detection."

---

## Root Cause

In `http_response.py`, the `text` property works as follows:

1. Call `_parse_content_type` to extract the `charset` from the
   `Content-Type` header.
2. If a `charset` was found, use it to decode `self.content`.
3. **If no charset was found**, fall back to `self.apparent_encoding` — a
   heuristic that inspects the raw bytes using chardet/charset_normalizer.

Step 3 is the bug. For `application/json` responses, there is no charset
in the header (servers correctly omit it per RFC 8259), so the code falls
through to the heuristic detector.

The heuristic (`apparent_encoding`) is unreliable for short JSON payloads
because UTF-8 encoded Latin characters (é, ñ, ü, etc.) produce byte
sequences that are also valid ISO-8859-1 / Windows-1252. Heuristic detectors
frequently mis-identify such content as ISO-8859-1, resulting in garbled text:

- UTF-8 bytes `0xC3 0xA9` = "é" in UTF-8, but "Ã©" in ISO-8859-1
- UTF-8 bytes `0xC3 0xB1` = "ñ" in UTF-8, but "Ã±" in ISO-8859-1
- UTF-8 bytes `0xE5 0x8C 0x97` = "北" in UTF-8, but three garbage chars in ISO-8859-1

---

## The Fix

In the `text` property (or the `encoding` property), add a check:

**If the MIME type from `Content-Type` starts with `application/json` AND no
explicit charset was provided, default to `"utf-8"` instead of falling back
to `apparent_encoding`.**

Pseudocode:

```python
@property
def text(self):
    enc = self.encoding  # charset from Content-Type header, or None
    if enc is None:
        mime_type, _ = self._parse_content_type(
            self.headers.get("content-type", "")
        )
        if mime_type == "application/json":
            enc = "utf-8"   # RFC 8259: JSON MUST be UTF-8
        else:
            enc = self.apparent_encoding  # heuristic fallback for non-JSON
    return self.content.decode(enc, errors="replace")
```

---

## What Must NOT Change

1. **`_parse_content_type` is correct.** Do not modify how the Content-Type
   header is parsed. It correctly extracts the mime type and any explicit
   charset parameter.

2. **`apparent_encoding` must not be removed.** Non-JSON content types
   (e.g., `text/html`, `text/plain`) legitimately rely on charset detection
   as a fallback. The heuristic must remain in place and continue to be used
   for non-JSON responses.

3. **Explicit charset always wins.** If a server sends
   `Content-Type: application/json; charset=utf-16`, that explicit charset
   must be respected (it will be, because the fix only applies when
   `self.encoding` is `None`).

4. **`json()` method should not be modified** — it calls `self.text`, so
   fixing `text` automatically fixes `json()`.

---

## Test Cases Summary

| Test | Content-Type | Body encoding | Expected behavior |
|------|-------------|---------------|-------------------|
| `test_json_utf8_default` | `application/json` | UTF-8 | Fix: use UTF-8, not detection |
| `test_json_with_charset` | `application/json; charset=utf-8` | UTF-8 | Already works (explicit charset) |
| `test_json_chinese` | `application/json` | UTF-8 (Chinese) | Fix: use UTF-8, not detection |
| `test_html_uses_detection` | `text/html` | latin-1 | Must still use detection |
| `test_json_method_works` | `application/json` | UTF-8 | Fix: `json()` returns correct dict |
| `test_content_type_parsing` | various | — | `_parse_content_type` unchanged |

---

## Files to Modify

- `workspace/http_response.py` — fix the `text` property encoding logic

Do NOT modify `workspace/test_encoding.py`.
