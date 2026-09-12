# GH382_redis-py_3988: New abstract method added to ConnectionInterface. Adding more debug logs when processing maint notifications. Filtering some e2e tests for notifications on new connections. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/redis/redis-py

## PR Description

Adding more debug logs when processing maint notifications - helpful when troubleshooting tests. 
Filtering some e2e tests for notifications on new connections - maintenance in some specific cases ends too fast, and when new connections start to wait for notification, the maintenance has already ended.

<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> **Medium Risk**
> Adds a new abstract `extract_connection_details()` method to the connection interface and uses it in several failure paths, which could impact any custom connection implementations. Runtime behavior changes are otherwise limited to extra debug logging and test configuration tweaks.
> 
> **Overview**
> Improves troubleshooting for maintenance notifications and retry/disconnect flows by adding **debug-only** logs that include per-connection details (via a new `AbstractConnection.extract_connection_details()` API) when operations fail or cluster transactions are torn down.
> 
> Enhances scenario tests by supporting optional mTLS client certs for `RedisCluster` setup and by filtering out an unreliable effect/trigger combination in the “new connections receive last notification” parametrized test.
> 
> <sup>Written by [Cursor Bugbot](https://cursor.com/dashboard?tab=bugbot) for commit a642347126bfa11ed445f6e99d9eadce92292410. This will update automatically on new commits. Configure [here](https://cursor.com/dashboard?tab=bugbot).</sup>
<!-- /CURSOR_SUMMARY -->

## PR Review Comments

**[user]** on `redis/maint_notifications.py`:

### Unbound variable `notification` when kwarg is missing

**High Severity**

<!-- DESCRIPTION START -->
The `notification` variable is only assigned inside the `if kwargs.get("notification"):` block, but it's referenced unconditionally on the next line and again later. When `notification` is not in `kwargs`, the variable is never defined, causing a `NameError` at `notification if notification else "MAINTENANCE_COMPLETED"`. The existing test `test_handle_maintenance_completed_notification_success` calls this method without the kwarg and will crash. A simple fix would be `notification = kwargs.get("notification")` without wrapping it in an `if`.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: f7fe3c92-fa26-40da-a0fe-60cbd0be54ec -->

<!-- LOCATIONS START
redis/maint_notifications.py#L1008-L1023
LOCATIONS END -->
<p><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OmZkZTJlZDU2LTViZTEtNDU5ZC04ODNhLTcwMTQyZTIzNmYzMSIsImVuY3J5cHRpb25LZXkiOiJrdWF0aEFQemIwV0NLY1V1R19hR2dpU3lXODJ0aWt6Z1M5R1JjN3dvNkswIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSJ9LCJpYXQiOjE3NzI2Mzg5MjIsImV4cCI6MTc3NTIzMDkyMn0.RV0f-6ml6pOGm47O3Ki2EbqEMNCVfE6vciM3odglQH8FnH_zCe9ybE1eAvbNSoEh1uX64furhg8yCCXhSqtjPGWM7eva7fU33WSlfUMIXbT4ivTgLL-Y7ZmHnLJ9z6glFa2tGLe214jGjNNHam2qTx3Xkx-hnP9LViJbbvl69aZjvWi4w_1liXSXavh8uiEJjcctPOIUQOn_M7EPpeNv2tzaSpo2El685VRmKvjNck-p0nfVB2FlMAxgiySysPNnGEYgriJsTWsFWND7Y5X3e2BQX3CjkF7dZBXnmPeTXDY1ntuNaaEmvS3xbqHZ1k2D5sAOThQsS4a42F4jEkFW2g" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OmZkZTJlZDU2LTViZTEtNDU5ZC04ODNhLTcwMTQyZTIzNmYzMSIsImVuY3J5cHRpb25LZXkiOiJrdWF0aEFQemIwV0NLY1V1R19hR2dpU3lXODJ0aWt6Z1M5R1JjN3dvNkswIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSIsInByTnVtYmVyIjozOTg4LCJjb21taXRTaGEiOiJkODYxZmU3MTMzOTBmMTFmY2RhYmFiOGRkNGU3MDc3YjI0MjIwNTlhIiwicHJvdmlkZXIiOiJnaXRodWIifSwiaWF0IjoxNzcyNjM4OTIyLCJleHAiOjE3NzUyMzA5MjJ9.oVxcSOx5-igkHTD0ihvbzQWNgTNd538oOlZECK7utyADF0HvRZ4Cm-xgXvEkpgsBHmhSPs-jCYYB5oCdbkWvaXdAR2wnQChxb_n5tTLwYQHTHJz1JxorT9hF2HOf8brgZEWBt4Ck4kQeM5FSau2qcPnd7_PQaHl44EHF_D6YeVtqZS_bUqxXzAv67D0AQjXyx_eLCv6q_tDTmQP2JtdZHGnG8a9AxcI1zS8eQPI8qlgpoWMKOHf_9KE_hSMlZZZA9lN0H8m9LKotUdRVQHlqbl3VlCsT7OahGDN8G48_xTA5giYqV1nwa_ihFnCdNBgt1Iq2gXhXScKd8CPon20Abw" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></p>

**[user]** on `redis/maint_notifications.py`:

fixed.

**[user]** on `redis/cluster.py`:

### Duplicated debug logging code instead of reusing existing function

**Low Severity**

<!-- DESCRIPTION START -->
The inline debug logging code in `_reinitialize_on_error` duplicates the logic of `add_debug_log_for_operation_failure` from `redis/client.py` — same socket address extraction, same try/except pattern, same log message format. The function could be reused (it's already imported from `redis.client` in this file) or refactored to accept a logger parameter, rather than copy-pasting the implementation inline.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: ba1fe1ec-8dc9-4dd9-9be8-c553253f0ba2 -->

<!-- LOCATIONS START
redis/cluster.py#L3953-L3971
LOCATIONS END -->
<p><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjQxZDI4ZmQxLWZjMmItNGZjNi05YmMyLTYyOThlYTg3ZDcxMyIsImVuY3J5cHRpb25LZXkiOiJLeUFfZ0J3OElqMnJrQ19WR3FxakxiMnowZ29YRS1BRFllR1lWR3RLR1hjIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSJ9LCJpYXQiOjE3NzI3MTUxMzIsImV4cCI6MTc3NTMwNzEzMn0.mnTtc8ANN22J-Sp81OSjzqyVpxlEXwM8a3kGS88ZAmmS9qhjczN_ti22pVwGrzag0U3VSmvcQRR2wHvZl7kw9NXufT5ehPCJJcuNQu9gtVCPBf7R6g8kbP7WS3KlEwEQuGKH3LK4dxYRTNdvIF4GZGYCRU3dSKgFUdhWCMaSwd573Q5uXsBHKSC2mIaeB0xGwvs8D4RYgcg4KTGfGtxSdRDLTdfIV15x50hYivOIjh3Z_STPVTNTEcFVO8yLZnoMUbBeiMRNAYnR-VnYWJIjTemL6F3NFj2ORVuBRyaHXPeYhLgvxefms6WWZKSxsbBQuYr3JzVUEmmjGAeaTgLHAw" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjQxZDI4ZmQxLWZjMmItNGZjNi05YmMyLTYyOThlYTg3ZDcxMyIsImVuY3J5cHRpb25LZXkiOiJLeUFfZ0J3OElqMnJrQ19WR3FxakxiMnowZ29YRS1BRFllR1lWR3RLR1hjIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSIsInByTnVtYmVyIjozOTg4LCJjb21taXRTaGEiOiIwNDQ5YTc0N2VkNjYxY2I4MWZhZjM5N2UyMGFlNzc0M2ExYjFjZmMwIiwicHJvdmlkZXIiOiJnaXRodWIifSwiaWF0IjoxNzcyNzE1MTMyLCJleHAiOjE3NzUzMDcxMzJ9.EFviJnSfvKMANbtnjBP6syb51Bz5iwEEyvqDxBtLnLbACfEA57WxhAuC0JE-P-uZArEwBWoWoC6KOdBajb5oBBQDCUhsp3FiwUYUHq04Ly9cR-9EVhwyLJeuCFP-qUmjnJnaK0MtUGHoif26s-Z3qmTplNgLI-DHDDHqGDsPin2cPJBie5MQSDO7n5UE2lWWqnVRLweIArVxRqCk_GGYq1LlqLr4-zdXbkTX6HHpB2iuQ_N6iy9j4UHfadGRiOSLahmzTat8K2JsDntN2GvFCkOWJxuc8FhTUizEmbrfWkY-F2mqwwDLSXFShglr6UpIq_Z9JUKbFr_aU4_8lDKAGQ" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></p>

**[user]** on `redis/client.py`:

### Redundant debug log level check before guarded function

**Low Severity**

<!-- DESCRIPTION START -->
The `is_debug_log_enabled()` call wrapping `add_debug_log_for_operation_failure(conn)` is redundant — `add_debug_log_for_operation_failure` already starts with `if logger.isEnabledFor(logging.DEBUG)` using the same module-level `logger`. The double check adds unnecessary noise at all three call sites in the failure callbacks.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: f7056aa3-0b12-4d4d-9ffd-45edf2274d9a -->

<!-- LOCATIONS START
redis/client.py#L755-L757
redis/client.py#L1739-L1741
redis/client.py#L1978-L1980
LOCATIONS END -->
<details>
<summary>Additional Locations (2)</summary>

- [`redis/client.py#L1739-L1741`](https://github.com/redis/redis-py/blob/0449a747ed661cb81faf397e20ae7743a1b1cfc0/redis/client.py#L1739-L1741)
- [`redis/client.py#L1978-L1980`](https://github.com/redis/redis-py/blob/0449a747ed661cb81faf397e20ae7743a1b1cfc0/redis/client.py#L1978-L1980)

</details>

<p><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjM2ODEyM2RlLTY0NTYtNGMyNi1iOTNmLTczMTA4MmQ4ZmQ4OSIsImVuY3J5cHRpb25LZXkiOiJqdmEySFoxdWRIS3VmWlRGTTNTVVR4a2ZoSU5aOFhMV0htOHZfbGtVazdnIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSJ9LCJpYXQiOjE3NzI3MTUxMzIsImV4cCI6MTc3NTMwNzEzMn0.f6V2JCQf-KxACjF6A0gNlqVSiDG9yrTu5Et_ReU_SpUVHJOPGeuz5EMqLfvLDoDd1gKfNxngW1tgsbsI5a11XRn4zwZfAMK0FoCuGCSyE2v037DtXEGVKOaWdBNUHoBnRIl6pdB4n9GOAEfpLU_bcW-1lJlz7VuvJWtFrP64idX1XMKWfQuN9xZ7wcoG1EnebGMI48GQBWcrYYJwGF9_dpeWYfybKZgVBAcPFYK1fWQD8UN1cxcpp4YESwvR3RSoHJh3-8aPOF_jQTvmptj6xpFxqPYwTyO47zzuLQAIkKK0OENm2GLzEijn7kZ7f00bqlisto_bws5W-W_mGZSDcg" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjM2ODEyM2RlLTY0NTYtNGMyNi1iOTNmLTczMTA4MmQ4ZmQ4OSIsImVuY3J5cHRpb25LZXkiOiJqdmEySFoxdWRIS3VmWlRGTTNTVVR4a2ZoSU5aOFhMV0htOHZfbGtVazdnIiwiYnJhbmNoIjoicHNfYWRkX2RlYnVnX2xvZ3NfZm9yX3N0YW5kYWxvbmVfY2xpZW50X2R1cmluZ19tYWludCIsInJlcG9Pd25lciI6InJlZGlzIiwicmVwb05hbWUiOiJyZWRpcy1weSIsInByTnVtYmVyIjozOTg4LCJjb21taXRTaGEiOiIwNDQ5YTc0N2VkNjYxY2I4MWZhZjM5N2UyMGFlNzc0M2ExYjFjZmMwIiwicHJvdmlkZXIiOiJnaXRodWIifSwiaWF0IjoxNzcyNzE1MTMyLCJleHAiOjE3NzUzMDcxMzJ9.w5o52q44pF4gSvDJw1P267CGhXKhxca_Mz7X0Qze-_K6gZ2Djhqcm2gb5RVaVMX-32DWl8W6HJ5tCg95QxV5qzwD0Ql0mJqx6ScG0Di6WaO4zH52_I8VHu1NgYAD7vhWxBsym2I4UsKdn_c6RlcakjcPWgbsG-fh4oCCikpBrbDGcv6bfyLMmbUObNfVhyLyk3qo__fs690LP305tz1pmMak9iK1eDNjOgozgo5rEIZVbtniLkXv3WaUODSOS5fnsHtVOGrYZeflvjwQq8z4TtL0V4Sz8sgwp1fDY2oC3-HLcEH9HAToE2dpckJB8utL3OXF9-YQkLLFBBETpHLb2A" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></p>

**[user]** on `redis/client.py`:

Simplified.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
