"""
Parameterized generator for SEC5: Secrets Rotation.

Each seed produces:
- Different service type (web_app, microservice, worker, scheduler)
- Different set of 4-6 hardcoded secrets scattered across multiple files
- Different vault backend (env_vars, json_vault, config_service)
- Different vault API paths and key naming conventions
- Same migration pattern but varied secret types and files

TNI Design (Pattern A,F):
  - brief.md: vague — "remove hardcoded secrets from the application"
  - spec.md: exact vault API contract (endpoints, auth method, key naming),
             required rotation ORDER (db creds first, then API keys, then certs),
             which secrets map to which vault paths
  - workspace: Python app with secrets hardcoded across 4-6 files
  - Breaking the rotation order causes simulated downtime (checked in grade)
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Service type variation pools ──────────────────────────────────────────────

SERVICE_TYPES = [
    {
        "name": "web_app",
        "label": "Web Application",
        "module": "app",
        "entrypoint": "server.py",
        "description": "Flask web application serving REST APIs",
    },
    {
        "name": "microservice",
        "label": "Microservice",
        "module": "service",
        "entrypoint": "main.py",
        "description": "Async microservice handling background jobs",
    },
    {
        "name": "worker",
        "label": "Worker Process",
        "module": "worker",
        "entrypoint": "worker.py",
        "description": "Queue-based worker processing tasks",
    },
    {
        "name": "scheduler",
        "label": "Scheduler",
        "module": "scheduler",
        "entrypoint": "scheduler.py",
        "description": "Cron-style task scheduler running periodic jobs",
    },
]

# ── Vault backend variation pools ─────────────────────────────────────────────

VAULT_BACKENDS = [
    {
        "name": "env_vars",
        "label": "Environment Variables Vault",
        "client_class": "EnvVaultClient",
        "client_module": "vault_client",
        "init_snippet": "vault = EnvVaultClient(prefix=VAULT_PREFIX)",
        "get_method": "get_secret",
        "auth_method": "token",
        "auth_header": "X-Vault-Token",
        "base_url": "http://vault.internal:8200",
        "secret_path_prefix": "secret/data",
        "description": "Reads secrets from environment variables with a configurable prefix",
    },
    {
        "name": "json_vault",
        "label": "JSON File Vault",
        "client_class": "JsonVaultClient",
        "client_module": "vault_client",
        "init_snippet": "vault = JsonVaultClient(vault_path=VAULT_PATH)",
        "get_method": "read",
        "auth_method": "token",
        "auth_header": "X-Vault-Token",
        "base_url": "http://vault.internal:8200",
        "secret_path_prefix": "kv/data",
        "description": "Reads secrets from a JSON vault file with path-based lookup",
    },
    {
        "name": "config_service",
        "label": "Config Service Vault",
        "client_class": "ConfigServiceClient",
        "client_module": "vault_client",
        "init_snippet": "vault = ConfigServiceClient(endpoint=VAULT_ENDPOINT, token=VAULT_TOKEN)",
        "get_method": "fetch",
        "auth_method": "bearer",
        "auth_header": "Authorization",
        "base_url": "http://config.internal:8500",
        "secret_path_prefix": "config/secrets",
        "description": "Reads secrets from a remote config service via HTTP API",
    },
]

# ── Secret type variation pools ───────────────────────────────────────────────

SECRET_GROUPS = [
    # Group 0: DB + API key + JWT + SMTP
    {
        "secrets": [
            {
                "type": "db_password",
                "var_name": "DB_PASSWORD",
                "hardcoded_value": "Sup3rS3cr3tDbPass!",
                "vault_path": "database/credentials",
                "vault_key": "password",
                "rotation_order": 1,
                "file": "database.py",
                "description": "PostgreSQL database password",
            },
            {
                "type": "db_user",
                "var_name": "DB_USER",
                "hardcoded_value": "prod_admin",
                "vault_path": "database/credentials",
                "vault_key": "username",
                "rotation_order": 1,
                "file": "database.py",
                "description": "PostgreSQL database username",
            },
            {
                "type": "api_key",
                "var_name": "PAYMENT_API_KEY",
                "hardcoded_value": "pk_live_abc123XYZ456def789",
                "vault_path": "external/payment",
                "vault_key": "api_key",
                "rotation_order": 2,
                "file": "payments.py",
                "description": "Payment gateway API key",
            },
            {
                "type": "jwt_secret",
                "var_name": "JWT_SECRET",
                "hardcoded_value": "my-super-secret-jwt-key-do-not-share",
                "vault_path": "auth/jwt",
                "vault_key": "secret",
                "rotation_order": 2,
                "file": "auth.py",
                "description": "JWT signing secret",
            },
            {
                "type": "smtp_password",
                "var_name": "SMTP_PASSWORD",
                "hardcoded_value": "EmailP@ssw0rd2024",
                "vault_path": "email/smtp",
                "vault_key": "password",
                "rotation_order": 3,
                "file": "mailer.py",
                "description": "SMTP server password for email delivery",
            },
        ]
    },
    # Group 1: DB + encryption key + webhook secret + S3
    {
        "secrets": [
            {
                "type": "db_password",
                "var_name": "DATABASE_PASSWORD",
                "hardcoded_value": "Pr0dDB$ecret99",
                "vault_path": "database/credentials",
                "vault_key": "password",
                "rotation_order": 1,
                "file": "db.py",
                "description": "MySQL database password",
            },
            {
                "type": "db_host",
                "var_name": "DATABASE_HOST",
                "hardcoded_value": "prod-db-01.internal",
                "vault_path": "database/credentials",
                "vault_key": "host",
                "rotation_order": 1,
                "file": "db.py",
                "description": "Database host address",
            },
            {
                "type": "encryption_key",
                "var_name": "ENCRYPTION_KEY",
                "hardcoded_value": "AES256-key-abcdef1234567890abcdef12",
                "vault_path": "crypto/keys",
                "vault_key": "aes_key",
                "rotation_order": 2,
                "file": "crypto.py",
                "description": "AES-256 encryption key for data at rest",
            },
            {
                "type": "api_key",
                "var_name": "WEBHOOK_SECRET",
                "hardcoded_value": "whsec_live_XYZ789abc012def345ghi",
                "vault_path": "external/webhooks",
                "vault_key": "secret",
                "rotation_order": 2,
                "file": "webhooks.py",
                "description": "Webhook signing secret",
            },
            {
                "type": "api_key",
                "var_name": "S3_SECRET_KEY",
                "hardcoded_value": "wJalrXUtnFEMI/K7MDENG/bPxRfiCY",
                "vault_path": "external/s3",
                "vault_key": "secret_key",
                "rotation_order": 3,
                "file": "storage.py",
                "description": "AWS S3 secret access key",
            },
        ]
    },
    # Group 2: DB + OAuth + signing cert + monitoring token
    {
        "secrets": [
            {
                "type": "db_password",
                "var_name": "POSTGRES_PASSWORD",
                "hardcoded_value": "pgS3cur3Pass#2024",
                "vault_path": "database/postgres",
                "vault_key": "password",
                "rotation_order": 1,
                "file": "models.py",
                "description": "PostgreSQL connection password",
            },
            {
                "type": "db_url",
                "var_name": "DATABASE_URL",
                "hardcoded_value": "postgresql://admin:pgS3cur3Pass#2024@prod-db:5432/myapp",
                "vault_path": "database/postgres",
                "vault_key": "url",
                "rotation_order": 1,
                "file": "models.py",
                "description": "Full database connection URL",
            },
            {
                "type": "api_key",
                "var_name": "OAUTH_CLIENT_SECRET",
                "hardcoded_value": "oauth_secret_abc123def456ghi789",
                "vault_path": "auth/oauth",
                "vault_key": "client_secret",
                "rotation_order": 2,
                "file": "oauth.py",
                "description": "OAuth2 client secret",
            },
            {
                "type": "encryption_key",
                "var_name": "SIGNING_KEY",
                "hardcoded_value": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkq...\n-----END PRIVATE KEY-----",
                "vault_path": "pki/signing",
                "vault_key": "private_key",
                "rotation_order": 3,
                "file": "signing.py",
                "description": "RSA private key for document signing",
            },
            {
                "type": "api_key",
                "var_name": "MONITORING_TOKEN",
                "hardcoded_value": "mon_tok_xyz9876abc5432def",
                "vault_path": "monitoring/tokens",
                "vault_key": "api_token",
                "rotation_order": 3,
                "file": "metrics.py",
                "description": "Monitoring platform API token",
            },
        ]
    },
    # Group 3: DB + Redis + Stripe + Twilio
    {
        "secrets": [
            {
                "type": "db_password",
                "var_name": "MYSQL_PASSWORD",
                "hardcoded_value": "Mysql$ecret!Prod",
                "vault_path": "database/mysql",
                "vault_key": "password",
                "rotation_order": 1,
                "file": "repository.py",
                "description": "MySQL database password",
            },
            {
                "type": "db_password",
                "var_name": "REDIS_PASSWORD",
                "hardcoded_value": "Redis@Auth2024!",
                "vault_path": "database/redis",
                "vault_key": "password",
                "rotation_order": 1,
                "file": "cache.py",
                "description": "Redis auth password",
            },
            {
                "type": "api_key",
                "var_name": "STRIPE_SECRET_KEY",
                "hardcoded_value": "sk_live_51NqBkL2eZvKYlo2CXYZabc123",
                "vault_path": "external/stripe",
                "vault_key": "secret_key",
                "rotation_order": 2,
                "file": "billing.py",
                "description": "Stripe payment secret key",
            },
            {
                "type": "api_key",
                "var_name": "TWILIO_AUTH_TOKEN",
                "hardcoded_value": "ac1234567890abcdef1234567890abcd",
                "vault_path": "external/twilio",
                "vault_key": "auth_token",
                "rotation_order": 2,
                "file": "sms.py",
                "description": "Twilio SMS auth token",
            },
            {
                "type": "encryption_key",
                "var_name": "DATA_ENCRYPTION_KEY",
                "hardcoded_value": "fernet-key-base64-abc123XYZ456def789",
                "vault_path": "crypto/data",
                "vault_key": "fernet_key",
                "rotation_order": 3,
                "file": "encryption.py",
                "description": "Fernet symmetric encryption key",
            },
        ]
    },
]

# ── App name prefixes for variety ─────────────────────────────────────────────

APP_NAMES = [
    "Nexus", "Apex", "Vantage", "Stratus", "Meridian",
    "Cortex", "Helix", "Prism", "Vertex", "Beacon",
]


class Generator(TaskGenerator):
    task_id = "SEC5_secrets_rotation"
    domain = "security"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        svc = SERVICE_TYPES[rng.randint(0, len(SERVICE_TYPES) - 1)]
        vault = VAULT_BACKENDS[rng.randint(0, len(VAULT_BACKENDS) - 1)]
        group = SECRET_GROUPS[rng.randint(0, len(SECRET_GROUPS) - 1)]
        app_name = APP_NAMES[rng.randint(0, len(APP_NAMES) - 1)]

        secrets = group["secrets"]

        # Compute rotation order groups
        order1 = [s for s in secrets if s["rotation_order"] == 1]
        order2 = [s for s in secrets if s["rotation_order"] == 2]
        order3 = [s for s in secrets if s["rotation_order"] == 3]

        # Unique files that contain secrets
        secret_files = sorted(set(s["file"] for s in secrets))

        expected = {
            "service_type": svc["name"],
            "vault_backend": vault["name"],
            "vault_client_class": vault["client_class"],
            "secrets_count": len(secrets),
            "secret_files": secret_files,
            "rotation_order": {
                "phase_1": [s["var_name"] for s in order1],
                "phase_2": [s["var_name"] for s in order2],
                "phase_3": [s["var_name"] for s in order3],
            },
            "vault_paths": {
                s["var_name"]: f"{vault['secret_path_prefix']}/{s['vault_path']}"
                for s in secrets
            },
            "no_hardcoded_secrets": True,
            "vault_initialized_before_secrets": True,
        }

        workspace_files = self._gen_workspace(svc, vault, secrets, app_name)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=self._gen_spec(svc, vault, secrets, app_name, order1, order2, order3),
            brief_md=self._gen_brief(svc, secrets, app_name),
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── workspace file generators ─────────────────────────────────────────────

    def _gen_workspace(self, svc: dict, vault: dict, secrets: list, app_name: str) -> dict:
        files: dict[str, str] = {}

        # config.py — app-level config referencing vault (scaffold, currently empty)
        files["config.py"] = self._gen_config(svc, vault, app_name)

        # vault_client.py — vault client stub (agents must implement real fetching)
        files["vault_client.py"] = self._gen_vault_client_stub(vault)

        # requirements.txt
        files["requirements.txt"] = self._gen_requirements(svc)

        # Generate per-secret-file files
        file_to_secrets: dict[str, list] = {}
        for s in secrets:
            file_to_secrets.setdefault(s["file"], []).append(s)

        for fname, fsecrets in file_to_secrets.items():
            files[fname] = self._gen_secret_file(fname, fsecrets, svc, vault)

        # Entrypoint — imports all secret files, initialises vault
        files[svc["entrypoint"]] = self._gen_entrypoint(svc, vault, secrets, app_name, file_to_secrets)

        # Test file
        files["tests/test_secrets.py"] = self._gen_tests(svc, vault, secrets)

        return files

    def _gen_config(self, svc: dict, vault: dict, app_name: str) -> str:
        if vault["name"] == "env_vars":
            vault_init = 'VAULT_PREFIX = "APP_SECRET"'
        elif vault["name"] == "json_vault":
            vault_init = 'VAULT_PATH = "/etc/vault/secrets.json"'
        else:
            vault_init = (
                'VAULT_ENDPOINT = "http://config.internal:8500"\n'
                'VAULT_TOKEN = "s.xyzABCdef123"  # bootstrap token only'
            )

        return f'''\
"""
{app_name} {svc["label"]} — Application Configuration

