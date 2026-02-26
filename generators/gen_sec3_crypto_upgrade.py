"""
Parameterized generator for SEC3: Crypto Upgrade.

Each seed produces:
- Different deprecated crypto scenario (MD5 passwords, DES file encryption,
  RC4 API signing, SHA1 tokens, AES-ECB storage)
- Different application domain (user auth, file vault, API gateway, session mgr)
- Different service/variable naming
- Same TNI pattern: spec has exact migration plan + compatibility matrix +
  ordered steps; brief says "upgrade deprecated crypto"

TNI Design:
  - brief.md: vague — "the app uses deprecated crypto; upgrade it"
  - spec.md: full migration plan with:
      * exact algorithm replacements
      * compatibility matrix (which services need what format)
      * ORDERED migration steps (key derivation → storage → API layer)
  - workspace: looks plausible; deprecated usage subtle (ECB mode, MD5, etc.)
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Variation pools ───────────────────────────────────────────────────────────

# Each scenario picks one dominant deprecated primitive + its replacement
CRYPTO_SCENARIOS = [
    {
        "name": "md5_passwords",
        "deprecated_algo": "MD5",
        "modern_algo": "SHA-256 with PBKDF2",
        "deprecated_import": "hashlib",
        "deprecated_call": "hashlib.md5(password.encode()).hexdigest()",
        "deprecated_pattern": "md5",
        "modern_call": "pbkdf2_hmac",
        "hash_store_field": "password_hash",
        "key_derivation": "PBKDF2",
        "check_name": "password hashing",
    },
    {
        "name": "sha1_tokens",
        "deprecated_algo": "SHA-1",
        "modern_algo": "SHA-256 with HMAC",
        "deprecated_import": "hashlib",
        "deprecated_call": "hashlib.sha1(token.encode()).hexdigest()",
        "deprecated_pattern": "sha1",
        "modern_call": "hmac.new",
        "hash_store_field": "token_hash",
        "key_derivation": "HMAC-SHA256",
        "check_name": "token signing",
    },
    {
        "name": "des_encryption",
        "deprecated_algo": "DES",
        "modern_algo": "AES-256-GCM",
        "deprecated_import": "Crypto.Cipher.DES",
        "deprecated_call": "DES.new(key, DES.MODE_CBC)",
        "deprecated_pattern": "DES",
        "modern_call": "AES.new(key, AES.MODE_GCM)",
        "hash_store_field": "encrypted_blob",
        "key_derivation": "PBKDF2",
        "check_name": "symmetric encryption",
    },
    {
        "name": "rc4_signing",
        "deprecated_algo": "RC4",
        "modern_algo": "HMAC-SHA256",
        "deprecated_import": "Crypto.Cipher.ARC4",
        "deprecated_call": "ARC4.new(key).encrypt(data)",
        "deprecated_pattern": "ARC4|RC4",
        "modern_call": "hmac.new(key, data, hashlib.sha256)",
        "hash_store_field": "signature",
        "key_derivation": "HKDF",
        "check_name": "API request signing",
    },
    {
        "name": "ecb_storage",
        "deprecated_algo": "AES-ECB",
        "modern_algo": "AES-256-GCM",
        "deprecated_import": "Crypto.Cipher.AES",
        "deprecated_call": "AES.new(key, AES.MODE_ECB)",
        "deprecated_pattern": "MODE_ECB",
        "modern_call": "AES.new(key, AES.MODE_GCM)",
        "hash_store_field": "encrypted_data",
        "key_derivation": "PBKDF2",
        "check_name": "data-at-rest encryption",
    },
]

APP_DOMAINS = [
    {
        "name": "user_auth",
        "display": "User Authentication Service",
        "module": "auth_service",
        "primary_object": "user",
        "primary_collection": "users",
        "key_env": "AUTH_SECRET_KEY",
        "storage_label": "user credential store",
        "api_label": "authentication API",
    },
    {
        "name": "file_vault",
        "display": "File Vault Service",
        "module": "vault_service",
        "primary_object": "file",
        "primary_collection": "files",
        "key_env": "VAULT_MASTER_KEY",
        "storage_label": "encrypted file store",
        "api_label": "vault REST API",
    },
    {
        "name": "api_gateway",
        "display": "API Gateway",
        "module": "gateway_service",
        "primary_object": "request",
        "primary_collection": "requests",
        "key_env": "GATEWAY_SIGNING_KEY",
        "storage_label": "request signature cache",
        "api_label": "gateway signing API",
    },
    {
        "name": "session_mgr",
        "display": "Session Manager",
        "module": "session_service",
        "primary_object": "session",
        "primary_collection": "sessions",
        "key_env": "SESSION_SECRET_KEY",
        "storage_label": "session token store",
        "api_label": "session management API",
    },
    {
        "name": "data_store",
        "display": "Encrypted Data Store",
        "module": "store_service",
        "primary_object": "record",
        "primary_collection": "records",
        "key_env": "STORE_ENCRYPTION_KEY",
        "storage_label": "encrypted record store",
        "api_label": "data store API",
    },
]

KEY_SIZES = [16, 24, 32]  # bytes (128, 192, 256-bit)

ITERATION_COUNTS = [100_000, 200_000, 310_000, 480_000, 600_000]


class Generator(TaskGenerator):
    task_id = "SEC3_crypto_upgrade"
    domain = "security"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        scenario = CRYPTO_SCENARIOS[rng.randint(0, len(CRYPTO_SCENARIOS) - 1)]
        domain = APP_DOMAINS[rng.randint(0, len(APP_DOMAINS) - 1)]
        key_size = KEY_SIZES[rng.randint(0, len(KEY_SIZES) - 1)]
        iterations = ITERATION_COUNTS[rng.randint(0, len(ITERATION_COUNTS) - 1)]

        expected = {
            "deprecated_algo": scenario["deprecated_algo"],
            "modern_algo": scenario["modern_algo"],
            "domain": domain["name"],
            "key_derivation": scenario["key_derivation"],
            "migration_order": [
                "key_derivation",
                "storage_layer",
                "api_layer",
            ],
            "backward_compat": True,
            "checks": {
                "no_deprecated_algo": f"No {scenario['deprecated_algo']} usage remains",
                "modern_algo_used": f"{scenario['modern_algo']} is used correctly",
                "key_derivation_correct": f"{scenario['key_derivation']} used for key material",
                "backward_compat": "Old-format data can still be read (migration bridge)",
                "migration_order": "Storage upgraded before API layer",
                "no_raw_hash_as_key": "Raw hash output not used directly as key material",
            },
        }

        workspace_files = {
            "crypto_utils.py": self._gen_crypto_utils(scenario, domain, key_size, iterations),
            "storage.py": self._gen_storage(scenario, domain),
            "api.py": self._gen_api(scenario, domain),
            "migrate.py": self._gen_migrate(scenario, domain),
            "requirements.txt": self._gen_requirements(scenario),
            "tests/test_crypto.py": self._gen_tests(scenario, domain),
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=self._gen_spec(scenario, domain, key_size, iterations),
            brief_md=self._gen_brief(scenario, domain),
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── workspace file generators ─────────────────────────────────────────────

    def _gen_crypto_utils(self, scenario: dict, domain: dict, key_size: int, iterations: int) -> str:
        """Generate the main crypto utilities module with deprecated primitives."""
        s = scenario
        d = domain
        key_env = d["key_env"]

        if s["name"] == "md5_passwords":
            return f'''\
"""Crypto utilities for {d["display"]}."""
import hashlib
import os


# Key loaded from environment
{key_env} = os.environ.get("{key_env}", "default-dev-key-change-in-prod")

SALT_SIZE = 16  # bytes


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    # TODO: migrate to stronger KDF
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    return hash_password(password) == stored_hash


def derive_key(master: str, context: str = "") -> bytes:
    """Derive an encryption key from master secret."""
    combined = (master + context).encode("utf-8")
    # Quick key derivation for now
    return hashlib.md5(combined).digest()  # 16 bytes


def generate_token(user_id: int, secret: str) -> str:
    """Generate a session token."""
    raw = f"{{user_id}}:{{secret}}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()
'''

        elif s["name"] == "sha1_tokens":
            return f'''\
"""Crypto utilities for {d["display"]}."""
import hashlib
import hmac
import os
import secrets


{key_env} = os.environ.get("{key_env}", "default-dev-key-change-in-prod")


def sign_token(data: str, key: str = {key_env}) -> str:
    """Sign a token for integrity verification."""
    # Legacy SHA-1 based signing
    return hashlib.sha1((key + data).encode("utf-8")).hexdigest()


def verify_token(data: str, signature: str, key: str = {key_env}) -> bool:
    """Verify a token signature."""
    expected = sign_token(data, key)
    return expected == signature


def hash_identifier(value: str) -> str:
    """Hash an identifier for indexing."""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def generate_session_id() -> str:
    """Generate a random session ID."""
    return secrets.token_hex(16)


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key from a password."""
    # Simple hash-based derivation
    combined = password.encode() + salt
    return hashlib.sha1(combined).digest()  # 20 bytes
