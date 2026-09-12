# G3 mechanism breakdown

Companion to `g3_reference_summary.md`. It answers the question that table cannot: when the grader refuses the upstream fix, whose defect is it?

| Outcome | Tasks | Share of 631 |
|---|---:|---:|
| `a_validated` | 0 | 0.0% |
| `b_grader_rejects_reference` | 604 | 95.7% |
| `c_unappliable` | 11 | 1.7% |
| `d_inconclusive_grader_timeout` | 16 | 2.5% |
| `error` | 0 | 0.0% |

## Attribution inside bucket (b)

| Where the defect lives | Tasks | Share of 604 |
|---|---:|---:|
| staged workspace Python cannot parse or import, so no agent edit could ever pass a check that runs the code | 566 | 93.7% |
| staged workspace Python is clean; the failure is in the grader or its environment | 38 | 6.3% |

The first row is a **lower bound**: it is a static test for renamed Python builtins, renamed stdlib import targets, and files that no longer parse. It does not catch a renamed third-party module name, and running the graders' own commands found two further such tasks inside the 'clean' row.

## Measured cause of the C1 ("test suite passes") failure

Obtained by re-running each grader's own pytest target against the reference workspace and reading the error.

| Cause | Clean-Python bucket-(b) tasks | Sampled corrupt bucket-(b) tasks |
|---|---:|---:|
| `missing_dependency` | 18 | 0 |
| `no_tests_collected` | 13 | 0 |
| `not_measured` | 2 | 0 |
| `other` | 2 | 0 |
| `parameterisation_break` | 2 | 13 |
| `relative_import` | 1 | 0 |
| `syntax_error_from_parameterisation` | 0 | 2 |

`assertion` -- a test that actually disagrees with the upstream fix -- does not appear at all.

On 539 of the 604 bucket-(b) tasks (89.2%) the reference scores *exactly* the pristine do-nothing floor.

`missing_dependency` has a mechanical explanation: 598 of the 631 graders in this scope still contain the literal line `# TODO: add repo-specific dependencies`, the placeholder the PR-to-task converter emits where the repository's own dependencies were meant to be installed. Every one of those graders installs `pytest` and nothing else, then runs the repository's tests.