Vault backend: {vault["label"]}
{vault["description"]}
"""
import os

APP_NAME = "{app_name}"
SERVICE_TYPE = "{svc["name"]}"
ENVIRONMENT = os.environ.get("APP_ENV", "production")

# Vault configuration
{vault_init}
'''

    def _gen_vault_client_stub(self, vault: dict) -> str:
        cls = vault["client_class"]
        method = vault["get_method"]
        auth_header = vault["auth_header"]
        base_url = vault["base_url"]

        if vault["name"] == "env_vars":
            return f'''\
"""
Vault client — reads secrets from environment variables.

Usage:
    vault = {cls}(prefix="APP_SECRET")
    password = vault.{method}("database/credentials", "password")
    # Looks up env var: APP_SECRET_DATABASE_CREDENTIALS_PASSWORD
"""
import os


class {cls}:
    """Read secrets from environment variables with a configurable prefix."""

    def __init__(self, prefix: str = ""):
        self._prefix = prefix.upper().rstrip("_")

    def _env_key(self, path: str, key: str) -> str:
        """Convert vault path + key to env var name."""
        parts = path.replace("/", "_").replace("-", "_").upper()
        k = key.replace("-", "_").upper()
        return f"{{self._prefix}}_{{parts}}_{{k}}" if self._prefix else f"{{parts}}_{{k}}"

    def {method}(self, path: str, key: str) -> str:
        """Read a secret from environment variables."""
        env_key = self._env_key(path, key)
        value = os.environ.get(env_key)
        if value is None:
            raise KeyError(f"Secret not found: {{env_key}}")
        return value
'''

        elif vault["name"] == "json_vault":
            return f'''\
"""
Vault client — reads secrets from a JSON vault file.