'''

        elif s["name"] == "des_encryption":
            return f'''\
"""Crypto utilities for {d["display"]}."""
import hashlib
import os

from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad


{key_env} = os.environ.get("{key_env}", "default-dev-key-change-in-prod")

DES_KEY_SIZE = 8  # DES uses 8-byte keys


def get_des_key(master_key: str) -> bytes:
    """Derive an 8-byte DES key from the master key."""
    return hashlib.md5(master_key.encode()).digest()[:DES_KEY_SIZE]


def encrypt_data(plaintext: bytes, key: str = {key_env}) -> bytes:
    """Encrypt data using DES-CBC."""
    des_key = get_des_key(key)
    iv = os.urandom(8)
    cipher = DES.new(des_key, DES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, DES.block_size))
    return iv + ciphertext


def decrypt_data(ciphertext_with_iv: bytes, key: str = {key_env}) -> bytes:
    """Decrypt DES-CBC encrypted data."""
    des_key = get_des_key(key)
    iv = ciphertext_with_iv[:8]
    ciphertext = ciphertext_with_iv[8:]
    cipher = DES.new(des_key, DES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), DES.block_size)


def hash_filename(name: str) -> str:
    """Hash a filename for lookup."""
    return hashlib.md5(name.encode()).hexdigest()
