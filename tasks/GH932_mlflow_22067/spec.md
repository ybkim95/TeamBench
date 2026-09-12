# GH932_mlflow_22067: Fix assistant stream killed by unhandled `rate_limit_event` from Claude Code CLI — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/mlflow/mlflow/issues/22066
- Repo: https://github.com/mlflow/mlflow

## Issue Description

<!-- issue-warning -->
> [!WARNING]
> Before submitting a PR, please make sure that:
> - A maintainer has triaged this issue and applied the `ready` label
> - This issue has no assignee
> - No duplicate PR exists
>
> PRs not meeting these requirements may be automatically closed.

## Describe the problem

When using the MLflow Assistant with the Claude Code provider, the Claude Code CLI emits `rate_limit_event` messages in its `stream-json` output. The message parser in `ClaudeCodeProvider._parse_message_to_event()` does not handle this message type, causing it to fall through to the catch-all case which converts it into an `Event.from_error()`.

This error event is sent to the frontend via SSE, where the error handler in `AssistantService.ts` closes the `EventSource` connection. This terminates the entire stream before the actual assistant response arrives, making the assistant completely non-functional when rate limit events are present.

### Expected behavior

`rate_limit_event` messages should be silently skipped (like `system` messages), allowing the stream to continue and deliver the actual assistant response.

### Actual behavior

The assistant displays `Error: Unknown message type: rate_limit_event` and never returns a response. The SSE connection is closed on the first unhandled event.

## Root cause

Two contributing factors:

1. **Backend** (`mlflow/assistant/providers/claude_code.py:580-581`): The catch-all case in `_parse_message_to_event()` converts unknown message types into error events:
   ```python
   case _:
       return Event.from_error(f"Unknown message type: {message_type}")
   ```

2. **Frontend** (`mlflow/server/js/src/assistant/AssistantService.ts:250-266`): The SSE error listener closes the EventSource on any error event, terminating the stream:
   ```typescript
   eventSource.addEventListener('error', (event) => {
       // ... parses error and calls onError() ...
       eventSource.close();  // Kills the stream
   });
   ```

## Proposed fix

Add a case for `rate_limit_event` in the message parser to return `None` (skip it), same as `system` messages:

```python
case "rate_limit_event":
    return None
```

## Code to reproduce issue

1. Configure MLflow Assistant with Claude Code provider
2. Start MLflow server: `mlflow server`
3. Open the MLflow UI and send a message to the assistant
4. If the Claude API returns a rate limit event during streaming, the assistant will fail with `Error: Unknown message type: rate_limit_event`

## Affected files

- `mlflow/assistant/providers/claude_code.py` — message parser
- `mlflow/server/js/src/assistant/AssistantService.ts` — SSE error handling

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for the report, added the ready label

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
