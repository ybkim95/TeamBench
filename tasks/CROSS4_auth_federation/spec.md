# CROSS4: Authentication Federation Gateway

## Goal
Fix 5 security bugs in the authentication gateway that integrates Service A (JWT tokens)
and Service B (HMAC API keys).

## Requirements
1. JWT validation must require RS256 algorithm — reject all other algorithms (especially HS256)
2. API key comparison must use constant-time comparison to prevent timing attacks
3. Role mapping must include all roles from both auth systems
4. Session tokens must expire — set expiry to 3600 seconds
5. JWT validation must verify the `aud` (audience) claim matches the service

## Supporting Documents
- `gateway/auth.py` — Auth validation (contains bugs 1, 2, 4, 5)
- `gateway/rbac.py` — Role mapping (contains bug 3)
- `service_a/keys/` — RSA key pair for JWT verification
- `service_b/secrets.py` — HMAC shared secret
- `tests/attack_vectors.py` — Documents known attack vectors for each bug

## Security Requirements (all mandatory)
- RS256 ONLY: Rejecting HS256 prevents algorithm confusion attacks (CVSS 9.8)
- Constant-time: `hmac.compare_digest` prevents timing-based API key extraction
- Non-zero expiry: Session tokens that never expire allow indefinite impersonation
- Audience validation: Prevents token reuse across services
- Complete role mapping: Missing roles cause authorization failures

## Real-World Context
All five bugs appear in documented CVEs and security advisories:
- **Bug 1 (JWT algorithm confusion)**: CVE-2023-48223 (fast-jwt npm, GHSA-c2ff-88x2-x9pg)
  and CVE-2026-27804 (Parse Server, complete account takeover via `alg: none` or
  HS256 confusion, CVSS 9.8). Auth0's 2015 post "Critical vulnerabilities in JWT libraries"
  documented this class across 6 major libraries. Fix: hardcode `algorithms=['RS256']`.
- **Bug 2 (timing attack on API keys)**: Same class as CVE-2025-59058 (httpsig-rs, CVSS
  7.5) and Django ticket #14445. Non-constant-time comparison leaks key bytes byte-by-byte.
- **Bug 3 (incomplete role mapping)**: Authorization failures from missing role coverage
  are a common misconfiguration in federated auth systems (OWASP Broken Access Control).
- **Bug 4 (no session expiry)**: CWE-613 (Insufficient Session Expiration). Sessions
  without expiry allow indefinite impersonation after token theft.
- **Bug 5 (missing audience validation)**: CVE-2017-8932 class — JWT tokens issued for
  service A accepted by service B when `aud` claim is not verified (CVSS 7.5).