Usage:
    vault = {cls}(vault_path="/etc/vault/secrets.json")
    password = vault.{method}("database/credentials", "password")

Vault file format:
    {{
      "database/credentials": {{"username": "...", "password": "..."}},
      "external/payment": {{"api_key": "..."}},
      ...
    }}
"""
import json
import os


class {cls}:
    """Read secrets from a JSON file with path-based lookup."""

    def __init__(self, vault_path: str):
        self._vault_path = vault_path
        self._cache: dict = {{}}

    def _load(self) -> dict:
        if not self._cache:
            with open(self._vault_path, "r") as f:
                self._cache = json.load(f)
        return self._cache

    def {method}(self, path: str, key: str) -> str:
        """Read a secret from the vault file."""
        data = self._load()
        if path not in data:
            raise KeyError(f"Vault path not found: {{path}}")
        section = data[path]
        if key not in section:
            raise KeyError(f"Key not found in {{path}}: {{key}}")
        return section[key]
'''

        else:  # config_service
            return f'''\
"""
Vault client — reads secrets from a remote config service.

Usage:
    vault = {cls}(endpoint="http://config.internal:8500", token="s.xyz")
    password = vault.{method}("database/credentials", "password")

API contract:
    GET {base_url}/config/secrets/{{path}}
    {auth_header}: Bearer {{token}}

    Response:
        200 OK
        {{"data": {{"username": "...", "password": "..."}}}}
