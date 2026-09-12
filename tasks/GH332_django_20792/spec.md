# GH332_django_20792: Fixed #36958 -- Reloaded logging config when logging settings are changed in tests. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

#### Trac ticket number
<!-- Replace XXXXX with the corresponding Trac ticket number. -->
<!-- Or delete the line and write "N/A" if this is a trivial PR. -->

ticket-36958

#### Branch description
Currently, when the `LOGGING` or `LOGGING_CONFIG` settings change during tests, such as through `@override_settings`, the test client does not adjust the Python logging module to align with the new settings.

This PR fixes the problem by adding a `setting_changed` signal receiver to `django/test/signals.py`. The receiver automatically calls `configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)` whenever these settings are changed.

A regression test has also been added to `tests/logging_tests/tests.py` to ensure that the logger's level updates correctly when the setting is overridden.

#### AI Assistance Disclosure (REQUIRED)
<!-- Please select exactly ONE of the following: -->
- [x] **No AI tools were used** in preparing this PR.
- [ ] **If AI tools were used**, I have disclosed which ones, and fully reviewed and verified their output.

#### Checklist
- [x] This PR follows the [contribution guidelines](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/submitting-patches/).
- [x] This PR **does not** disclose a security vulnerability (see [vulnerability reporting](https://docs.djangoproject.com/en/stable/internals/security/)).
- [x] This PR targets the `main` branch. <!-- Backports will be evaluated and done by mergers, when necessary. -->
- [x] The commit message is written in past tense, mentions the ticket number, and ends with a period.
- [x] I have checked the "Has patch" ticket flag in the Trac system.
- [x] I have added or updated relevant tests.
- [ ] I have added or updated relevant docs, including release notes if applicable.
- [ ] I have attached screenshots in both light and dark modes for any UI changes.

## PR Review Comments

**[user]** on `tests/logging_tests/tests.py`:

There is already a similar test class (`SetupConfigureLogging(SimpleTestCase)`) defined above. Rather than creating a separate class, it would be better to include this as an additional method in that existing class.

```python
class SetupConfigureLogging(SimpleTestCase):
    . . . .
```

**[user]** on `tests/logging_tests/tests.py`:

```suggestion
```
`import logging` is already present at the top of the file, so there is no need to import it again inside the override_settings

**[user]** on `tests/logging_tests/tests.py`:

The docstring states, “The test client should reload logging configuration,” but this is not related to the test client (`django.test.Client`). The implementation is actually about the `setting_changed` signal handler in response to `override_settings`. Therefore, it seems that the description should be revised to better reflect the actual behavior.

**[user]** on `tests/logging_tests/tests.py`:

It does verify that logging is reconfigured, but it does not check whether the configuration is restored when exiting the with block. Since the setting_changed signal also fires on exit, it would be better to verify the restoration as well.

```python
original_level = logger.level
with override_settings(LOGGING=new_logging):
		logger = logging.getLogger("django.test_custom_logger")
		self.assertEqual(logger.level, logging.WARNING)
self.assertEqual(logger.level, original_level)
```

**[user]** on `django/test/signals.py`:

Question: Why import settings here rather than in the file?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
