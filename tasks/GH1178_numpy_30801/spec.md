# GH1178_numpy_30801: TST: fix POWER VSX feature mapping — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

** Problem**
On POWER systems, the CPU feature tests check for a literal "VSX" flag in AT_HWCAP. However, Linux never reports a "VSX" auxv flag. VSX is a baseline capability implied by POWER ISA ≥ 2.06, so the test-side detection incorrectly reports VSX as unavailable, causing false failures on POWER (e.g. Power10,power9).

turns out theres another issue too - on some POWER systems AT_HWCAP shows up in hex format like 0xdc0065c2 instead of the string format with actual flag names. the existing load_flags_auxv() only works with string format so it just fails when its hex.

**This PR**

1. Maps VSX to ARCH_2_06, VSX2 to ARCH_2_07, VSX3 to ARCH_3_00, and VSX4 to ARCH_3_1B (fixed typo from ARCH_3_1)
2. Parses AT_PLATFORM to figure out the POWER generation (power7, power8, power9, power10 etc)
3. Uses the platform info to add the right ARCH flags based on which POWER version it is
4. Works on both hex and string AUXV formats now

**Changes**
 1.fixed the features_map with correct ISA levels
2.rewrote load_flags() to check AT_PLATFORM and infer ISA levels from that
3.added _get_platform() helper to get the platform string

**Note**
test-only change, no runtime behavior modified. should work on both POWER9 and POWER10 now.

Fixes gh-30529

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