'''

        elif s["name"] == "rc4_signing":
            return f'''\
"""Crypto utilities for {d["display"]}."""
import hashlib
import os

from Crypto.Cipher import ARC4


{key_env} = os.environ.get("{key_env}", "default-dev-key-change-in-prod")


def sign_request(payload: bytes, key: str = {key_env}) -> bytes:
    """Sign an API request payload using RC4."""
    # RC4 stream cipher used as signing primitive
    rc4 = ARC4.new(key.encode("utf-8"))
    return rc4.encrypt(payload)


def verify_request(payload: bytes, signature: bytes, key: str = {key_env}) -> bool:
    """Verify a signed API request."""
    expected = sign_request(payload, key)
    return expected == signature


def derive_api_key(master: str, client_id: str) -> bytes:
    """Derive a per-client API key."""
    combined = f"{{master}}:{{client_id}}".encode()
    return hashlib.md5(combined).digest()


def hash_request_id(request_id: str) -> str:
    """Hash a request ID for deduplication."""
    return hashlib.md5(request_id.encode()).hexdigest()
'''

        else:  # ecb_storage
            return f'''\
"""Crypto utilities for {d["display"]}."""
import hashlib
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


{key_env} = os.environ.get("{key_env}", "default-dev-key-change-in-prod")

AES_KEY_SIZE = 16  # AES-128


def get_aes_key(master_key: str) -> bytes:
    """Derive AES key from master key."""
    return hashlib.md5(master_key.encode()).digest()  # 16 bytes for AES-128


def encrypt_record(plaintext: bytes, key: str = {key_env}) -> bytes:
    """Encrypt a record using AES-ECB."""
    aes_key = get_aes_key(key)
    # ECB mode — no IV needed
    cipher = AES.new(aes_key, AES.MODE_ECB)
    return cipher.encrypt(pad(plaintext, AES.block_size))


def decrypt_record(ciphertext: bytes, key: str = {key_env}) -> bytes:
    """Decrypt an AES-ECB encrypted record."""
    aes_key = get_aes_key(key)
    cipher = AES.new(aes_key, AES.MODE_ECB)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


def hash_record_id(record_id: str) -> str:
    """Hash a record ID for indexing."""
    return hashlib.md5(record_id.encode()).hexdigest()
'''

    def _gen_storage(self, scenario: dict, domain: dict) -> str:
        d = domain
        s = scenario
        obj = d["primary_object"]
        coll = d["primary_collection"]
        field = s["hash_store_field"]

        return f'''\
"""Storage layer for {d["display"]}."""
import json
import os
from typing import Optional

