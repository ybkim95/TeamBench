# GH1206_FLAML_1477: Fix BlendSearch OptunaSearch warning for non-hierarchical spaces with Ray Tune domains — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

BlendSearch issues a warning when using Ray Tune domains in non-hierarchical search spaces: "You passed a `space` parameter to OptunaSearch that contained unresolved search space definitions."

```python
from ray import tune
from flaml.tune.searcher.blendsearch import BlendSearch

# Previously triggered warning
searcher = BlendSearch(
    metric='loss',
    mode='min',
    space={'lr': tune.uniform(0.001, 0.1), 'depth': tune.randint(1, 10)}
)
```

## Changes

- **blendsearch.py**: Always use define-by-run mode when passing spaces to Ray's OptunaSearch, not just for hierarchical spaces. Ray's OptunaSearch expects either Optuna distributions or a callable define-by-run function, not Ray Tune domain objects.

- **test_searcher.py**: Add regression test capturing stderr to verify warning is eliminated.

CFO remains unaffected (doesn't use global search). The `evaluated_rewards` parameter continues to be correctly set to `None` for define-by-run mode.

> [!WARNING]
>
> <details>
> <summary>Firewall rules blocked me from connecting to one or more addresses (expand for details)</summary>
>
> #### I tried to connect to the following addresses, but was blocked by firewall rules:
>
> - `metadata.google.internal`
>   - Triggering command: `/usr/bin/python3 /usr/bin/python3 /home/REDACTED/.local/lib/python3.12/site-packages/ray/dashboard/dashboard.py --host=127.0.0.1 --port=8265 --port-retries=50 --temp-dir=/tmp/ray --log-dir=/tmp/ray/session_2026-01-10_08-37-43_892531_3832/logs --session-dir=/tmp/ray/session_2026-01-10_08-37-43_892531_3832 --logging-rotate-bytes=536870912 --logging-rotate-backup-count=5 --gcs-address=127.0.0.1:43919 --cluster-id-hex=97d382d349ced6bc4406879caed009b547b42c9aad36ac5cd3305571 --node-ip-address=127.0.0.1 --stdout-filepath=/tmp/ray/session_2026-01-10_08-37-43_892531_3832/logs/dashboard.out --stderr-filepath=/tmp/ray/session_2026-01-10_08-37-43_892531_3832/logs/dashboard.err --minimal pull.rebase` (dns block)
>   - Triggering command: `/usr/bin/python3 /usr/bin/python3 /home/REDACTED/.local/lib/python3.12/site-packages/ray/dashboard/dashboard.py --host=127.0.0.1 --port=8265 --port-retries=50 --temp-dir=/tmp/ray --log-dir=/tmp/ray/session_2026-01-10_08-38-34_168600_4240/logs --session-dir=/tmp/ray/session_2026-01-10_08-38-34_168600_4240 --logging-rotate-bytes=536870912 --logging-rotate-backup-count=5 --gcs-address=127.0.0.1:46054 --cluster-id-hex=fb1fa4f56b7d156e008fbba8f39cdf69844e221bfd3ffd5b729b74c4 --node-ip-address=127.0.0.1 --stdout-filepath=/tmp/ray/session_2026-01-10_08-38-34_168600_4240/logs/dashboard.out --stderr-filepath=/tmp/ray/session_2026-01-10_08-38-34_168600_4240/logs/dashboard.err --minimal .js` (dns block)
>   - Triggering command: `/usr/bin/python3 /usr/bin/python3 /home/REDACTED/.local/lib/python3.12/site-packages/ray/dashboard/dashboard.py --host=127.0.0.1 --port=8265 --port-retries=50 --temp-dir=/tmp/ray --log-dir=/tmp/ray/session_2026-01-10_08-40-16_435306_4778/logs --session-dir=/tmp/ray/session_2026-01-10_08-40-16_435306_4778 --logging-rotate-bytes=536870912 --logging-rotate-backup-count=5 --gcs-address=127.0.0.1:45251 --cluster-id-hex=12830389913f810d52524c2e0628c76352cbd9da533c1b2c9ada2482 --node-ip-address=127.0.0.1 --stdout-filepath=/tmp/ray/session_2026-01-10_08-40-16_435306_4778/logs/dashboard.out --stderr-filepath=/tmp/ray/session_2026-01-10_08-40-16_435306_4778/logs/dashboard.err --minimal` (dns block)
>
> If you need me to access, download, or install something from one of these locations, you can either:
>
> - Configure [Actions setup steps](https://gh.io/copilot/actions-setup-steps) to set up my environment, which run before the firewall is enabled
> - Add the appropriate URLs or hosts to the custom allowlist in this repository's [Copilot coding agent settings](https://github.com/microsoft/FLAML/settings/copilot/coding_agent) (admins only)
>
> </details>

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>BlendSearch in UDF mode</issue_title>
> <issue_description>When I select the BlendSearch search algorithm, I consistently encounter the following warning, whereas it does not appear when using CFO:
> 
> You passed a `space` parameter to OptunaSearch that contained unresolved search space definitions. OptunaSearch should however be instantiated with fully configured search spaces only. To use Ray Tune's automatic search space conversion, pass the space definition as part of the `param_space` argument to `tune.Tuner()` instead.</issue_description>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes microsoft/FLAML#1283

<!-- START COPILOT CODING AGENT TIPS -->
---

💡 You can make Copilot smarter by setting up custom instructions, customizing its development environment and configuring Model Context Protocol (MCP) servers. Learn more [Copilot coding agent tips](https://gh.io/copilot-coding-agent-tips) in the docs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
