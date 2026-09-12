# GH339_NeMo-Agent-Toolkit_787: fix(cli): nat workflow create should validate workflow name — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues/765
- Repo: https://github.com/NVIDIA/NeMo-Agent-Toolkit

## Issue Description

### Version

1.2.0

### Which installation method(s) does this occur on?

_No response_

### Describe the bug.

UI is accepting empty string as a folder name

<img width="231" height="235" alt="Image" src="https://github.com/user-attachments/assets/ee19fb75-50fc-4e31-ba8b-bae49422c1c6" />

### Minimum reproducible example

```shell
Click "New Folder" button. Enter empty name.
```

### Relevant log output

<details><summary>Click here to see error details</summary><pre>

 [Paste the error here, it will be hidden by default]

</pre></details>

### Other/Misc.

_No response_

### Code of Conduct

- [x] I agree to follow the NeMo Agent toolkit Code of Conduct
- [x] I have searched the [open bugs](https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues?q=is%3Aopen+is%3Aissue+label%3Abug) and have found no duplicates for this bug report

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], is this issue still open? If yes, I’d like to work on it.

### Comment 2 ([user]):

Yes it is open and you can work on a new MR/PR.

### Comment 3 ([user]):

Thanks for confirming! I’ll get started and will raise a PR once it’s ready

## PR Review Comments

**[user]** on `src/nat/cli/entrypoint.py`:

None of the changes in this file are necessary. Please revert.

**[user]** on `src/nat/cli/commands/workflow/__init__.py`:

None of the changes in this file are necessary. Please revert.

**[user]** on `tests/nat/cli/commands/test_workflow_commands.py`:

Please do not remove existing tests

**[user]** on `tests/nat/cli/commands/test_workflow_commands.py`:

If you leave this test in, then we should also delete the workflow that was created

**[user]** on `tests/nat/cli/commands/test_workflow_commands.py`:

_💡 Verification agent_

<details>
<summary>🧩 Analysis chain</summary>

**Align success-message assertion with implementation and verify side-effects; use the fixture.**

Implementation prints “created successfully in '<path>'”. Also assert the workflow directory exists.

[Code changes omitted — Planner should analyze the issue and guide the Executor]

Run locally to confirm the message format and symlink behavior:

---

🏁 Script executed:

```shell
#!/usr/bin/env bash
pytest -q tests/nat/cli/commands/test_workflow_commands.py -k "create_workflow" -vv -s
```

Length of output: 44

---

🏁 Script executed:

```shell
#!/bin/bash
set -euo pipefail
echo "=== show test file (tests/nat/cli/commands/test_workflow_commands.py) ==="
sed -n '1,240p' tests/nat/cli/commands/test_workflow_commands.py || true

echo
echo "=== search for create_command definitions/usages ==="
rg -n --hidden --no-ignore-vcs -S "create_command\b" || true

echo
echo "=== search for 'created successfully' messages in repo ==="
rg -n --hidden --no-ignore-vcs -S "created successfully" || true

echo
echo "=== search for 'created successfully in' exact phrase ==="
rg -n --hidden --no-ignore-vcs -S "created successfully in" || true

echo
echo "=== search for '--workflow-dir' occurrences ==="
rg -n --hidden --no-ignore-vcs -S "--workflow-dir|workflow-dir" || true

echo
echo "=== search for cli_runner / CliRunner fixtures/usages in tests ==="
rg -n --hidden --no-ignore-vcs -S "\bcli_runner\b|\bCliRunner\b" || true

echo
echo "=== list nat/cli/commands (if present) ==="
ls -R nat/cli/commands || true

echo
echo "=== show likely workflow command implementation file(s) ==="
rg -n --hidden --no-ignore-vcs -S "def create_command\(|def create_command\s*:" nat || true
rg -n --hidden --no-ignore-vcs -S "workflow_commands\.py|workflow/.*workflow_commands" || true
sed -n '1,240p' nat/cli/commands/workflow/workflow_commands.py || true

echo
echo "=== search for directory-creation calls (mkdir, mkdir_p, Path(...).mkdir, symlink_to) ==="
rg -n --hidden --no-ignore-vcs -S "mkdir\(|\.mkdir\(|symlink_to\(|symlink\(" || true

echo
echo "=== Done ==="
```

Length of output: 8153

---

</details>

**Align test assertion with implementation and verify created workflow directory**

- Update tests/nat/cli/commands/test_workflow_commands.py::test_create_workflow_with_valid_name to assert the substring "Workflow 'my-workflow' created successfully in" (implementation prints this at src/nat/cli/commands/workflow/workflow_commands.py:276) and add assert (tmp_path / "my-workflow").is_dir().
- Prefer using the project cli_runner fixture if one exists instead of instantiating CliRunner() directly.

<!-- fingerprinting:phantom:poseidon:chinchilla -->

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commits 618b5f9 to 583fbe1

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
