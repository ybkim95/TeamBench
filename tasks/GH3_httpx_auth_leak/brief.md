# GH3: Fix Credential Leak in HTTP Client Redirects

The HTTP client library leaks sensitive headers when following redirects.
Security audit flagged that credentials may be sent to unintended hosts.

Fix the redirect handling in `httpclient.py` to prevent credential leakage
while preserving correct redirect behavior for same-origin requests.
