# CRYPTO2: Timing-Safe Secret Comparisons

## Goal
Fix timing side-channel vulnerabilities in the authentication system's secret comparisons.

## Requirements
1. All secret comparisons must use constant-time comparison functions
2. Non-secret comparisons (public data lookups) must NOT be changed
3. All functional tests must pass after changes: `pytest tests/`
4. See `SECURITY_REQUIREMENTS.md` for which comparisons are secret-bearing

## Supporting Documents
- `auth/api_keys.py`: API key validation (secret comparison)
- `auth/signatures.py`: HMAC signature verification (secret comparison)
- `auth/passwords.py`: Password hash comparison (secret comparison)
- `auth/sessions.py`: Session token validation (secret comparison)
- `auth/users.py`: Username lookup (NOT secret — plain == is correct here)
- `SECURITY_REQUIREMENTS.md`: Documents which comparisons need timing safety

## Important
NOT all string comparisons need to be constant-time. A username is a public identifier;
timing differences in username lookup do not leak secret information. Changing the username
lookup to use `hmac.compare_digest` is security theater and will cause issues.
Only comparisons involving secrets (keys, signatures, hashes, tokens) need fixing.

## Real-World Context
Timing side-channel vulnerabilities in authentication are well-documented in production:
- **Django ticket #14445 (2010)**: Django's CSRF token comparison used `==`, leaking
  token bytes one at a time via response-time differences. Fixed by introducing
  `crypto.constant_time_compare()` in Django 1.4.
- **PyJWT issue #7 (2013)**: HMAC signature verification used Python's `==` operator,
  enabling remote timing oracle attacks against JWT-authenticated APIs.
- **CVE-2022-48566**: Python's HMAC library timing properties under CPython optimization;
  `hmac.compare_digest()` is the standard fix (PEP 466, Python 3.4+).
- **CVE-2025-59058** (httpsig-rs): Timing attack on HTTP signature verification in Rust,
  CVSS 7.5 — constant-time comparison missed in one code path.
