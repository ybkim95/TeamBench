# GH407_bench_709: 🐛 Fix native gates handling for mirror circuits — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/munich-quantum-toolkit/bench/issues/654
- Repo: https://github.com/munich-quantum-toolkit/bench

## Issue Description

### System Information

All versions that support `generate_mirror_circuit`.

### Bug Description

When enabling the `generate_mirror_circuit` option in any of the target-specific benchmark levels, the resulting circuit does not respect the native gate set of the device any longer.
This is because `_create_mirror_circuit` simply inverts the gates, e.g., converting a native `sx` gate to a non-native `sxdg` gate.

### Steps to Reproduce

Simply request any circuit with `generate_mirror_circuit = True` for any target-specific benchmark.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I think it’s better to handle this directly within MQT Bench instead of relying on qiskit. My proposed solution is to extend the mirroring logic with a native-aware inversion function that checks each gate against the backend’s supported basis gates. If a gate is not native, it’s replaced using a predefined mapping to equivalent native sequences.

Example sketch:
```py
def native_inverse(qc, basis_gates, gate_map):
    qc_inv = QuantumCircuit(qc.num_qubits)
    for inst, qargs, _ in reversed(qc.data):
        name = inst.operation.name
        if name not in basis_gates and name in gate_map:
            for native_inst in reversed(gate_map[name]):
                qc_inv.append(native_inst, qargs)
        else:
            qc_inv.append(inst.inverse(), qargs)
    return qc_inv
```

This keeps the mirror generation consistent with the device’s native gate set while preserving layout and measurement structure. I’m happy to discuss or adjust the approach if you have other solutions in mind.

### Comment 2 ([user]):

> I think it’s better to handle this directly within MQT Bench instead of relying on qiskit. My proposed solution is to extend the mirroring logic with a native-aware inversion function that checks each gate against the backend’s supported basis gates. If a gate is not native, it’s replaced using a predefined mapping to equivalent native sequences.
> 
> Example sketch:
> 
> def native_inverse(qc, basis_gates, gate_map):
>     qc_inv = QuantumCircuit(qc.num_qubits)
>     for inst, qargs, _ in reversed(qc.data):
>         name = inst.operation.name
>         if name not in basis_gates and name in gate_map:
>             for native_inst in reversed(gate_map[name]):
>                 qc_inv.append(native_inst, qargs)
>         else:
>             qc_inv.append(inst.inverse(), qargs)
>     return qc_inv
> This keeps the mirror generation consistent with the device’s native gate set while preserving layout and measurement structure. I’m happy to discuss or adjust the approach if you have other solutions in mind.

Thanks for the suggestion here!
I believe that maintaining such a gate map of known inverses might be rather fragile and prone to breaking over time.
In my opinion, the preferred solution here would be to simply run Qiskit's native gate decomposition pass again over the final circuit.
This should be fairly straight-forward and should not require more than a handful lines of code.
[user] would you agree?

### Comment 3 ([user]):

Thanks [user] . Running Qiskit’s native gate decomposition again instead of maintaining a manual gate map is definitely a cleaner and more future-proof solution.
I am planning to update a `_create_mirror_circuit` accordingly by adding an optional `basis_gates` parameter and applying a light transpilation step after composing the inverse, like this
```py
def _create_mirror_circuit(qc_original: QuantumCircuit, inplace: bool = False, basis_gates: Optional[List[str]] = None) -> QuantumCircuit:
    target_qc = qc_original if inplace else qc_original.copy()
    target_qc.remove_final_measurements(inplace=True)
    qc_inv = target_qc.inverse()

    target_qc.barrier()
    target_qc.compose(qc_inv, inplace=True)

    # Ensure circuit only uses native gates
    if basis_gates is not None:
        from qiskit import transpile
        target_qc = transpile(target_qc, basis_gates=basis_gates, optimization_level=0)
   
    # Other implementation

    target_qc.measure_all()
    target_qc.name = f"{target_qc.name}_mirror"
    return target_qc
```
This keeps the mirror generation simple while ensuring the resulting circuit respects the target device’s native gate set. If this approach looks good to you, I'll go ahead an open a PR with the changes.

### Comment 4 ([user]):

