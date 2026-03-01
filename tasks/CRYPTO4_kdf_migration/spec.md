# CRYPTO4: Password Hash Migration

## Goal
Migrate the password hashing system from MD5 to Argon2id while maintaining backward
compatibility with all existing users.

## Requirements
1. New users must receive Argon2id hashes (not MD5)
2. Existing users with any of the 3 legacy hash formats must be able to authenticate
3. On successful login with a legacy hash, the hash must be transparently upgraded to Argon2id
4. The format marker must be updated correctly when upgrading a hash
5. The hex-encoded salt used in legacy format 1 (salted MD5) must be handled correctly
6. All tests must pass: `pytest tests/`

## Legacy Hash Formats (in database)
- Format 0 (plain MD5): `md5:<hex_hash>` — no salt, just MD5 of password
- Format 1 (salted MD5): `md5s:<hex_salt>:<hex_hash>` — MD5 with hex-encoded salt
- Format 2 (SHA256-HMAC): `sha256h:<b64_salt>:<b64_hash>` — HMAC-SHA256 with base64 salt
- Format 3 (Argon2id): `argon2:$argon2id$...` — new format

## Known Bugs (find and fix them)
See `auth_system/migrator.py` and `auth_system/verifier.py` for the bugs described in
the supporting documentation. The format marker bug and hex-salt handling bug are subtle
and will cause cascading failures if not fixed.

## Real-World Context
MD5→Argon2 migrations with backward compatibility are a recurring real-world challenge:
- **WordPress trac #39499 (2017)**: Proposed migrating from 8,192-round salted MD5
  (phpass) to Argon2i. The transparent upgrade-on-login pattern (authenticate with old
  hash, re-hash with Argon2 on success) is the industry standard for zero-downtime
  migrations without forcing password resets.
- **Keycloak KDF upgrade**: Migrating from PBKDF2-SHA1 to Argon2id required format
  markers and multi-format verifiers — identical to the format-marker bug in this task.
- **The hex-salt bug** mirrors a real Django migration issue where legacy `md5(password
  + salt)` stored the salt as hex in the database, but the migration code decoded it
  as base64, producing incorrect hashes for all legacy users.
