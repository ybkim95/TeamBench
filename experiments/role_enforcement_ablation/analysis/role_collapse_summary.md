# Role-Collapse Audit (H1 evidence)

Source: role_compliance.jsonl; cells with condition=unknown excluded.

Violation rate = % of turns flagged by deterministic rubric in `04_score_compliance.py`.
Wilson 95% CIs reported in JSON output; this table shows point estimates only.

## Aggregate (pooled across models)

| Condition | Role | Turns | Violations | Rate |
|---|---|---:|---:|---:|
| prompt_only | planner | 2460 | 2 | 0.1% |
| prompt_only | executor | 4797 | 262 | 5.5% |
| prompt_only | verifier | 4463 | 374 | 8.4% |
| enforced_shared_history | planner | 1263 | 0 | 0.0% |
| enforced_shared_history | executor | 2209 | 295 | 13.4% |
| enforced_shared_history | verifier | 2690 | 208 | 7.7% |
| enforced | planner | 2218 | 0 | 0.0% |
| enforced | executor | 4404 | 421 | 9.6% |
| enforced | verifier | 5403 | 225 | 4.2% |

## Per-model breakdown

### claude_haiku_4_5

| Condition | Role | Runs | Turns | Violations | Rate |
|---|---|---:|---:|---:|---:|
| prompt_only | planner | 82 | 1350 | 0 | 0.0% |
| prompt_only | executor | 82 | 1391 | 177 | 12.7% |
| prompt_only | verifier | 82 | 1136 | 108 | 9.5% |
| enforced_shared_history | planner | 52 | 1016 | 0 | 0.0% |
| enforced_shared_history | executor | 52 | 1224 | 192 | 15.7% |
| enforced_shared_history | verifier | 52 | 1336 | 143 | 10.7% |
| enforced | planner | 50 | 960 | 0 | 0.0% |
| enforced | executor | 50 | 1255 | 234 | 18.6% |
| enforced | verifier | 50 | 1503 | 76 | 5.1% |

### gemini_3_flash

| Condition | Role | Runs | Turns | Violations | Rate |
|---|---|---:|---:|---:|---:|
| prompt_only | planner | 61 | 995 | 2 | 0.2% |
| prompt_only | executor | 61 | 2833 | 14 | 0.5% |
| prompt_only | verifier | 61 | 2918 | 198 | 6.8% |
| enforced_shared_history | planner | 6 | 120 | 0 | 0.0% |
| enforced_shared_history | executor | 6 | 254 | 3 | 1.2% |
| enforced_shared_history | verifier | 6 | 252 | 0 | 0.0% |
| enforced | planner | 52 | 1040 | 0 | 0.0% |
| enforced | executor | 52 | 1793 | 23 | 1.3% |
| enforced | verifier | 52 | 2153 | 43 | 2.0% |

### gpt_5_4_mini

| Condition | Role | Runs | Turns | Violations | Rate |
|---|---|---:|---:|---:|---:|
| prompt_only | planner | 50 | 115 | 0 | 0.0% |
| prompt_only | executor | 50 | 573 | 71 | 12.4% |
| prompt_only | verifier | 50 | 409 | 68 | 16.6% |
| enforced_shared_history | planner | 57 | 127 | 0 | 0.0% |
| enforced_shared_history | executor | 57 | 731 | 100 | 13.7% |
| enforced_shared_history | verifier | 57 | 1102 | 65 | 5.9% |
| enforced | planner | 97 | 218 | 0 | 0.0% |
| enforced | executor | 97 | 1356 | 164 | 12.1% |
| enforced | verifier | 97 | 1747 | 106 | 6.1% |

## Top violation types per condition (pooled)

**prompt_only**:
- `executor_plans`: 261
- `verifier_modifies_code`: 256
- `verifier_skips_tests`: 118
- `planner_writes_code`: 2
- `executor_self_approves`: 1

**enforced_shared_history**:
- `executor_plans`: 295
- `verifier_skips_tests`: 123
- `verifier_modifies_code`: 85

**enforced**:
- `executor_plans`: 416
- `verifier_skips_tests`: 153
- `verifier_modifies_code`: 72
- `executor_self_approves`: 5