"""
import urllib.request
import urllib.error
import json


class {cls}:
    """Read secrets from a remote config service via HTTP API."""

    def __init__(self, endpoint: str, token: str):
        self._endpoint = endpoint.rstrip("/")
        self._token = token
        self._cache: dict = {{}}

    def {method}(self, path: str, key: str) -> str:
        """Fetch a secret from the config service."""
        if path in self._cache:
            section = self._cache[path]
        else:
            url = f"{{self._endpoint}}/config/secrets/{{path}}"
            req = urllib.request.Request(url)
            req.add_header("{auth_header}", f"Bearer {{self._token}}")
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = json.loads(resp.read())
                section = body.get("data", {{}})
                self._cache[path] = section
            except urllib.error.HTTPError as e:
                raise KeyError(f"Vault request failed for {{path}}: {{e.code}}")
        if key not in section:
            raise KeyError(f"Key not found in {{path}}: {{key}}")
        return section[key]
'''

    def _gen_secret_file(self, fname: str, fsecrets: list, svc: dict, vault: dict) -> str:
        """Generate a Python module with hardcoded secrets."""
        module_name = fname.replace(".py", "")
        imports = "import os\n"

        # Build hardcoded secret assignments
        secret_lines = []
        for s in fsecrets:
            val = s["hardcoded_value"]
            # For multi-line values (private keys) use triple-quote
            if "\n" in val:
                secret_lines.append(f'# {s["description"]}\n{s["var_name"]} = """{val}"""')
            else:
                secret_lines.append(f'# {s["description"]}\n{s["var_name"]} = "{val}"')

        secrets_block = "\n\n".join(secret_lines)

        # Build a usage function for each module type
        usage = self._gen_module_usage(module_name, fsecrets, svc)

        return f'''\
"""
{svc["label"]} — {module_name} module.

