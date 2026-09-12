# Reference solution — GH1031_mlflow_21922

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1031_mlflow_21922`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1031_mlflow_21922/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/gateway/providers/anthropic.py` (modified, +58/-5)
- `mlflow/metrics/genai/model_utils.py` (modified, +64/-7)
- `tests/gateway/providers/test_anthropic.py` (modified, +141/-1)
- `tests/metrics/genai/test_model_utils.py` (modified, +182/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/gateway/providers/anthropic.py`
```diff
@@ -23,6 +23,47 @@
 _logger = logging.getLogger(__name__)
 
 
+class _UnsupportedSchemaError(Exception):
+    """Schema contains constructs that Anthropic structured outputs cannot represent."""
+
+
+def _enforce_strict_schema(schema: dict[str, Any]) -> None:
+    """Recursively set ``additionalProperties: false`` on object types that have ``properties``.
+
+    Anthropic's structured outputs require every object node to explicitly set
+    ``additionalProperties: false``. Pydantic-generated schemas often violate
+    this — for example, ``dict[str, str]`` produces:
+
+        // Rejected by Anthropic (400)
+        {"type": "object", "additionalProperties": {"type": "string"}}
+
+    This function rewrites it to:
+
+        // Accepted by Anthropic
+        {"type": "object", "additionalProperties": false}
+
+    Objects without ``properties`` (i.e. free-form dicts like ``dict[str, str]``)
+    are left unchanged so the model can still populate them with arbitrary keys.
+    """
+    if not isinstance(schema, dict):
+        return
+    if schema.get("type") == "object":
+        if "properties" not in schema:
+            raise _UnsupportedSchemaError(
+                "Object type without 'properties' (free-form dict) cannot be represented "
+                "with Anthropic structured outputs, which require additionalProperties: false."
+            )
+        schema["additionalProperties"] = False
+    for value in schema.values():
+        match value:
+            case dict():
+                _enforce_strict_schema(value)
+            case list():
+                for item in value:
+                    if isinstance(item, dict):
+                        _enforce_strict_schema(item)
+
+
 class AnthropicAdapter(ProviderAdapter):
     @classmethod
     def chat_to_model(cls, payload, config):
@@ -141,12 +182,24 @@ def chat_to_model(cls, payload, config):
         if response_format := payload.pop("response_format", None):
             if response_format.get("ty
```

### `mlflow/metrics/genai/model_utils.py`
```diff
@@ -127,6 +127,44 @@ def _is_supported_llm_provider(schema: str) -> bool:
     return schema in provider_registry.keys()
 
 
+_MODELS_WITHOUT_OUTPUT_CONFIG: set[tuple[str, str]] = set()
+
+
+def _is_unsupported_output_format_error(exc: MlflowException) -> bool:
+    """Check if the error indicates the model doesn't support structured output.
+
+    Older Anthropic models (e.g. claude-sonnet-4-20250514) don't support ``output_config``
+    and return a 400 with::
+
+        {
+            "type": "error",
+            "error": {
+                "type": "invalid_request_error",
+                "message": "'claude-sonnet-4-20250514' does not support output format.",
+            },
+        }
+
+    Newer models (e.g. claude-sonnet-4-5-20250929) support it.
+    """
+    match exc.__cause__:
+        case requests.exceptions.HTTPError(
+            response=requests.Response(status_code=400) as response,
+        ):
+            try:
+                body = response.json()
+            except Exception:
+                return False
+            match body:
+                case {
+                    "error": {
+                        "type": "invalid_request_error",
+                        "message": str(msg),
+                    }
+                }:
+                    return "does not support output format" in msg.lower()
+    return False
+
+
 def _call_llm_provider_api(
     provider_name: str,
     model: str,
@@ -208,11 +246,28 @@ def _call_llm_provider_api(
             )
         response = provider._request(chat_payload)
     else:
-        response = _send_request(
-            endpoint=proxy_url or provider.get_endpoint_url("llm/v1/chat"),
-            headers=provider.headers | extra_headers,
-            payload=chat_payload,
-        )
+        if (provider_name, model) in _MODELS_WITHOUT_OUTPUT_CONFIG:
+            chat_payload.pop("output_config", None)
+            chat_payload.pop("response_format", None)
+
+        try:
+            response
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `mlflow/gateway/providers/anthropic.py`
- `mlflow/metrics/genai/model_utils.py`
