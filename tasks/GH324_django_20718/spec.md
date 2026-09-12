# GH324_django_20718: Fixed #36926 -- Made admin use boolean icons for related BooleanFields in list_display — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

#### Trac ticket number

[ticket-36926](https://code.djangoproject.com/ticket/36926)

#### Branch description
When using related field lookups in list_display:
```
class GrandChildAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent__is_active']  # parent__is_active is a BooleanField
```
**Before the fix**:
Displayed: True or False (as plain text)
Users had to create workaround methods with @admin.display(boolean=True)

**After the fix**:

Displays: ✅ (green checkmark) or ❌ (red X icon)
Works automatically, just like direct BooleanFields

<img width="1512" height="735" alt="Screenshot 2026-02-17 at 2 07 14 AM" src="https://github.com/user-attachments/assets/0ba87420-6b93-4198-b5c4-08b68a2ae957" />
<img width="1512" height="735" alt="Screenshot 2026-02-17 at 2 07 07 AM" src="https://github.com/user-attachments/assets/03a805de-c8d0-4dbb-b1e8-b34232347997" />

#### AI Assistance Disclosure (REQUIRED)
<!-- Please select exactly ONE of the following: -->
- [ ] **No AI tools were used** in preparing this PR.
- [x] **If AI tools were used**, I have disclosed which ones, and fully reviewed and verified their output.

#### Checklist
- [x] This PR follows the [contribution guidelines](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/submitting-patches/).
- [x] This PR **does not** disclose a security vulnerability (see [vulnerability reporting](https://docs.djangoproject.com/en/stable/internals/security/)).
- [x] This PR targets the `main` branch. <!-- Backports will be evaluated and done by mergers, when necessary. -->
- [x] The commit message is written in past tense, mentions the ticket number, and ends with a period.
- [x] I have checked the "Has patch" ticket flag in the Trac system.
- [x] I have added or updated relevant tests.
- [ ] I have added or updated relevant docs, including release notes if applicable.
- [x] I have attached screenshots in both light and dark modes for any UI changes.

## PR Review Comments

**[user]** on `django/contrib/admin/utils.py`:

Did you look into centralizing `f = None` outside the main try/except?

**[user]** on `tests/admin_changelist/tests.py`:

I would just save the return value of the create() calls instead of refetching.

**[user]** on `django/contrib/admin/utils.py`:

Should let this exception rise? Toying with your test case shows that this should already raise an error elsewhere. Also, `NotRelationField` is not caught.

**[user]** on `django/contrib/admin/utils.py`:

I've refactored the code to centralize `f = None` at the start of the 
exception handler. This eliminated 5 redundant assignments throughout 
the conditional branches and simplified the exception handling at line 317 to just 
use `pass`. The logic remains the same but is now cleaner.

**[user]** on `tests/admin_changelist/tests.py`:

Fixed! Changed the test to store the return values:

child_active = Child.objects.create(name="Active Child", parent=parent, is_active=True)
child_inactive = Child.objects.create(name="Inactive Child", parent=parent, is_active=False)

This eliminates the unnecessary .get() refetches.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