TODO: These hardcoded secrets must be migrated to the vault.
"""
{imports}

# ── Hardcoded secrets (MUST be removed) ──────────────────────────────────────
{secrets_block}


{usage}
'''

    def _gen_module_usage(self, module_name: str, fsecrets: list, svc: dict) -> str:
        """Generate plausible usage code for each module."""
        if module_name in ("database", "db", "models", "repository"):
            s = fsecrets[0]
            return f'''\
def get_connection():
    """Return a database connection using the configured credentials."""
    import sqlite3  # Using sqlite3 as a stand-in for the real DB driver
    # In production this uses {s["var_name"]} to authenticate
    conn = sqlite3.connect(":memory:")
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    return conn
'''
        elif module_name in ("auth", "oauth"):
            s = fsecrets[0]
            return f'''\
import hmac, hashlib


def sign_token(payload: str) -> str:
    """Sign a token using the JWT secret."""
    secret = {s["var_name"]}.encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def verify_token(payload: str, signature: str) -> bool:
    """Verify a token signature."""
    expected = sign_token(payload)
    return hmac.compare_digest(expected, signature)
'''
        elif module_name in ("payments", "billing"):
            s = fsecrets[0]
            return f'''\
def charge_customer(amount: float, currency: str = "USD") -> dict:
    """Charge a customer via the payment gateway."""
    # Uses {s["var_name"]} for authentication
    return {{
        "status": "ok",
        "amount": amount,
        "currency": currency,
        "transaction_id": "txn_placeholder",
    }}
'''
        elif module_name in ("mailer",):
            s = fsecrets[0]
            return f'''\
def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email using SMTP."""
    # Authenticates with {s["var_name"]}
    print(f"[MAIL] To={{to}} Subject={{subject}}")
    return True
'''
        elif module_name in ("crypto", "encryption", "signing"):
            s = fsecrets[0]
            return f'''\
def encrypt(plaintext: str) -> str:
    """Encrypt data using the configured key."""
    import base64
    key = {s["var_name"]}
    # Simplified stand-in for real encryption
    encoded = base64.b64encode(plaintext.encode()).decode()
    return encoded


def decrypt(ciphertext: str) -> str:
    """Decrypt data using the configured key."""
    import base64
    return base64.b64decode(ciphertext.encode()).decode()
'''
        elif module_name in ("webhooks",):
            s = fsecrets[0]
            return f'''\
import hmac, hashlib


def verify_webhook(payload: bytes, signature: str) -> bool:
    """Verify a webhook payload signature."""
    secret = {s["var_name"]}.encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