from crypto_utils import encrypt_data, decrypt_data, hash_password, derive_key

# In-memory store (replace with DB in production)
_{coll.upper()}_STORE: dict[str, dict] = {{}}


def save_{obj}(record: dict) -> None:
    """Persist a {obj} record."""
    _{coll.upper()}_STORE[record["id"]] = record


def load_{obj}(record_id: str) -> Optional[dict]:
    """Retrieve a {obj} record by id."""
    return _{coll.upper()}_STORE.get(record_id)


def list_{coll}() -> list[dict]:
    """List all {coll} (non-sensitive fields)."""
    return [
        {{k: v for k, v in r.items() if k != "{field}"}}
        for r in _{coll.upper()}_STORE.values()
    ]


def delete_{obj}(record_id: str) -> bool:
    """Remove a {obj} record."""
    if record_id in _{coll.upper()}_STORE:
        del _{coll.upper()}_STORE[record_id]
        return True
    return False


def {obj}_exists(record_id: str) -> bool:
    """Check if a {obj} record exists."""
    return record_id in _{coll.upper()}_STORE
'''

    def _gen_api(self, scenario: dict, domain: dict) -> str:
        d = domain
        s = scenario
        obj = d["primary_object"]
        coll = d["primary_collection"]

        return f'''\
"""API layer for {d["display"]}."""
from flask import Blueprint, jsonify, request

from crypto_utils import (
    hash_password,
    verify_password,
    generate_token,
    derive_key,
)
from storage import save_{obj}, load_{obj}, list_{coll}

bp = Blueprint("api", __name__)


@bp.route("/api/{coll}", methods=["POST"])
def create_{obj}():
    """Create a new {obj}."""
    body = request.get_json(force=True) or {{}}
    record_id = body.get("id")
    if not record_id:
        return jsonify({{"error": "id required"}}), 400

    # Store with hashed/encrypted sensitive field
    record = dict(body)
    if "password" in record:
        record["password_hash"] = hash_password(record.pop("password"))

    save_{obj}(record)
    return jsonify({{"status": "created", "id": record_id}}), 201


@bp.route("/api/{coll}/<record_id>", methods=["GET"])
def get_{obj}(record_id: str):
    """Retrieve a {obj}."""
    record = load_{obj}(record_id)
    if record is None:
        return jsonify({{"error": "not found"}}), 404
    # Exclude sensitive fields
    safe = {{k: v for k, v in record.items() if "hash" not in k and "encrypt" not in k}}
    return jsonify(safe)


@bp.route("/api/{coll}", methods=["GET"])
def list_{obj}s():
    """List all {coll}."""
    return jsonify({{"data": list_{coll}()}})
'''

    def _gen_migrate(self, scenario: dict, domain: dict) -> str:
        s = scenario
        d = domain
        obj = d["primary_object"]
        coll = d["primary_collection"]

        return f'''\
"""
Migration script: upgrade deprecated crypto for {d["display"]}.

Migration order (MUST follow this sequence per spec):
  1. key_derivation  — upgrade key derivation first (PBKDF2/scrypt/HMAC)
  2. storage_layer   — re-encrypt/re-hash stored data with new primitives
  3. api_layer       — update API verification to use new primitives

Backward compatibility: old-format records must still be readable during migration.
"""
import hashlib
import os
from typing import Optional


# ── Step 1: Key derivation upgrade ───────────────────────────────────────────

def migrate_key_derivation(master_key: str, salt: bytes) -> bytes:
    """
    DEPRECATED: was using raw MD5/SHA1 as key derivation.
    TODO: Replace with PBKDF2/scrypt/argon2.
    """
    # Old (insecure) approach — kept for backward compat during migration
    return hashlib.md5(master_key.encode()).digest()


# ── Step 2: Storage layer migration ─────────────────────────────────────────

def migrate_{obj}_record(record: dict) -> dict:
    """
    Re-encrypt/re-hash a {obj} record from old format to new format.
    Must maintain backward compat: old_format field preserved until cutover.
    """
    migrated = dict(record)
    # TODO: apply new crypto here (step 2)
    migrated["_migrated"] = False  # placeholder
    return migrated


def migrate_storage() -> dict:
    """
    Migrate all {coll} records in the storage layer.
    Returns migration summary.
    """
    # TODO: iterate over all {coll} and apply migrate_{obj}_record
    return {{"migrated": 0, "failed": 0, "skipped": 0}}


