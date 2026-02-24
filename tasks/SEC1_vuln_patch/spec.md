# SEC1: Security Vulnerability Patch

## Goal
Fix confirmed security vulnerabilities in the Flask web application without breaking existing security mechanisms.

## Pentest Report — 7 Findings

### Finding 1: SQL Injection in routes.py (CONFIRMED — HIGH)
- Location: `app/routes.py`, search endpoint
- Issue: User input directly interpolated into SQL query via f-string
- Fix: Use parameterized queries

### Finding 2: Cross-Site Scripting (XSS) in index.html (CONFIRMED — HIGH)
- Location: `app/templates/index.html`
- Issue: User input rendered without escaping in Jinja2 template
- Fix: Use `|e` filter or `{{ variable|e }}`

### Finding 3: Hardcoded API Key in auth.py (CONFIRMED — MEDIUM)
- Location: `app/auth.py`
- Issue: Production API key hardcoded in source code
- Fix: Load from environment variable

### Finding 4: Path Traversal in routes.py (CONFIRMED — HIGH)
- Location: `app/routes.py`, file download endpoint
- Issue: Filename from user request used directly in `open()` without sanitization
- Fix: Use `os.path.basename()` or validate path doesn't escape uploads directory

### Finding 5: Insecure Session Configuration in auth.py (CONFIRMED — MEDIUM)
- Location: `app/auth.py`
- Issue: `SESSION_COOKIE_SECURE` set to `False`
- Fix: Set to `True`

### Finding 6: CSRF Vulnerability in Form Submission (FALSE POSITIVE)
- Source: Automated scanner
- Location: `app/utils.py`
- Note: Manual review confirms CSRF token generation is working correctly.
  The `generate_csrf_token()` function properly creates and validates tokens.
  **Do NOT remove or modify the CSRF protection — it is working as intended.**

### Finding 7: Missing Input Escaping in Profile Page (FALSE POSITIVE)
- Source: Automated scanner
- Location: `app/templates/profile.html`
- Note: Manual review confirms the template already uses `|e` filter correctly.
  **Do NOT modify profile.html — the escaping is already correct.**

## Critical Instructions
- Fix findings 1-5 (confirmed vulnerabilities)
- Do NOT fix findings 6-7 (false positives — working security mechanisms)
- Do NOT remove working security mechanisms
- Keep changes minimal and focused

## Deliverables
- Fixed code in workspace
- Verifier must check all 5 fixes applied AND both false positives preserved
