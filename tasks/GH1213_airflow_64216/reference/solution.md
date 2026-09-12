# Reference solution — GH1213_airflow_64216

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1213_airflow_64216`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1213_airflow_64216/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `providers/amazon/src/airflow/providers/amazon/aws/hooks/base_aws.py` (modified, +9/-2)
- `providers/amazon/tests/unit/amazon/aws/hooks/test_base_aws.py` (modified, +54/-7)

## Diff Summary (What the Fix Changes)

### `providers/amazon/src/airflow/providers/amazon/aws/hooks/base_aws.py`
```diff
@@ -412,8 +412,15 @@ def _fetch_saml_assertion_using_http_spegno_auth(self, saml_config: dict[str, An
     def _get_web_identity_credential_fetcher(
         self,
     ) -> botocore.credentials.AssumeRoleWithWebIdentityCredentialFetcher:
-        base_session = self.basic_session._session or botocore.session.get_session()
-        client_creator = base_session.create_client
+        session_config = self.config
+        endpoint_url = self.conn.get_service_endpoint_url("sts", sts_connection_assume=True)
+
+        def client_creator(service_name, **kwargs):
+            config = kwargs.pop("config", None)
+            if session_config:
+                config = session_config.merge(config) if config else session_config
+            return self.basic_session.client(service_name, config=config, endpoint_url=endpoint_url, **kwargs)
+
         federation = str(self.extra_config.get("assume_role_with_web_identity_federation"))
 
         web_identity_token_loader = {
```

## Moved from `brief.md`

## Files That May Need Changes

- `providers/amazon/src/airflow/providers/amazon/aws/hooks/base_aws.py`
