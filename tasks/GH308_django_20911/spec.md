# GH308_django_20911: Fixed #36960 -- Enabled the use of psycopg 3's optimized timestamp loader. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

#### Trac ticket number

ticket-36960

#### Branch description

Even when available via psycopg-c or psycopg-binary, Django would never use the optimized C implementation of timestamp loaders.

This changes the implementation to load a reference to the actual registered timestamptz loader class from psycopg instead of deriving from the always-Python impl.

This was based on Daniele Varrazzo's code from https://github.com/psycopg/psycopg/issues/1273#issuecomment-3986829769.

On my machine, this speeds up a `assert list(SomeModel.objects.values_list("ctime", flat=True))` benchmark (where the length of the list ends up being some 100,000 items) with psycopg-binary==3.3.3 from 12.543 s ± 0.084 s to 4.647 s ± 0.039 s.

#### AI Assistance Disclosure (REQUIRED)

- [x] **No AI tools were used** in preparing this PR.
- [ ] **If AI tools were used**, I have disclosed which ones, and fully reviewed and verified their output.

#### Checklist
- [x] This PR follows the [contribution guidelines](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/submitting-patches/).
- [x] This PR **does not** disclose a security vulnerability (see [vulnerability reporting](https://docs.djangoproject.com/en/stable/internals/security/)).
- [x] This PR targets the `main` branch. <!-- Backports will be evaluated and done by mergers, when necessary. -->
- [x] The commit message is written in past tense, mentions the ticket number, and ends with a period (see [guidelines](https://docs.djangoproject.com/en/dev/internals/contributing/committing-code/#committing-guidelines)).
- [x] I have not requested, and will not request, an automated AI review for this PR. <!-- You are welcome to do so in your own fork. -->
- [x] I have checked the "Has patch" ticket flag in the Trac system.
- [ ] I have added or updated relevant tests.
  - No tests needed, I don't think? (One could add a test to check that the class we borrow is the optimized one if the test is being run with optimized classes available, but eh...).  
- [ ] I have added or updated relevant docs, including release notes if applicable
  - Not yet. Does this need doc updates? Of course it'd be nice to note that psycopg 3 support is better and faster.
- [ ] I have attached screenshots in both light and dark modes for any UI changes.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