> Thanks [user] . Running Qiskit’s native gate decomposition again instead of maintaining a manual gate map is definitely a cleaner and more future-proof solution. I am planning to update a `_create_mirror_circuit` accordingly by adding an optional `basis_gates` parameter and applying a light transpilation step after composing the inverse, like this
> 
> def _create_mirror_circuit(qc_original: QuantumCircuit, inplace: bool = False, basis_gates: Optional[List[str]] = None) -> QuantumCircuit:
>     target_qc = qc_original if inplace else qc_original.copy()
>     target_qc.remove_final_measurements(inplace=True)
>     qc_inv = target_qc.inverse()
> 
>     target_qc.barrier()
>     target_qc.compose(qc_inv, inplace=True)
> 
>     # Ensure circuit only uses native gates
>     if basis_gates is not None:
>         from qiskit import transpile
>         target_qc = transpile(target_qc, basis_gates=basis_gates, optimization_level=0)
>    
>     # Other implementation
> 
>     target_qc.measure_all()
>     target_qc.name = f"{target_qc.name}_mirror"
>     return target_qc
> This keeps the mirror generation simple while ensuring the resulting circuit respects the target device’s native gate set. If this approach looks good to you, I'll go ahead an open a PR with the changes.

This mostly looks good, yeah 👍🏼 
I'd probably directly pass in a Qiskit `Target` (well, actually `Target | None`), which we have available anyway as part of the compilation when targeting the native levels.
And I'd probably also pass in the original optimization level used for the compilation so that the transpile call might also perform some more optimization.
The only thing that would be good to ensure is that no routing is performed as part of the transpilation as this is costly and should be unnecessary. I am not 100% sure if Qiskit is clever enough to check whether the circuit can directly run and skip routing based on that.
Feel free to open a PR and we can take it from there.

### Comment 5 ([user]):

Thanks for the feedback! I’ll start with this implementation and then we can move on to the adjustments you suggested regarding passing the Target, using the original optimization level, and ensuring no unnecessary routing.

## PR Review Comments

**[user]** on `src/mqt/bench/benchmark_generation.py`:

_⚠️ Potential issue_ | _🔴 Critical_

**Fix docstring parameter name mismatch.**

The docstring references `basis_gates` (lines 88-89, 96-97), but the actual parameter is `target`. This inconsistency will confuse users.

Apply this diff to correct the docstring:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

Also applies to: 96-97

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/mqt/bench/benchmark_generation.py around lines 88-89 and 96-97, the
docstring incorrectly references a parameter named "basis_gates" while the
actual function parameter is "target"; update the docstring to use the correct
parameter name ("target") in both places (and if the intent was to document a
sub-attribute like target.basis_gates, make that explicit), ensuring the
description matches the function signature and removing or clarifying any
ambiguous references.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commits e8eaecf to b56db85

**[user]** on `src/mqt/bench/benchmark_generation.py`:

_⚠️ Potential issue_ | _🟠 Major_

**Fix parameter documentation errors.**

The docstrings contain inaccuracies:

- Line 96: `target` is a `Target` object, not "List of native gates". The `Target` class encapsulates the native gate set, connectivity, and other device properties.
- Line 97: "Optimization level of the device" should be "Optimization level for transpilation" since it controls the transpiler's optimization passes, not a device property.

Apply this diff:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
        target: Target object specifying the native gate set and device properties.
        optimization_level: Optimization level for the transpilation pass (0-3).
```

</details>

<!-- suggestion_end -->

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/mqt/bench/benchmark_generation.py around lines 96 to 97, the docstring
parameter descriptions are incorrect: change the `target` description to state
it is a Target object that encapsulates native gates, connectivity, and device
properties (not a List of native gates), and update `optimization_level` to read
that it is the optimization level for transpilation (controls transpiler
passes), not a device property; modify those two lines accordingly to reflect
the accurate types and meanings.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commits e8eaecf to b56db85

**[user]** on `src/mqt/bench/benchmark_generation.py`:

_⚠️ Potential issue_ | _🟡 Minor_

**Fix grammar and wording in docstring.**

The docstring contains two errors:
- "respect" should be "respects" (subject-verb agreement)
- "a list of target" should be "a target" (the parameter is a `Target` object, not a list)

Apply this diff:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
    Also ensures that the mirrored circuit respects the native gate set of the target device
    if a target is provided.
```