# ── Step 3: API layer migration ───────────────────────────────────────────────

def update_api_verification() -> bool:
    """
    Switch API verification to use new crypto primitives.
    Must only run AFTER storage migration is complete.
    """
    # TODO: update API layer after storage is ready
    return False


# ── Entry point ───────────────────────────────────────────────────────────────

def run_migration() -> None:
    """
    Execute migration in correct order:
    key_derivation → storage → api
    """
    print("[1/3] Migrating key derivation...")
    # TODO: implement

    print("[2/3] Migrating storage layer...")
    result = migrate_storage()
    print(f"  Storage: {{result}}")

    print("[3/3] Updating API verification layer...")
    success = update_api_verification()
    print(f"  API layer updated: {{success}}")


if __name__ == "__main__":
    run_migration()
'''

    def _gen_requirements(self, scenario: dict) -> str:
        s = scenario
        base = "Flask>=2.3.0\npycryptodome>=3.19.0\n"
        if s["name"] in ("md5_passwords", "sha1_tokens"):
            # hashlib is stdlib, but add cryptography for modern approach
            return base + "cryptography>=41.0.0\n"
        return base + "cryptography>=41.0.0\n"

    def _gen_tests(self, scenario: dict, domain: dict) -> str:
        s = scenario
        d = domain
        obj = d["primary_object"]

        return f'''\
"""Tests for {d["display"]} crypto utilities."""
import pytest
from crypto_utils import *


class TestCryptoUtils:
    """Basic smoke tests for crypto primitives."""

    def test_round_trip_basic(self):
        """Verify that encrypt/decrypt or hash/verify round-trips."""
        # This test verifies the interface; the underlying primitive
        # must be upgraded from {s["deprecated_algo"]}
        pass  # TODO: implement after migration

    def test_deprecated_algo_not_used(self):
        """Verify deprecated algorithm is no longer in use."""
        import inspect
        import crypto_utils
        source = inspect.getsource(crypto_utils)
        # Deprecated pattern must not appear in final implementation
        # {s["deprecated_algo"]} must be replaced with {s["modern_algo"]}
        pass  # Grader checks this via static analysis

    def test_key_derivation_is_modern(self):
        """Key derivation must use PBKDF2, scrypt, or argon2 — not raw hashes."""
        pass  # TODO: verify derive_key uses proper KDF

    def test_backward_compat_bridge(self):
        """Old-format data must still be readable during migration."""
        pass  # TODO: test migration bridge reads old-format correctly