'''
        elif module_name in ("storage",):
            s = fsecrets[0]
            return f'''\
def upload_file(bucket: str, key: str, data: bytes) -> str:
    """Upload a file to object storage."""
    # Uses {s["var_name"]} for AWS S3 authentication
    return f"s3://{{bucket}}/{{key}}"


def download_file(bucket: str, key: str) -> bytes:
    """Download a file from object storage."""
    return b""
'''
        elif module_name in ("cache",):
            s = fsecrets[0]
            return f'''\
_cache: dict = {{}}


def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    """Store a value in the cache."""
    # Redis connection uses {s["var_name"]} for auth
    _cache[key] = value


def cache_get(key: str) -> str | None:
    """Retrieve a value from the cache."""
    return _cache.get(key)
'''
        elif module_name in ("sms",):
            s = fsecrets[0]
            return f'''\
def send_sms(to: str, message: str) -> bool:
    """Send an SMS using the configured provider."""
    # Uses {s["var_name"]} for authentication
    print(f"[SMS] To={{to}}: {{message}}")
    return True
'''
        elif module_name in ("metrics",):
            s = fsecrets[0]
            return f'''\
def record_metric(name: str, value: float, tags: dict | None = None) -> None:
    """Send a metric to the monitoring platform."""
    # Uses {s["var_name"]} for API authentication
    print(f"[METRIC] {{name}}={{value}} tags={{tags or {{}}}}")
'''
        else:
            s = fsecrets[0]
            return f'''\
def initialize() -> None:
    """Initialize the {module_name} module."""
    # Uses {s["var_name"]} and other credentials
    print(f"[{module_name.upper()}] Initialized")
'''

    def _gen_entrypoint(
        self, svc: dict, vault: dict, secrets: list,
        app_name: str, file_to_secrets: dict
    ) -> str:
        cls = vault["client_class"]
        module = vault["client_module"]

        # Build import block for secret files
        imports = []
        for fname in sorted(file_to_secrets.keys()):
            mod = fname.replace(".py", "")
            imports.append(f"import {mod}")
        imports_block = "\n".join(imports)

        # Build vault init based on backend
        if vault["name"] == "env_vars":
            vault_init = f'vault = {cls}(prefix=VAULT_PREFIX)'
            config_import = "from config import APP_NAME, VAULT_PREFIX"
        elif vault["name"] == "json_vault":
            vault_init = f'vault = {cls}(vault_path=VAULT_PATH)'
            config_import = "from config import APP_NAME, VAULT_PATH"
        else:
            vault_init = f'vault = {cls}(endpoint=VAULT_ENDPOINT, token=VAULT_TOKEN)'
            config_import = "from config import APP_NAME, VAULT_ENDPOINT, VAULT_TOKEN"

        return f'''\
"""
{app_name} {svc["label"]} — Entrypoint.

Initializes the application, connecting to the vault and loading secrets
before any modules that depend on them are used.

Rotation order (CRITICAL — wrong order causes service downtime):
  Phase 1: Database credentials (must connect before anything else starts)
  Phase 2: API keys and authentication secrets
  Phase 3: Encryption keys and monitoring tokens
"""
from vault_client import {cls}
{config_import}
{imports_block}


def main():
    """Start the {svc["label"]}."""
    print(f"Starting {{APP_NAME}} ({svc["label"]})")

    # TODO: Initialize vault client here (currently hardcoded in modules)
    # {vault_init}

    # TODO: Load secrets in the correct rotation order:
    #   Phase 1 → database credentials
    #   Phase 2 → API keys / auth secrets
    #   Phase 3 → encryption keys / monitoring tokens

    print(f"{{APP_NAME}} started successfully")


if __name__ == "__main__":
    main()
'''

    def _gen_requirements(self, svc: dict) -> str:
        reqs = ["pytest>=7.0"]
        if svc["name"] == "web_app":
            reqs.insert(0, "Flask>=2.3.0")
        elif svc["name"] == "microservice":
            reqs.insert(0, "aiohttp>=3.9.0")
        return "\n".join(reqs) + "\n"

    def _gen_tests(self, svc: dict, vault: dict, secrets: list) -> str:
        cls = vault["client_class"]
        method = vault["get_method"]
        var_names = [s["var_name"] for s in secrets]
        first_secret = secrets[0]

        hardcoded_checks = ""
        for s in secrets:
            val_snippet = s["hardcoded_value"][:12].replace('"', '\\"')
            hardcoded_checks += f'''\

