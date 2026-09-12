# GH1213_airflow_64216: Fix assume_role_with_web_identity not using botocore config for STS c… — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

When `assume_role_method` is set to `assume_role_with_web_identity`, the STS client used to fetch credentials was created without the connection's botocore config. This meant proxy settings, timeouts, and other config from `config_kwargs` in the connection extra were silently ignored.

The `assume_role` and `assume_role_with_saml` paths correctly pass `self.config` to the STS client, but the web identity path passed a raw `base_session.create_client` as `client_creator` to botocore's `AssumeRoleWithWebIdentityCredentialFetcher`, which never received the connection config.

This wraps `client_creator` to merge the connection's botocore config into any config that botocore passes when creating the STS client, ensuring proxy and other settings are respected.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
