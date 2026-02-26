"""
Parameterized generator for TEST3: Integration Tests from Service Contract.

TNI Pattern D (Cross-System Contract): Spec has the complete service contract
(endpoint URLs, request/response schemas, auth requirements, error codes, rate
limits, timeout behaviour). Brief says "The service lacks integration tests.
Write tests that verify the API contract."

Each seed produces:
- A different service type (user_service, payment_service,
  notification_service, search_service)
- 4-6 endpoints per service
- A working Flask server (server.py) the agent can run
- A test skeleton (tests/test_integration.py) with TODOs
- A broken variant of the server for mutation testing
- Spec: full API contract (endpoints, schemas, error codes, auth, rate limits)
- Brief: vague "write integration tests"
"""
from __future__ import annotations

import textwrap
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ---------------------------------------------------------------------------
# Service definitions
# ---------------------------------------------------------------------------

SERVICE_POOL = [
    # ── user_service ──────────────────────────────────────────────────────
    {
        "service_name": "user_service",
        "display_name": "User Service",
        "description": "manages user accounts and authentication",
        "base_url": "http://localhost:5000",
        "auth_header": "X-API-Key",
        "valid_api_key": "secret-key-abc123",
        "port": 5000,
        "rate_limit": 100,
        "timeout_ms": 5000,
        "endpoints": [
            {
                "id": "create_user",
                "method": "POST",
                "path": "/users",
                "summary": "Create a new user account",
                "auth_required": True,
                "request_schema": {
                    "username": "string, required, 3-50 chars",
                    "email": "string, required, valid email format",
                    "role": "string, optional, one of: admin|editor|viewer (default: viewer)",
                },
                "response_schema": {
                    "id": "string (UUID)",
                    "username": "string",
                    "email": "string",
                    "role": "string",
                    "created_at": "string (ISO-8601)",
                },
                "status_codes": {
                    "201": "User created successfully",
                    "400": "Validation error (missing field, bad email, invalid role)",
                    "401": "Missing or invalid API key",
                    "409": "Username already exists",
                },
                "test_cases": [
                    {
                        "desc": "create valid user",
                        "payload": {"username": "alice", "email": "alice@example.com", "role": "editor"},
                        "expected_status": 201,
                        "check_fields": ["id", "username", "email", "role", "created_at"],
                    },
                    {
                        "desc": "missing email → 400",
                        "payload": {"username": "bob"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "invalid role → 400",
                        "payload": {"username": "carol", "email": "carol@example.com", "role": "superuser"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "no auth → 401",
                        "payload": {"username": "dave", "email": "dave@example.com"},
                        "expected_status": 401,
                        "skip_auth": True,
                    },
                ],
            },
            {
                "id": "get_user",
                "method": "GET",
                "path": "/users/{user_id}",
                "summary": "Retrieve a user by ID",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "id": "string (UUID)",
                    "username": "string",
                    "email": "string",
                    "role": "string",
                    "created_at": "string (ISO-8601)",
                },
                "status_codes": {
                    "200": "User found",
                    "401": "Missing or invalid API key",
                    "404": "User not found",
                },
                "test_cases": [
                    {
                        "desc": "get existing user → 200",
                        "setup": "create_user_first",
                        "expected_status": 200,
                        "check_fields": ["id", "username", "email", "role", "created_at"],
                    },
                    {
                        "desc": "get non-existent user → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "list_users",
                "method": "GET",
                "path": "/users",
                "summary": "List all users; supports ?role= filter",
                "auth_required": True,
                "request_schema": {
                    "role": "query param, optional, filter by role",
                },
                "response_schema": {
                    "users": "array of user objects",
                    "total": "integer",
                },
                "status_codes": {
                    "200": "List returned (may be empty)",
                    "401": "Missing or invalid API key",
                },
                "test_cases": [
                    {
                        "desc": "list all users → 200 with users array and total",
                        "expected_status": 200,
                        "check_fields": ["users", "total"],
                    },
                    {
                        "desc": "filter by role → only matching users returned",
                        "query": "?role=admin",
                        "expected_status": 200,
                    },
                ],
            },
            {
                "id": "delete_user",
                "method": "DELETE",
                "path": "/users/{user_id}",
                "summary": "Delete a user by ID",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "deleted": "boolean true",
                    "id": "string (UUID)",
                },
                "status_codes": {
                    "200": "User deleted",
                    "401": "Missing or invalid API key",
                    "404": "User not found",
                },
                "test_cases": [
                    {
                        "desc": "delete existing user → 200 with deleted=true",
                        "setup": "create_user_first",
                        "expected_status": 200,
                        "check_fields": ["deleted", "id"],
                    },
                    {
                        "desc": "delete non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "health_check",
                "method": "GET",
                "path": "/health",
                "summary": "Health check endpoint",
                "auth_required": False,
                "request_schema": {},
                "response_schema": {
                    "status": "string 'ok'",
                    "service": "string 'user_service'",
                },
                "status_codes": {
                    "200": "Service healthy",
                },
                "test_cases": [
                    {
                        "desc": "health returns 200 with status=ok",
                        "expected_status": 200,
                        "check_fields": ["status", "service"],
                        "check_values": {"status": "ok", "service": "user_service"},
                    },
                ],
            },
            {
                "id": "update_user",
                "method": "PATCH",
                "path": "/users/{user_id}",
                "summary": "Partially update a user (email or role only)",
                "auth_required": True,
                "request_schema": {
                    "email": "string, optional, valid email format",
                    "role": "string, optional, one of: admin|editor|viewer",
                },
                "response_schema": {
                    "id": "string",
                    "username": "string",
                    "email": "string",
                    "role": "string",
                    "created_at": "string",
                },
                "status_codes": {
                    "200": "User updated",
                    "400": "Validation error",
                    "401": "Unauthorized",
                    "404": "User not found",
                },
                "test_cases": [
                    {
                        "desc": "update role → 200 with new role",
                        "setup": "create_user_first",
                        "payload": {"role": "admin"},
                        "expected_status": 200,
                        "check_values": {"role": "admin"},
                    },
                    {
                        "desc": "update with invalid role → 400",
                        "setup": "create_user_first",
                        "payload": {"role": "god"},
                        "expected_status": 400,
                    },
                ],
            },
        ],
    },

    # ── payment_service ───────────────────────────────────────────────────
    {
        "service_name": "payment_service",
        "display_name": "Payment Service",
        "description": "processes payments and manages transaction records",
        "base_url": "http://localhost:5001",
        "auth_header": "Authorization",
        "valid_api_key": "Bearer pay-token-xyz789",
        "port": 5001,
        "rate_limit": 60,
        "timeout_ms": 10000,
        "endpoints": [
            {
                "id": "create_payment",
                "method": "POST",
                "path": "/payments",
                "summary": "Create a payment transaction",
                "auth_required": True,
                "request_schema": {
                    "amount": "number, required, > 0, max 100000",
                    "currency": "string, required, one of: USD|EUR|GBP",
                    "recipient_id": "string, required",
                    "description": "string, optional, max 255 chars",
                },
                "response_schema": {
                    "transaction_id": "string (UUID)",
                    "status": "string: pending|completed|failed",
                    "amount": "number",
                    "currency": "string",
                    "recipient_id": "string",
                    "created_at": "string (ISO-8601)",
                },
                "status_codes": {
                    "201": "Payment created",
                    "400": "Validation error (bad amount, bad currency)",
                    "401": "Unauthorized",
                    "422": "Amount exceeds limit",
                },
                "test_cases": [
                    {
                        "desc": "create valid payment → 201",
                        "payload": {"amount": 99.99, "currency": "USD", "recipient_id": "recv-001"},
                        "expected_status": 201,
                        "check_fields": ["transaction_id", "status", "amount", "currency", "created_at"],
                    },
                    {
                        "desc": "negative amount → 400",
                        "payload": {"amount": -10, "currency": "USD", "recipient_id": "recv-001"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "unsupported currency → 400",
                        "payload": {"amount": 50, "currency": "JPY", "recipient_id": "recv-001"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "amount over limit → 422",
                        "payload": {"amount": 200000, "currency": "USD", "recipient_id": "recv-001"},
                        "expected_status": 422,
                    },
                    {
                        "desc": "no auth → 401",
                        "payload": {"amount": 10, "currency": "USD", "recipient_id": "recv-001"},
                        "expected_status": 401,
                        "skip_auth": True,
                    },
                ],
            },
            {
                "id": "get_payment",
                "method": "GET",
                "path": "/payments/{transaction_id}",
                "summary": "Retrieve a payment by transaction ID",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "transaction_id": "string",
                    "status": "string",
                    "amount": "number",
                    "currency": "string",
                    "recipient_id": "string",
                    "created_at": "string",
                },
                "status_codes": {
                    "200": "Payment found",
                    "401": "Unauthorized",
                    "404": "Transaction not found",
                },
                "test_cases": [
                    {
                        "desc": "get existing payment → 200",
                        "setup": "create_payment_first",
                        "expected_status": 200,
                        "check_fields": ["transaction_id", "status", "amount"],
                    },
                    {
                        "desc": "get non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "list_payments",
                "method": "GET",
                "path": "/payments",
                "summary": "List payments; supports ?status= and ?currency= filters",
                "auth_required": True,
                "request_schema": {
                    "status": "query param, optional",
                    "currency": "query param, optional",
                },
                "response_schema": {
                    "payments": "array",
                    "total": "integer",
                },
                "status_codes": {
                    "200": "List returned",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "list payments → 200 with payments array and total",
                        "expected_status": 200,
                        "check_fields": ["payments", "total"],
                    },
                ],
            },
            {
                "id": "refund_payment",
                "method": "POST",
                "path": "/payments/{transaction_id}/refund",
                "summary": "Refund a completed payment",
                "auth_required": True,
                "request_schema": {
                    "reason": "string, optional",
                },
                "response_schema": {
                    "refund_id": "string",
                    "original_transaction_id": "string",
                    "status": "string: refunded",
                    "amount": "number",
                },
                "status_codes": {
                    "200": "Refund processed",
                    "401": "Unauthorized",
                    "404": "Transaction not found",
                    "409": "Payment already refunded or not completed",
                },
                "test_cases": [
                    {
                        "desc": "refund completed payment → 200 with refund_id",
                        "setup": "create_payment_first",
                        "expected_status": 200,
                        "check_fields": ["refund_id", "original_transaction_id", "status", "amount"],
                    },
                    {
                        "desc": "refund non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "health_check",
                "method": "GET",
                "path": "/health",
                "summary": "Health check endpoint",
                "auth_required": False,
                "request_schema": {},
                "response_schema": {
                    "status": "string 'ok'",
                    "service": "string 'payment_service'",
                },
                "status_codes": {
                    "200": "Service healthy",
                },
                "test_cases": [
                    {
                        "desc": "health returns 200 with status=ok",
                        "expected_status": 200,
                        "check_fields": ["status", "service"],
                        "check_values": {"status": "ok", "service": "payment_service"},
                    },
                ],
            },
        ],
    },

    # ── notification_service ──────────────────────────────────────────────
    {
        "service_name": "notification_service",
        "display_name": "Notification Service",
        "description": "sends and tracks notifications via email and SMS channels",
        "base_url": "http://localhost:5002",
        "auth_header": "X-Service-Token",
        "valid_api_key": "svc-token-notif-42",
        "port": 5002,
        "rate_limit": 200,
        "timeout_ms": 3000,
        "endpoints": [
            {
                "id": "send_notification",
                "method": "POST",
                "path": "/notifications",
                "summary": "Send a notification via email or SMS",
                "auth_required": True,
                "request_schema": {
                    "channel": "string, required, one of: email|sms",
                    "recipient": "string, required (email address or phone number)",
                    "subject": "string, required for email, max 200 chars",
                    "body": "string, required, max 1000 chars",
                    "priority": "string, optional, one of: low|normal|high (default: normal)",
                },
                "response_schema": {
                    "notification_id": "string (UUID)",
                    "status": "string: queued|sent|failed",
                    "channel": "string",
                    "recipient": "string",
                    "queued_at": "string (ISO-8601)",
                },
                "status_codes": {
                    "202": "Notification queued",
                    "400": "Validation error (bad channel, missing body, invalid priority)",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "send email → 202 with notification_id",
                        "payload": {"channel": "email", "recipient": "user@example.com",
                                    "subject": "Hello", "body": "Test message"},
                        "expected_status": 202,
                        "check_fields": ["notification_id", "status", "channel", "recipient", "queued_at"],
                    },
                    {
                        "desc": "invalid channel → 400",
                        "payload": {"channel": "fax", "recipient": "user@example.com", "body": "Hi"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "missing body → 400",
                        "payload": {"channel": "sms", "recipient": "+15550001234"},
                        "expected_status": 400,
                    },
                    {
                        "desc": "no auth → 401",
                        "payload": {"channel": "sms", "recipient": "+15550001234", "body": "Hi"},
                        "expected_status": 401,
                        "skip_auth": True,
                    },
                ],
            },
            {
                "id": "get_notification",
                "method": "GET",
                "path": "/notifications/{notification_id}",
                "summary": "Get notification status by ID",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "notification_id": "string",
                    "status": "string",
                    "channel": "string",
                    "recipient": "string",
                    "queued_at": "string",
                },
                "status_codes": {
                    "200": "Notification found",
                    "401": "Unauthorized",
                    "404": "Notification not found",
                },
                "test_cases": [
                    {
                        "desc": "get existing notification → 200",
                        "setup": "create_notification_first",
                        "expected_status": 200,
                        "check_fields": ["notification_id", "status", "channel"],
                    },
                    {
                        "desc": "get non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "list_notifications",
                "method": "GET",
                "path": "/notifications",
                "summary": "List notifications; supports ?channel= and ?status= filters",
                "auth_required": True,
                "request_schema": {
                    "channel": "query param, optional",
                    "status": "query param, optional",
                },
                "response_schema": {
                    "notifications": "array",
                    "total": "integer",
                },
                "status_codes": {
                    "200": "List returned",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "list notifications → 200 with array and total",
                        "expected_status": 200,
                        "check_fields": ["notifications", "total"],
                    },
                ],
            },
            {
                "id": "cancel_notification",
                "method": "DELETE",
                "path": "/notifications/{notification_id}",
                "summary": "Cancel a queued notification (cannot cancel already-sent)",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "cancelled": "boolean true",
                    "notification_id": "string",
                },
                "status_codes": {
                    "200": "Notification cancelled",
                    "401": "Unauthorized",
                    "404": "Notification not found",
                    "409": "Cannot cancel — already sent",
                },
                "test_cases": [
                    {
                        "desc": "cancel queued notification → 200",
                        "setup": "create_notification_first",
                        "expected_status": 200,
                        "check_fields": ["cancelled", "notification_id"],
                    },
                    {
                        "desc": "cancel non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "health_check",
                "method": "GET",
                "path": "/health",
                "summary": "Health check endpoint",
                "auth_required": False,
                "request_schema": {},
                "response_schema": {
                    "status": "string 'ok'",
                    "service": "string 'notification_service'",
                },
                "status_codes": {
                    "200": "Service healthy",
                },
                "test_cases": [
                    {
                        "desc": "health returns 200 with status=ok",
                        "expected_status": 200,
                        "check_fields": ["status", "service"],
                        "check_values": {"status": "ok", "service": "notification_service"},
                    },
                ],
            },
            {
                "id": "retry_notification",
                "method": "POST",
                "path": "/notifications/{notification_id}/retry",
                "summary": "Retry a failed notification",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "notification_id": "string",
                    "status": "string: queued",
                    "retry_count": "integer",
                },
                "status_codes": {
                    "200": "Retry queued",
                    "401": "Unauthorized",
                    "404": "Not found",
                    "409": "Cannot retry — not in failed state",
                },
                "test_cases": [
                    {
                        "desc": "retry non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
        ],
    },

    # ── search_service ────────────────────────────────────────────────────
    {
        "service_name": "search_service",
        "display_name": "Search Service",
        "description": "provides full-text search over indexed documents",
        "base_url": "http://localhost:5003",
        "auth_header": "X-API-Key",
        "valid_api_key": "search-api-key-def456",
        "port": 5003,
        "rate_limit": 300,
        "timeout_ms": 2000,
        "endpoints": [
            {
                "id": "search",
                "method": "GET",
                "path": "/search",
                "summary": "Search documents; requires ?q= query param",
                "auth_required": True,
                "request_schema": {
                    "q": "query param, required, 1-200 chars",
                    "page": "query param, optional integer >= 1 (default: 1)",
                    "page_size": "query param, optional integer 1-100 (default: 10)",
                    "category": "query param, optional, filter by document category",
                },
                "response_schema": {
                    "results": "array of result objects",
                    "total": "integer",
                    "page": "integer",
                    "page_size": "integer",
                    "query": "string (echoed back)",
                },
                "status_codes": {
                    "200": "Search results returned (may be empty)",
                    "400": "Missing or invalid query param",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "valid search → 200 with results, total, page",
                        "query": "?q=test",
                        "expected_status": 200,
                        "check_fields": ["results", "total", "page", "page_size", "query"],
                    },
                    {
                        "desc": "missing q → 400",
                        "query": "",
                        "expected_status": 400,
                    },
                    {
                        "desc": "no auth → 401",
                        "query": "?q=test",
                        "expected_status": 401,
                        "skip_auth": True,
                    },
                    {
                        "desc": "page_size out of range → 400",
                        "query": "?q=test&page_size=500",
                        "expected_status": 400,
                    },
                ],
            },
            {
                "id": "index_document",
                "method": "POST",
                "path": "/documents",
                "summary": "Index a new document",
                "auth_required": True,
                "request_schema": {
                    "title": "string, required, max 500 chars",
                    "content": "string, required",
                    "category": "string, optional",
                    "tags": "array of strings, optional",
                },
                "response_schema": {
                    "document_id": "string (UUID)",
                    "title": "string",
                    "category": "string or null",
                    "indexed_at": "string (ISO-8601)",
                },
                "status_codes": {
                    "201": "Document indexed",
                    "400": "Validation error (missing title or content)",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "index document → 201 with document_id",
                        "payload": {"title": "Test Doc", "content": "Hello world", "category": "general"},
                        "expected_status": 201,
                        "check_fields": ["document_id", "title", "indexed_at"],
                    },
                    {
                        "desc": "missing title → 400",
                        "payload": {"content": "No title here"},
                        "expected_status": 400,
                    },
                ],
            },
            {
                "id": "get_document",
                "method": "GET",
                "path": "/documents/{document_id}",
                "summary": "Retrieve an indexed document by ID",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "document_id": "string",
                    "title": "string",
                    "content": "string",
                    "category": "string or null",
                    "tags": "array",
                    "indexed_at": "string",
                },
                "status_codes": {
                    "200": "Document found",
                    "401": "Unauthorized",
                    "404": "Document not found",
                },
                "test_cases": [
                    {
                        "desc": "get existing document → 200",
                        "setup": "create_document_first",
                        "expected_status": 200,
                        "check_fields": ["document_id", "title", "content", "indexed_at"],
                    },
                    {
                        "desc": "get non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "delete_document",
                "method": "DELETE",
                "path": "/documents/{document_id}",
                "summary": "Delete an indexed document",
                "auth_required": True,
                "request_schema": {},
                "response_schema": {
                    "deleted": "boolean true",
                    "document_id": "string",
                },
                "status_codes": {
                    "200": "Document deleted",
                    "401": "Unauthorized",
                    "404": "Document not found",
                },
                "test_cases": [
                    {
                        "desc": "delete existing document → 200",
                        "setup": "create_document_first",
                        "expected_status": 200,
                        "check_fields": ["deleted", "document_id"],
                    },
                    {
                        "desc": "delete non-existent → 404",
                        "path_param": "00000000-0000-0000-0000-000000000000",
                        "expected_status": 404,
                    },
                ],
            },
            {
                "id": "health_check",
                "method": "GET",
                "path": "/health",
                "summary": "Health check endpoint",
                "auth_required": False,
                "request_schema": {},
                "response_schema": {
                    "status": "string 'ok'",
                    "service": "string 'search_service'",
                },
                "status_codes": {
                    "200": "Service healthy",
                },
                "test_cases": [
                    {
                        "desc": "health returns 200 with status=ok",
                        "expected_status": 200,
                        "check_fields": ["status", "service"],
                        "check_values": {"status": "ok", "service": "search_service"},
                    },
                ],
            },
            {
                "id": "suggest",
                "method": "GET",
                "path": "/suggest",
                "summary": "Autocomplete suggestions for a query prefix",
                "auth_required": True,
                "request_schema": {
                    "q": "query param, required, 1-50 chars",
                    "limit": "query param, optional integer 1-20 (default: 5)",
                },
                "response_schema": {
                    "suggestions": "array of strings",
                    "query": "string (echoed back)",
                },
                "status_codes": {
                    "200": "Suggestions returned (may be empty)",
                    "400": "Missing or invalid query param",
                    "401": "Unauthorized",
                },
                "test_cases": [
                    {
                        "desc": "valid suggest → 200 with suggestions array",
                        "query": "?q=te",
                        "expected_status": 200,
                        "check_fields": ["suggestions", "query"],
                    },
                    {
                        "desc": "missing q → 400",
                        "query": "",
                        "expected_status": 400,
                    },
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Server code generators
# ---------------------------------------------------------------------------

def _build_server_py(svc: dict, selected_endpoint_ids: list[str]) -> str:
    """Build a working Flask server for the given service."""
    svc_name = svc["service_name"]
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    endpoints = {ep["id"]: ep for ep in svc["endpoints"]}
    selected = [endpoints[eid] for eid in selected_endpoint_ids if eid in endpoints]

    if svc_name == "user_service":
        return _build_user_service_server(svc, selected)
    elif svc_name == "payment_service":
        return _build_payment_service_server(svc, selected)
    elif svc_name == "notification_service":
        return _build_notification_service_server(svc, selected)
    elif svc_name == "search_service":
        return _build_search_service_server(svc, selected)
    else:
        raise ValueError(f"Unknown service: {svc_name}")


def _build_user_service_server(svc: dict, endpoints: list[dict]) -> str:
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    return f'''\
#!/usr/bin/env python3
"""
User Service — working implementation.
Run: python server.py
"""
import uuid
import datetime
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_API_KEY = "{valid_key}"
AUTH_HEADER = "{auth_header}"
VALID_ROLES = {{"admin", "editor", "viewer"}}

_users = {{}}  # id -> user dict


def _check_auth():
    key = request.headers.get(AUTH_HEADER, "")
    if key != VALID_API_KEY:
        return jsonify({{"error": "unauthorized", "code": 401}}), 401
    return None


def _now():
    return datetime.datetime.utcnow().isoformat() + "Z"


def _valid_email(email):
    return bool(re.match(r"^[^@]+@[^@]+\\.[^@]+$", email))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "ok", "service": "user_service"}}), 200


@app.route("/users", methods=["POST"])
def create_user():
    err = _check_auth()
    if err:
        return err
    data = request.get_json(force=True) or {{}}
    if "username" not in data:
        return jsonify({{"error": "missing username"}}), 400
    if "email" not in data:
        return jsonify({{"error": "missing email"}}), 400
    if not _valid_email(data["email"]):
        return jsonify({{"error": "invalid email format"}}), 400
    role = data.get("role", "viewer")
    if role not in VALID_ROLES:
        return jsonify({{"error": f"invalid role: {{role}}"}}), 400
    # Check duplicate username
    for u in _users.values():
        if u["username"] == data["username"]:
            return jsonify({{"error": "username already exists"}}), 409
    user_id = str(uuid.uuid4())
    user = {{
        "id": user_id,
        "username": data["username"],
        "email": data["email"],
        "role": role,
        "created_at": _now(),
    }}
    _users[user_id] = user
    return jsonify(user), 201


@app.route("/users", methods=["GET"])
def list_users():
    err = _check_auth()
    if err:
        return err
    role_filter = request.args.get("role")
    users = list(_users.values())
    if role_filter:
        users = [u for u in users if u["role"] == role_filter]
    return jsonify({{"users": users, "total": len(users)}}), 200


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    err = _check_auth()
    if err:
        return err
    user = _users.get(user_id)
    if not user:
        return jsonify({{"error": "user not found"}}), 404
    return jsonify(user), 200


@app.route("/users/<user_id>", methods=["PATCH"])
def update_user(user_id):
    err = _check_auth()
    if err:
        return err
    user = _users.get(user_id)
    if not user:
        return jsonify({{"error": "user not found"}}), 404
    data = request.get_json(force=True) or {{}}
    if "email" in data:
        if not _valid_email(data["email"]):
            return jsonify({{"error": "invalid email format"}}), 400
        user["email"] = data["email"]
    if "role" in data:
        if data["role"] not in VALID_ROLES:
            return jsonify({{"error": f"invalid role: {{data['role']}}"}}), 400
        user["role"] = data["role"]
    return jsonify(user), 200


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    err = _check_auth()
    if err:
        return err
    user = _users.pop(user_id, None)
    if not user:
        return jsonify({{"error": "user not found"}}), 404
    return jsonify({{"deleted": True, "id": user_id}}), 200


if __name__ == "__main__":
    app.run(port={port}, debug=False)
'''


def _build_payment_service_server(svc: dict, endpoints: list[dict]) -> str:
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    return f'''\
#!/usr/bin/env python3
"""
Payment Service — working implementation.
Run: python server.py
"""
import uuid
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_AUTH = "{valid_key}"
AUTH_HEADER = "{auth_header}"
VALID_CURRENCIES = {{"USD", "EUR", "GBP"}}
MAX_AMOUNT = 100000

_payments = {{}}   # transaction_id -> payment dict
_refunds = {{}}    # refund_id -> refund dict


def _check_auth():
    key = request.headers.get(AUTH_HEADER, "")
    if key != VALID_AUTH:
        return jsonify({{"error": "unauthorized", "code": 401}}), 401
    return None


def _now():
    return datetime.datetime.utcnow().isoformat() + "Z"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "ok", "service": "payment_service"}}), 200


@app.route("/payments", methods=["POST"])
def create_payment():
    err = _check_auth()
    if err:
        return err
    data = request.get_json(force=True) or {{}}
    amount = data.get("amount")
    currency = data.get("currency")
    recipient_id = data.get("recipient_id")
    if amount is None or currency is None or recipient_id is None:
        return jsonify({{"error": "missing required fields"}}), 400
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({{"error": "amount must be a positive number"}}), 400
    if currency not in VALID_CURRENCIES:
        return jsonify({{"error": f"unsupported currency: {{currency}}"}}), 400
    if amount > MAX_AMOUNT:
        return jsonify({{"error": f"amount exceeds limit of {{MAX_AMOUNT}}"}}), 422
    txn_id = str(uuid.uuid4())
    payment = {{
        "transaction_id": txn_id,
        "status": "completed",
        "amount": amount,
        "currency": currency,
        "recipient_id": recipient_id,
        "description": data.get("description", ""),
        "created_at": _now(),
    }}
    _payments[txn_id] = payment
    return jsonify(payment), 201


@app.route("/payments", methods=["GET"])
def list_payments():
    err = _check_auth()
    if err:
        return err
    status_filter = request.args.get("status")
    currency_filter = request.args.get("currency")
    payments = list(_payments.values())
    if status_filter:
        payments = [p for p in payments if p["status"] == status_filter]
    if currency_filter:
        payments = [p for p in payments if p["currency"] == currency_filter]
    return jsonify({{"payments": payments, "total": len(payments)}}), 200


@app.route("/payments/<txn_id>", methods=["GET"])
def get_payment(txn_id):
    err = _check_auth()
    if err:
        return err
    payment = _payments.get(txn_id)
    if not payment:
        return jsonify({{"error": "transaction not found"}}), 404
    return jsonify(payment), 200


@app.route("/payments/<txn_id>/refund", methods=["POST"])
def refund_payment(txn_id):
    err = _check_auth()
    if err:
        return err
    payment = _payments.get(txn_id)
    if not payment:
        return jsonify({{"error": "transaction not found"}}), 404
    if payment["status"] != "completed":
        return jsonify({{"error": "payment not in completed state"}}), 409
    # Check already refunded
    for r in _refunds.values():
        if r["original_transaction_id"] == txn_id:
            return jsonify({{"error": "already refunded"}}), 409
    refund_id = str(uuid.uuid4())
    data = request.get_json(force=True) or {{}}
    refund = {{
        "refund_id": refund_id,
        "original_transaction_id": txn_id,
        "status": "refunded",
        "amount": payment["amount"],
        "reason": data.get("reason", ""),
    }}
    _refunds[refund_id] = refund
    payment["status"] = "refunded"
    return jsonify(refund), 200


if __name__ == "__main__":
    app.run(port={port}, debug=False)
'''


def _build_notification_service_server(svc: dict, endpoints: list[dict]) -> str:
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    return f'''\
#!/usr/bin/env python3
"""
Notification Service — working implementation.
Run: python server.py
"""
import uuid
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_TOKEN = "{valid_key}"
AUTH_HEADER = "{auth_header}"
VALID_CHANNELS = {{"email", "sms"}}
VALID_PRIORITIES = {{"low", "normal", "high"}}

_notifications = {{}}  # notification_id -> notification dict


def _check_auth():
    key = request.headers.get(AUTH_HEADER, "")
    if key != VALID_TOKEN:
        return jsonify({{"error": "unauthorized", "code": 401}}), 401
    return None


def _now():
    return datetime.datetime.utcnow().isoformat() + "Z"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "ok", "service": "notification_service"}}), 200


@app.route("/notifications", methods=["POST"])
def send_notification():
    err = _check_auth()
    if err:
        return err
    data = request.get_json(force=True) or {{}}
    channel = data.get("channel")
    recipient = data.get("recipient")
    body = data.get("body")
    if not channel or not recipient or not body:
        return jsonify({{"error": "missing required fields: channel, recipient, body"}}), 400
    if channel not in VALID_CHANNELS:
        return jsonify({{"error": f"invalid channel: {{channel}}"}}), 400
    priority = data.get("priority", "normal")
    if priority not in VALID_PRIORITIES:
        return jsonify({{"error": f"invalid priority: {{priority}}"}}), 400
    notif_id = str(uuid.uuid4())
    notif = {{
        "notification_id": notif_id,
        "status": "queued",
        "channel": channel,
        "recipient": recipient,
        "subject": data.get("subject", ""),
        "body": body,
        "priority": priority,
        "queued_at": _now(),
        "retry_count": 0,
    }}
    _notifications[notif_id] = notif
    return jsonify({{
        "notification_id": notif_id,
        "status": notif["status"],
        "channel": notif["channel"],
        "recipient": notif["recipient"],
        "queued_at": notif["queued_at"],
    }}), 202


@app.route("/notifications", methods=["GET"])
def list_notifications():
    err = _check_auth()
    if err:
        return err
    channel_filter = request.args.get("channel")
    status_filter = request.args.get("status")
    notifs = list(_notifications.values())
    if channel_filter:
        notifs = [n for n in notifs if n["channel"] == channel_filter]
    if status_filter:
        notifs = [n for n in notifs if n["status"] == status_filter]
    return jsonify({{"notifications": notifs, "total": len(notifs)}}), 200


@app.route("/notifications/<notif_id>", methods=["GET"])
def get_notification(notif_id):
    err = _check_auth()
    if err:
        return err
    notif = _notifications.get(notif_id)
    if not notif:
        return jsonify({{"error": "notification not found"}}), 404
    return jsonify(notif), 200


@app.route("/notifications/<notif_id>", methods=["DELETE"])
def cancel_notification(notif_id):
    err = _check_auth()
    if err:
        return err
    notif = _notifications.get(notif_id)
    if not notif:
        return jsonify({{"error": "notification not found"}}), 404
    if notif["status"] == "sent":
        return jsonify({{"error": "cannot cancel already-sent notification"}}), 409
    _notifications.pop(notif_id)
    return jsonify({{"cancelled": True, "notification_id": notif_id}}), 200


@app.route("/notifications/<notif_id>/retry", methods=["POST"])
def retry_notification(notif_id):
    err = _check_auth()
    if err:
        return err
    notif = _notifications.get(notif_id)
    if not notif:
        return jsonify({{"error": "notification not found"}}), 404
    if notif["status"] != "failed":
        return jsonify({{"error": "can only retry failed notifications"}}), 409
    notif["status"] = "queued"
    notif["retry_count"] = notif.get("retry_count", 0) + 1
    return jsonify({{
        "notification_id": notif_id,
        "status": "queued",
        "retry_count": notif["retry_count"],
    }}), 200


if __name__ == "__main__":
    app.run(port={port}, debug=False)
'''


def _build_search_service_server(svc: dict, endpoints: list[dict]) -> str:
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    return f'''\
#!/usr/bin/env python3
"""
Search Service — working implementation.
Run: python server.py
"""
import uuid
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_API_KEY = "{valid_key}"
AUTH_HEADER = "{auth_header}"

_documents = {{}}  # document_id -> document dict


def _check_auth():
    key = request.headers.get(AUTH_HEADER, "")
    if key != VALID_API_KEY:
        return jsonify({{"error": "unauthorized", "code": 401}}), 401
    return None


def _now():
    return datetime.datetime.utcnow().isoformat() + "Z"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "ok", "service": "search_service"}}), 200


@app.route("/search", methods=["GET"])
def search():
    err = _check_auth()
    if err:
        return err
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({{"error": "missing required query param: q"}}), 400
    if len(q) > 200:
        return jsonify({{"error": "query too long (max 200 chars)"}}), 400
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({{"error": "page must be integer >= 1"}}), 400
    try:
        page_size = int(request.args.get("page_size", 10))
        if not (1 <= page_size <= 100):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({{"error": "page_size must be integer 1-100"}}), 400
    category_filter = request.args.get("category")
    # Simple full-text match on title + content
    results = []
    for doc in _documents.values():
        if category_filter and doc.get("category") != category_filter:
            continue
        text = (doc.get("title", "") + " " + doc.get("content", "")).lower()
        if q.lower() in text:
            results.append({{
                "document_id": doc["document_id"],
                "title": doc["title"],
                "category": doc.get("category"),
                "score": 1.0,
            }})
    total = len(results)
    start = (page - 1) * page_size
    results = results[start: start + page_size]
    return jsonify({{
        "results": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "query": q,
    }}), 200


@app.route("/documents", methods=["POST"])
def index_document():
    err = _check_auth()
    if err:
        return err
    data = request.get_json(force=True) or {{}}
    title = data.get("title")
    content = data.get("content")
    if not title:
        return jsonify({{"error": "missing required field: title"}}), 400
    if not content:
        return jsonify({{"error": "missing required field: content"}}), 400
    doc_id = str(uuid.uuid4())
    doc = {{
        "document_id": doc_id,
        "title": title,
        "content": content,
        "category": data.get("category"),
        "tags": data.get("tags", []),
        "indexed_at": _now(),
    }}
    _documents[doc_id] = doc
    return jsonify({{
        "document_id": doc_id,
        "title": title,
        "category": doc.get("category"),
        "indexed_at": doc["indexed_at"],
    }}), 201


@app.route("/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    err = _check_auth()
    if err:
        return err
    doc = _documents.get(doc_id)
    if not doc:
        return jsonify({{"error": "document not found"}}), 404
    return jsonify(doc), 200


@app.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    err = _check_auth()
    if err:
        return err
    doc = _documents.pop(doc_id, None)
    if not doc:
        return jsonify({{"error": "document not found"}}), 404
    return jsonify({{"deleted": True, "document_id": doc_id}}), 200


@app.route("/suggest", methods=["GET"])
def suggest():
    err = _check_auth()
    if err:
        return err
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({{"error": "missing required query param: q"}}), 400
    if len(q) > 50:
        return jsonify({{"error": "query too long (max 50 chars)"}}), 400
    try:
        limit = int(request.args.get("limit", 5))
        if not (1 <= limit <= 20):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({{"error": "limit must be integer 1-20"}}), 400
    suggestions = []
    for doc in _documents.values():
        title = doc.get("title", "")
        if title.lower().startswith(q.lower()):
            suggestions.append(title)
    suggestions = list(dict.fromkeys(suggestions))[:limit]
    return jsonify({{"suggestions": suggestions, "query": q}}), 200


if __name__ == "__main__":
    app.run(port={port}, debug=False)
'''


# ---------------------------------------------------------------------------
# Broken server generator (for mutation testing)
# ---------------------------------------------------------------------------

def _build_broken_server_py(svc: dict, selected_endpoint_ids: list[str]) -> str:
    """Return a broken variant with deliberate bugs for mutation testing."""
    good = _build_server_py(svc, selected_endpoint_ids)
    svc_name = svc["service_name"]

    if svc_name == "user_service":
        # Bug: 409 returns 200, auth check removed for create_user
        broken = good.replace(
            'return jsonify({"error": "username already exists"}), 409',
            'return jsonify({"error": "username already exists"}), 200',
        )
        broken = broken.replace(
            'if role not in VALID_ROLES:\n        return jsonify({"error": f"invalid role: {role}"}), 400',
            '# BROKEN: role validation removed',
        )
        return broken
    elif svc_name == "payment_service":
        # Bug: amount > MAX_AMOUNT returns 400 instead of 422; negative amount not checked
        broken = good.replace(
            'return jsonify({"error": f"amount exceeds limit of {MAX_AMOUNT}"}), 422',
            'return jsonify({"error": f"amount exceeds limit of {MAX_AMOUNT}"}), 400',
        )
        broken = broken.replace(
            'if not isinstance(amount, (int, float)) or amount <= 0:\n        return jsonify({"error": "amount must be a positive number"}), 400',
            '# BROKEN: negative amount check removed',
        )
        return broken
    elif svc_name == "notification_service":
        # Bug: send returns 200 instead of 202; cancel of sent returns 200 instead of 409
        broken = good.replace(
            '}}, 202', '}}, 200', 1
        )
        broken = broken.replace(
            'return jsonify({"error": "cannot cancel already-sent notification"}), 409',
            'return jsonify({"error": "cannot cancel already-sent notification"}), 200',
        )
        return broken
    elif svc_name == "search_service":
        # Bug: missing q returns 200 instead of 400; page_size validation removed
        broken = good.replace(
            'return jsonify({"error": "missing required query param: q"}), 400',
            'return jsonify({"results": [], "total": 0, "page": 1, "page_size": 10, "query": ""}), 200',
            1,
        )
        broken = broken.replace(
            'if not (1 <= page_size <= 100):\n            raise ValueError',
            'pass  # BROKEN: page_size validation removed',
        )
        return broken
    return good


# ---------------------------------------------------------------------------
# Test skeleton generator
# ---------------------------------------------------------------------------

def _build_test_skeleton(svc: dict, selected_endpoint_ids: list[str]) -> str:
    svc_name = svc["service_name"]
    base_url = svc["base_url"]
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    port = svc["port"]
    endpoints = {ep["id"]: ep for ep in svc["endpoints"]}
    selected = [endpoints[eid] for eid in selected_endpoint_ids if eid in endpoints]

    endpoint_comments = []
    for ep in selected:
        endpoint_comments.append(f"# {ep['method']} {ep['path']} — {ep['summary']}")

    ep_comments_str = "\n".join(endpoint_comments)

    return f'''\
"""
Integration tests for {svc["display_name"]}.

The service {svc["description"]}.

Start the server before running tests:
    python server.py &

Run tests:
    python -m pytest tests/test_integration.py -v

Base URL: {base_url}
Auth header: {auth_header}: {valid_key}
"""
import pytest
import requests

BASE_URL = "{base_url}"
AUTH_HEADERS = {{"{auth_header}": "{valid_key}"}}

# Endpoints covered by this contract:
{ep_comments_str}


# ---------------------------------------------------------------------------
# TODO: Write integration tests below.
# Your tests must verify:
#   1. Each endpoint returns the correct HTTP status code
#   2. Response bodies contain the required fields
#   3. Authentication is enforced (missing/wrong key → 401)
#   4. Validation errors return 400 with meaningful error response
#   5. Not-found cases return 404
#   6. The /health endpoint is reachable without auth
# ---------------------------------------------------------------------------


# TODO: Implement tests for the /health endpoint
class TestHealth:
    def test_health_returns_200(self):
        # TODO: GET {base_url}/health and assert status == 200
        pass

    def test_health_response_schema(self):
        # TODO: assert response JSON has 'status' == 'ok' and 'service' fields
        pass


# TODO: Implement tests for each authenticated endpoint
# Example structure:

# class TestCreateResource:
#     def test_valid_request_returns_201(self):
#         pass
#
#     def test_missing_field_returns_400(self):
#         pass
#
#     def test_no_auth_returns_401(self):
#         pass

# class TestGetResource:
#     def test_existing_resource_returns_200(self):
#         pass
#
#     def test_nonexistent_returns_404(self):
#         pass
'''


# ---------------------------------------------------------------------------
# Spec and brief generators
# ---------------------------------------------------------------------------

def _build_spec_md(svc: dict, selected_endpoint_ids: list[str], seed: int) -> str:
    svc_name = svc["service_name"]
    display_name = svc["display_name"]
    base_url = svc["base_url"]
    auth_header = svc["auth_header"]
    valid_key = svc["valid_api_key"]
    rate_limit = svc["rate_limit"]
    timeout_ms = svc["timeout_ms"]
    port = svc["port"]

    endpoints = {ep["id"]: ep for ep in svc["endpoints"]}
    selected = [endpoints[eid] for eid in selected_endpoint_ids if eid in endpoints]

    # Build endpoint sections
    ep_sections = []
    for ep in selected:
        method = ep["method"]
        path = ep["path"]
        summary = ep["summary"]
        auth_req = "Yes" if ep["auth_required"] else "No"

        req_schema_lines = []
        for field, desc in ep["request_schema"].items():
            req_schema_lines.append(f"  - `{field}`: {desc}")
        req_schema = "\n".join(req_schema_lines) if req_schema_lines else "  _(no body)_"

        resp_schema_lines = []
        for field, desc in ep["response_schema"].items():
            resp_schema_lines.append(f"  - `{field}`: {desc}")
        resp_schema = "\n".join(resp_schema_lines) if resp_schema_lines else "  _(empty body)_"

        status_lines = []
        for code, desc in ep["status_codes"].items():
            status_lines.append(f"  - `{code}`: {desc}")
        status_block = "\n".join(status_lines)

        # Test cases as a table
        tc_rows = []
        for tc in ep.get("test_cases", []):
            tc_rows.append(f"  - {tc['desc']} → {tc['expected_status']}")
        tc_block = "\n".join(tc_rows) if tc_rows else "  _(see status codes)_"

        ep_sections.append(textwrap.dedent(f"""\
            ### `{method} {path}`

            **Summary**: {summary}
            **Auth required**: {auth_req}

            **Request schema**:
            {req_schema}

            **Response schema** (success):
            {resp_schema}

            **Status codes**:
            {status_block}

            **Expected test cases**:
            {tc_block}
        """))

    ep_text = "\n".join(ep_sections)
    ep_count = len(selected)

    return textwrap.dedent(f"""\
        # TEST3: Integration Tests — {display_name} Contract (Seed {seed})

        ## Overview

        The `{svc_name}` {svc["description"]}.
        A working implementation is provided at `server.py`. Your task is to write
        integration tests that fully verify the API contract below.

        ## Service Details

        | Property | Value |
        |----------|-------|
        | Base URL | `{base_url}` |
        | Auth header | `{auth_header}` |
        | Valid API key | `{valid_key}` |
        | Rate limit | {rate_limit} requests/minute |
        | Request timeout | {timeout_ms} ms |
        | Port | {port} |

        ## Authentication

        All endpoints marked "Auth required: Yes" must receive the header:

        ```
        {auth_header}: {valid_key}
        ```

        Requests missing this header or providing a wrong value **must** receive HTTP `401`.

        ## Endpoints ({ep_count} total)

        {ep_text}

        ## Error Response Format

        All error responses follow this shape:
        ```json
        {{"error": "<human-readable message>"}}
        ```

        ## Contract Guarantees

        1. All response bodies are JSON (`Content-Type: application/json`).
        2. Timestamps use ISO-8601 format (e.g. `"2024-01-15T10:30:00Z"`).
        3. IDs are UUID strings.
        4. The `/health` endpoint never requires authentication.
        5. Rate limiting: exceeding {rate_limit} requests/minute returns `429`.
        6. Timeouts: the server processes requests within {timeout_ms} ms under normal load.

        ## Deliverables

        - `tests/test_integration.py` with pytest tests.
        - Tests must pass against the running `server.py`.
        - Minimum {ep_count + 4} test functions.
        - Cover: status codes, response schemas, auth enforcement, error codes, 404 cases.

        ## Grading

        - Check 1: `tests/test_integration.py` exists.
        - Check 2: `/health` endpoint test present and passes.
        - Check 3: Auth enforcement tested (401 on missing key).
        - Check 4: 400 validation error cases tested.
        - Check 5: 404 not-found cases tested.
        - Check 6: Response schema fields verified (not just status codes).
        - Check 7: All tests pass against working server.
        - Check 8: Tests fail against broken server (mutation detection).
        - Check 9: Minimum test count ({ep_count + 4}+) met.
        - Check 10: Tests cover all {ep_count} endpoints.
        - Check 11: No hardcoded UUIDs from prior runs (tests create fresh resources).
        - Check 12: Content-Type header verified in at least one test.
    """)


def _build_brief_md(svc: dict) -> str:
    return textwrap.dedent(f"""\
        # TEST3: Integration Tests from Service Contract (Brief)

        The `{svc["service_name"]}` {svc["description"]}.
        The service lacks integration tests.

        Write tests that verify the API contract.

        - File to write: `tests/test_integration.py`
        - Run the server: `python server.py` (starts on port {svc["port"]})
        - Run tests: `python -m pytest tests/test_integration.py -v`
        - The Planner has the full API contract with all endpoint details.
    """)


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class Generator(TaskGenerator):
    task_id = "TEST3_integration"
    domain = "testing"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pick service type
        svc_idx = rng.randint(0, len(SERVICE_POOL) - 1)
        svc = SERVICE_POOL[svc_idx]

        # Pick 4-6 endpoints (always include health_check, then sample the rest)
        all_ep_ids = [ep["id"] for ep in svc["endpoints"]]
        non_health = [eid for eid in all_ep_ids if eid != "health_check"]
        num_endpoints = rng.randint(3, min(5, len(non_health)))
        sampled = rng.sample(non_health, num_endpoints)
        # health always included, put it last
        selected_endpoint_ids = sampled + ["health_check"]

        # Build workspace files
        server_py = _build_server_py(svc, selected_endpoint_ids)
        broken_server_py = _build_broken_server_py(svc, selected_endpoint_ids)
        test_skeleton = _build_test_skeleton(svc, selected_endpoint_ids)
        spec_md = _build_spec_md(svc, selected_endpoint_ids, seed)
        brief_md = _build_brief_md(svc)

        # requirements.txt for the server
        requirements_txt = "flask>=2.0\nrequests\npytest\n"

        workspace_files = {
            "server.py": server_py,
            "tests/__init__.py": "",
            "tests/test_integration.py": test_skeleton,
            "requirements.txt": requirements_txt,
            # Broken server stored for grader use
            "broken_server.py": broken_server_py,
        }

        endpoints = {ep["id"]: ep for ep in svc["endpoints"]}
        selected_eps = [endpoints[eid] for eid in selected_endpoint_ids if eid in endpoints]

        expected = {
            "service_name": svc["service_name"],
            "port": svc["port"],
            "auth_header": svc["auth_header"],
            "valid_api_key": svc["valid_api_key"],
            "endpoint_count": len(selected_endpoint_ids),
            "endpoint_ids": selected_endpoint_ids,
            "min_tests": len(selected_endpoint_ids) + 4,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )
