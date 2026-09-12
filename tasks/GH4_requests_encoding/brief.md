# GH4: Fix JSON Response Encoding Detection

The HTTP response library incorrectly detects encoding for JSON responses,
causing corrupted text for non-ASCII characters. Users report garbled
output when parsing JSON responses containing Unicode text.

Fix the encoding detection in `http_response.py`.
