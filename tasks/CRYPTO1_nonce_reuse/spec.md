# CRYPTO1: AES-GCM Encryption Service

## Goal
The encryption service must implement AES-256-GCM correctly per CRYPTO_SPEC.md.

## Requirements
1. Nonces must be 96-bit (12 bytes) and cryptographically random — not counter-based
2. Key derivation must use PBKDF2 with >= 100,000 iterations
3. GCM authentication tag must be full 16 bytes — no truncation
4. Salt generation using `os.urandom()` is already correct — do not modify it

## Supporting Documents
- `CRYPTO_SPEC.md`: Full cryptographic requirements with rationale
- `crypto_service/nonce.py`: Nonce generation (has counter-based bug)
- `crypto_service/key_derivation.py`: KDF (has iteration count bug)
- `crypto_service/encryption.py`: Encrypt/decrypt (has tag truncation bug)
- `crypto_service/utils.py`: Salt generation (CORRECT, do not change)

## Important
The basic encrypt/decrypt round-trip tests will pass even with the bugs — the service
is functionally correct but cryptographically weak. The adversarial tests in
`tests/test_nonce_collision.py`, `tests/test_key_strength.py`, and
`tests/test_tag_integrity.py` catch the actual vulnerabilities.

## Real-World Context
These bugs reflect vulnerabilities documented in production systems:
- **Nonce reuse (Bug 1)**: Internet-wide scanning (Joux 2006; Böck et al. 2016,
  "Nonce-Disrespecting Adversaries") found 184 HTTPS servers reusing AES-GCM nonces,
  allowing full plaintext recovery and authentication key extraction.
- **Weak KDF (Bug 2)**: PBKDF2 with 1,000 iterations is breakable in minutes with
  commodity GPUs. OWASP recommends ≥ 600,000 iterations for PBKDF2-SHA256 (2023).
- **Truncated tag (Bug 3)**: CVE-2022-21449-style truncation of authentication tags
  reduces forgery resistance from 2^128 to 2^64, enabling birthday attacks at scale.