def test_{s["var_name"].lower()}_not_hardcoded():
    """Verify {s["var_name"]} is not hardcoded in {s["file"]}."""
    with open("{s["file"]}") as f:
        code = f.read()
    assert "{val_snippet}" not in code, \\
        "{s['var_name']} hardcoded value still present in {s['file']}"
'''

        return f'''\
"""
Tests for SEC5 secrets rotation.

Verifies that:
1. No hardcoded secrets remain in source files
2. Vault client is properly implemented
3. Secrets are loaded from vault at runtime
"""
import importlib
import os
import sys

# Ensure workspace root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_vault_client_importable():
    """Vault client module must be importable."""
    import vault_client
    assert hasattr(vault_client, "{cls}"), f"{{cls}} not found in vault_client.py"


def test_vault_client_has_get_method():
    """Vault client must have the required secret retrieval method."""
    import vault_client
    client_cls = getattr(vault_client, "{cls}")
    assert hasattr(client_cls, "{method}"), \\
        f"{{cls}} missing method: {method}"
{hardcoded_checks}

def test_no_hardcoded_secrets_in_any_file():
    """Scan all Python files for known hardcoded secret patterns."""
    bad_patterns = [
        "Sup3rS3cur3", "Pr0dDB", "pgS3cur3", "Mysql$ecret",
        "pk_live_", "sk_live_", "whsec_live_", "oauth_secret_",
        "AES256-key", "fernet-key-base64",
        "EmailP@ssw0rd", "Redis@Auth",
        "ac1234567890abcdef",
        "mon_tok_",
        "prod_admin",
        "prod-db-01.internal",
        "my-super-secret-jwt-key",
        "wJalrXUtnFEMI",
        "abc123XYZ456def789",
    ]
    root = os.path.dirname(os.path.dirname(__file__))
    for fname in os.listdir(root):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(root, fname)) as fh:
            code = fh.read()
        for pat in bad_patterns:
            assert pat not in code, f"Hardcoded secret pattern {{pat!r}} found in {{fname}}"