'''

    # ── doc generators ────────────────────────────────────────────────────────

    def _gen_spec(self, scenario: dict, domain: dict, key_size: int, iterations: int) -> str:
        s = scenario
        d = domain
        key_bits = key_size * 8

        return f"""\
# SEC3: Crypto Upgrade — Migration Specification (Planner/Verifier Only)

## Overview

The **{d["display"]}** currently uses **{s["deprecated_algo"]}** for {s["check_name"]}.
This primitive is cryptographically broken and must be replaced with **{s["modern_algo"]}**.

This document contains the full migration plan, compatibility matrix, and ORDERED steps.
The Executor's brief omits this detail — it only says to "upgrade deprecated crypto."

---

## Deprecated Primitive Analysis

| Property | Value |
|----------|-------|
| Current algorithm | `{s["deprecated_algo"]}` |
| Location | `crypto_utils.py` |
| Vulnerability | Collision attacks / insufficient key space / no authenticated encryption |
| Data at risk | `{d["storage_label"]}` |
| API surface affected | `{d["api_label"]}` |

---

## Target Architecture

| Layer | Current | Target |
|-------|---------|--------|
| Key derivation | Raw MD5/SHA1 hash | **{s["key_derivation"]}** with salt + {iterations:,} iterations |
| {s["check_name"]} | `{s["deprecated_algo"]}` | `{s["modern_algo"]}` |
| Key size | Reduced (≤128-bit effective) | **{key_bits}-bit** |
| Authentication | None / broken | **Authenticated encryption (AEAD)** where applicable |

---

## Compatibility Matrix

The following consumers depend on the current crypto format and must be updated
in the order listed. Updating out of order WILL break production.

| Priority | Component | Depends On | Action |
|----------|-----------|-----------|--------|
| 1 (FIRST) | Key derivation module | Nothing | Replace raw hash with `{s["key_derivation"]}` |
| 2 | Storage layer (`storage.py`) | Key derivation (step 1) | Re-encrypt/re-hash stored data; add backward-compat read bridge |
| 3 (LAST) | API layer (`api.py`) | Storage migration complete | Switch verification to new primitives |

**Breaking change rule**: The API layer MUST NOT be updated before the storage layer.
If `api.py` is migrated first, existing records in the storage layer become unreadable
because the old-format data cannot be verified with new primitives.

---

## Migration Order (MANDATORY)

### Step 1 — Key Derivation (`crypto_utils.py`: `derive_key`)

Replace raw MD5/SHA1 hash with **{s["key_derivation"]}**:

```python
# BEFORE (broken):
key = hashlib.md5(master.encode()).digest()

# AFTER (required):
import hashlib
key = hashlib.pbkdf2_hmac(
    "sha256",
    password=master.encode("utf-8"),
    salt=salt,           # random 16-byte salt, stored alongside derived key
    iterations={iterations},
    dklen={key_size},    # {key_bits}-bit key
)
```

**Constraint**: `derive_key()` must never use raw hash output as key material.
Key material MUST come from a proper KDF (PBKDF2, scrypt, or argon2).

### Step 2 — Storage Layer (`storage.py`, `crypto_utils.py`)

After step 1 is complete:

1. Update `{s["deprecated_call"]}` → `{s["modern_call"]}` in `crypto_utils.py`
2. Add a **backward-compat read bridge** so old-format records can still be read:
   - Old records: identified by absence of `_v2` flag or presence of `_legacy` field
   - New records: tagged with `"_crypto_version": 2`
3. Re-encrypt/re-hash existing records using the new primitive
4. The function `migrate_storage()` in `migrate.py` must actually perform this migration

**Do NOT touch `api.py` until this step is complete.**

### Step 3 — API Layer (`api.py`)

Only after step 2 is verified:

1. Update verification calls in `api.py` to use new primitives from `crypto_utils.py`
2. Update `update_api_verification()` in `migrate.py` to return `True`
3. The API must handle both old-format and new-format during the migration window

---

## Verification Criteria

The Verifier must confirm ALL of the following:

1. **No deprecated algorithm**: `{s["deprecated_algo"]}` (`{s["deprecated_pattern"]}`) does not appear
   in `crypto_utils.py` in any active (non-comment) code path
2. **Modern algorithm used**: `{s["modern_algo"]}` is correctly applied in `crypto_utils.py`
3. **Key derivation correct**: `derive_key()` uses `{s["key_derivation"]}` — NOT raw `md5()` or `sha1()` output
4. **Key size adequate**: derived key is at least {key_bits} bits ({key_size} bytes)
5. **Backward compat**: old-format data can still be read (migration bridge present in `storage.py` or `crypto_utils.py`)
6. **Migration order correct**: `migrate.py` runs key_derivation → storage → api (in that order)
7. **Authenticated encryption**: if AES is used, it MUST be GCM or CCM mode (NOT ECB, NOT plain CBC)
8. **No raw hash as key**: key material never derives directly from `md5()` or `sha1()` output
9. **Tests pass**: `tests/test_crypto.py` imports successfully and basic assertions hold
10. **No regression**: `api.py` endpoints still present and functional after migration

---

## Deliverables

The Executor must:
- Update `crypto_utils.py` with modern primitives (steps 1 & 2)
- Update `storage.py` with backward-compat bridge (step 2)
- Update `api.py` to use new primitives (step 3)
- Complete the migration stubs in `migrate.py`

The Planner must ensure the Executor follows the mandatory migration order.
"""

    def _gen_brief(self, scenario: dict, domain: dict) -> str:
        s = scenario
        d = domain
        return f"""\
# SEC3: Crypto Upgrade (Executor Brief)

The **{d["display"]}** has been flagged for using deprecated cryptographic functions.
Upgrade the crypto implementation. The Planner has the full migration plan.

**Your workspace contains**:
- `crypto_utils.py` — cryptographic utility functions
- `storage.py` — data persistence layer
- `api.py` — REST API endpoints
- `migrate.py` — migration script (stubs to complete)
- `requirements.txt` — Python dependencies
- `tests/test_crypto.py` — test suite

The application uses deprecated cryptographic functions. Upgrade them.
Do not remove backward compatibility for existing data.
"""