</details>

<!-- suggestion_end -->

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/mqt/bench/benchmark_generation.py around lines 88 to 89, the docstring
sentence has grammar/wording errors: change "respect" to "respects" for correct
subject-verb agreement and change "a list of target" to "a target" to reflect
that the parameter is a Target object; update the sentence so it reads something
like: "Also ensures that the mirrored circuit respects the native gate set of
the target device if a target is provided."
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `src/mqt/bench/benchmark_generation.py`:

_⚠️ Potential issue_ | _🟡 Minor_

**Add `seed_transpiler` for reproducibility.**

The transpilation logic correctly decomposes the mirror circuit to native gates without introducing new routing. However, for consistency with all other transpile calls in this file (lines 236, 314-317, 380-385), the `seed_transpiler` parameter should be included to ensure reproducible results.

Apply this diff:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

*Technical note: While `routing_method=None` reduces stochastic elements, optimization passes at higher levels may still have non-deterministic behavior without a seed.*

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
    # Transpile to ensure the final circuit uses only native gates
    if target is not None:
        target_qc = transpile(
            target_qc,
            target=target,
            optimization_level=optimization_level,
            routing_method=None,
            seed_transpiler=10,
        )
```

</details>

<!-- suggestion_end -->

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/mqt/bench/benchmark_generation.py around lines 116 to 118, the transpile
call lacks a seed for the transpiler which makes results non-reproducible; add
the seed_transpiler argument to the transpile invocation (use the same seed
variable used by other transpile calls in this file, e.g. seed or
seed_transpiler) so the call becomes transpile(..., routing_method=None,
seed_transpiler=<existing_seed_variable>), keeping the rest of the parameters
unchanged.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `src/mqt/bench/benchmark_generation.py`:

_🧹 Nitpick_ | _🔵 Trivial_

<details>
<summary>🧩 Analysis chain</summary>

**Verify the fix resolves issue #654.**

The callers correctly pass `target` and `optimization_level` to ensure mirror circuits respect the native gate set. The implementation looks correct and should resolve the reported bug.

Run this script to verify that mirror circuits now honor the target's native gate set:

Based on learnings: Qiskit 2.1.x transpiler correctly handles Target objects for native gate decomposition when routing_method=None is specified.

Also applies to: 389-389

---

🏁 Script executed:

```shell
#!/bin/bash
# Description: Verify mirror circuits use native gates for a target device.
# Expected: Mirror circuit should only contain gates from the target's basis_gates.

# Search for test files related to mirror circuits
fd -e py -E __pycache__ -E .venv test.*mirror

# Check if there are existing tests for the native gate fix
rg -n "generate_mirror_circuit.*True" --type py -C 3

# Look for test assertions that verify native gate compliance
rg -n "target.*basis_gates" --type py -C 2
```

Length of output: 5034

---

🏁 Script executed:

```shell
#!/bin/bash
# Locate the definition of _create_mirror_circuit and inspect transpile usage
rg -n "def _create_mirror_circuit" -C10 --type py
```

Length of output: 2015

---

🏁 Script executed:

```shell
#!/bin/bash
# Display full body of _create_mirror_circuit
sed -n '78,150p' src/mqt/bench/benchmark_generation.py
```

Length of output: 3075

---

</details>

**Approve issue #654 fix**  
Callers now correctly pass `target` and `optimization_level` into `_create_mirror_circuit`, and its implementation invokes `transpile(..., target=target, optimization_level, routing_method=None)`, ensuring mirror circuits use the device’s native basis gates. Optionally add a test asserting that the resulting `qc_mirror` contains only `target.basis_gates`.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/mqt/bench/benchmark_generation.py around line 323, update the
_create_mirror_circuit implementation so it accepts and uses the passed target
and optimization_level: call transpile(compiled_circuit, target=target,
optimization_level=optimization_level, routing_method=None) (ensuring
routing_method is explicitly None) so the mirrored circuit is transpiled to the
device native basis gates; optionally add a unit test that generates a mirror
circuit and asserts all gate names in qc_mirror are contained in
target.basis_gates.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
