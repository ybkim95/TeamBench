# GH51_werkzeug_3091: Check event type before pattern matching in watchdog reloader — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3090
- Repo: https://github.com/pallets/werkzeug

## Issue Description

Werkzeug often reloads slowly when in `watchdog` mode for me. It can take 10 to 20 seconds before changes are noticed. This may be due to having a lot of `extra_files` being watched, I have ~110 extra files listed.

With `stat` reload mode the reload happens almost immediately.

Environment:

- Linux (`watchdog` uses `inotify`)
- Python version: 3.12.6
- Werkzeug version: 3.1.3

I did some testing and it appears that the `WatchdogReloaderLoop.EventHandler` in `_reloader.py` is a bit slow due to unnecessary pattern matching. This 
```
        class EventHandler(PatternMatchingEventHandler):
            def on_any_event(self, event: FileModifiedEvent):  # type: ignore
                if event.event_type not in {
                   EVENT_TYPE_CLOSED,
                   EVENT_TYPE_CREATED,
                   EVENT_TYPE_DELETED,
                   EVENT_TYPE_MODIFIED,
                   EVENT_TYPE_MOVED,
                }:
                   # skip events that don't involve changes to the file
                   return

                trigger_reload(event.src_path)
```
becomes much faster if irrelevant event types are discarded before pattern matching in `dispatch`:
```
        class EventHandler(PatternMatchingEventHandler):
            def dispatch(self, event: FileSystemEvent) -> None:
                if event.event_type not in {
                   EVENT_TYPE_CLOSED,
                   EVENT_TYPE_CREATED,
                   EVENT_TYPE_DELETED,
                   EVENT_TYPE_MODIFIED,
                   EVENT_TYPE_MOVED,
                }:
                   # skip events that don't involve changes to the file
                   return

                super().dispatch(event)

            def on_any_event(self, event: FileModifiedEvent):  # type: ignore
                trigger_reload(event.src_path)
```
This actually fixes the slowness issue for me and reloads are instant.

I have a pretty complex terminal prompt (doing git and python virtualenv stuff) that causes ~300 events to be sent to the dispatch method. Previously, holding enter in my terminal for a second would cause 100% core usage for 10 seconds in the dev server. With the changed version, core usage stays below 50% even if I hold enter indefinitely.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Seems fine, thanks for investigating. Happy to review a PR with that change.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
