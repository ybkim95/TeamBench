# Reference solution — GH509_django_20028

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH509_django_20028`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH509_django_20028/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `django/contrib/humanize/templatetags/humanize.py` (modified, +4/-1)
- `tests/humanize_tests/locale/fr/LC_MESSAGES/django.mo` (added, +0/-0)
- `tests/humanize_tests/locale/fr/LC_MESSAGES/django.po` (added, +74/-0)
- `tests/humanize_tests/tests.py` (modified, +8/-2)

## `django/contrib/humanize/templatetags/humanize.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `django/contrib/humanize/templatetags/humanize.py`