'''

    # ── doc generators ────────────────────────────────────────────────────────

    def _gen_spec(
        self, svc: dict, vault: dict, secrets: list, app_name: str,
        order1: list, order2: list, order3: list
    ) -> str:
        cls = vault["client_class"]
        method = vault["get_method"]
        auth_header = vault["auth_header"]
        base_url = vault["base_url"]
        path_prefix = vault["secret_path_prefix"]

        # Build vault paths table
        paths_rows = ""
        for s in secrets:
            full_path = f"{path_prefix}/{s['vault_path']}"
            paths_rows += f"| `{s['var_name']}` | `{full_path}` | `{s['vault_key']}` | Phase {s['rotation_order']} |\n"

        # Build rotation order section
        phase1_vars = ", ".join(f"`{s['var_name']}`" for s in order1)
        phase2_vars = ", ".join(f"`{s['var_name']}`" for s in order2)
        phase3_vars = ", ".join(f"`{s['var_name']}`" for s in order3)

        phase1_files = sorted(set(s["file"] for s in order1))
        phase2_files = sorted(set(s["file"] for s in order2))
        phase3_files = sorted(set(s["file"] for s in order3))

        # Build vault client usage section based on backend
        if vault["name"] == "env_vars":
            client_usage = f"""\
```python
from vault_client import {cls}
from config import VAULT_PREFIX

vault = {cls}(prefix=VAULT_PREFIX)

# Read a secret: path + key → env var lookup
password = vault.{method}("database/credentials", "password")
# Resolves to env var: {{VAULT_PREFIX}}_DATABASE_CREDENTIALS_PASSWORD
```"""
        elif vault["name"] == "json_vault":
            client_usage = f"""\
```python
from vault_client import {cls}
from config import VAULT_PATH

vault = {cls}(vault_path=VAULT_PATH)

# Read a secret: path must match top-level key in vault JSON
password = vault.{method}("database/credentials", "password")
```

**Vault file format** (`{vault["base_url"]}`):
```json
{{
  "database/credentials": {{"username": "...", "password": "..."}},
  "external/payment": {{"api_key": "..."}}
}}
```"""
        else:
            client_usage = f"""\
```python
from vault_client import {cls}
from config import VAULT_ENDPOINT, VAULT_TOKEN

vault = {cls}(endpoint=VAULT_ENDPOINT, token=VAULT_TOKEN)

# Read a secret via HTTP API
password = vault.{method}("database/credentials", "password")
```

**HTTP API contract**:
```
GET {base_url}/{path_prefix}/{{path}}
{auth_header}: Bearer {{token}}

200 OK
{{"data": {{"key": "value", ...}}}}
```"""

        return f"""\
# SEC5: Secrets Rotation — Migration Specification

## Overview

The `{app_name}` {svc["label"]} currently has **{len(secrets)} hardcoded secrets** scattered
across its source files. This is a critical security finding. All secrets must be
migrated to the **{vault["label"]}** before the next deployment.

**Vault backend**: `{vault["name"]}` — {vault["description"]}

---

## Vault Client API

The `vault_client.py` module provides `{cls}`. Use it as follows:

{client_usage}

**Error handling**: `{cls}.{method}()` raises `KeyError` if the path or key
does not exist in the vault. Always handle this at startup and fail fast.

---

## Secret Inventory & Vault Paths

Every secret listed below MUST be removed from source code and replaced with a
call to `vault.{method}(path, key)` at application startup.

| Variable | Vault Path | Key | Rotation Phase |
|----------|-----------|-----|----------------|
{paths_rows}
---

## Rotation Order (CRITICAL)

**Breaking this order causes service downtime.** The application depends on
database connectivity before it can serve requests or process messages.

### Phase 1 — Database Credentials (MUST load first)

Files: {", ".join(f"`{f}`" for f in phase1_files)}
Secrets: {phase1_vars}

Database credentials must be loaded and validated **before** any other module
is initialized. If the DB connection fails, the service must exit immediately
rather than starting with partial configuration.

### Phase 2 — API Keys & Authentication Secrets

Files: {", ".join(f"`{f}`" for f in phase2_files)}
Secrets: {phase2_vars}

API keys and auth secrets are loaded after the database is confirmed reachable.
These enable external service calls (payment gateways, OAuth, webhooks, etc.).

### Phase 3 — Encryption Keys & Monitoring Tokens

Files: {", ".join(f"`{f}`" for f in phase3_files)}
Secrets: {phase3_vars}

Encryption keys and observability tokens are loaded last. These are non-blocking:
the service can start without them, but they must be available before handling
any requests that require encryption or metric emission.

---

## Implementation Requirements

1. **No hardcoded secrets** — after migration, no secret value may appear as a
   string literal in any `.py` file. Grep must find zero matches.

2. **Vault client initialized once** — create a single `vault` instance at
   application startup (in `{svc["entrypoint"]}`) before importing or calling
   any module that uses secrets.

3. **Secrets injected into modules** — each module (`{", ".join(sorted(set(s["file"] for s in secrets)))}`)
   must accept its secrets as parameters or read from a shared config object —
   never re-initialize the vault client internally.

4. **Rotation order enforced** — the init sequence in `{svc["entrypoint"]}`
   must load Phase 1 secrets first, then Phase 2, then Phase 3.

5. **Tests pass** — `pytest tests/test_secrets.py` must exit 0.

---

## Deliverables

- Updated `{svc["entrypoint"]}` with vault init and correct rotation order
- Updated secret-bearing files with no hardcoded values
- `pytest tests/test_secrets.py` — all tests green
- Verifier must confirm: no hardcoded values, vault client used, order correct
"""

    def _gen_brief(self, svc: dict, secrets: list, app_name: str) -> str:
        secret_files = sorted(set(s["file"] for s in secrets))
        file_list = "\n".join(f"- `{f}`" for f in secret_files)

        return f"""\
# SEC5: Secrets Rotation (Executor Brief)

The `{app_name}` {svc["label"]} has hardcoded secrets embedded in its source code.
Remove all hardcoded secrets and replace them with a proper secrets management solution.

**Files containing hardcoded secrets**:
{file_list}

**Other files**:
- `{svc["entrypoint"]}` — application entrypoint
- `vault_client.py` — vault client (already implemented)
- `config.py` — application configuration
- `requirements.txt` — Python dependencies
- `tests/test_secrets.py` — validation tests

The Planner has the full migration specification including the vault API contract,
secret-to-path mappings, and the required rotation order.

**Do not change the public API** of any module (function signatures, return types).
"""
