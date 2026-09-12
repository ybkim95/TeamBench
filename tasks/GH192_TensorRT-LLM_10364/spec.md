# GH192_TensorRT-LLM_10364: [TRTLLM-10362][feat] Added Mamba and MLA layers to the sharding tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/NVIDIA/TensorRT-LLM/issues/10362
- Repo: https://github.com/NVIDIA/TensorRT-LLM

## Issue Description

### 🚀 The feature, motivation and pitch

Currently, `test_tp_sharing.py` covers only GQA, MLP, and a single linear layer. MLA and Mamba layers require dedicated logic, which is essential for Nemotron and DeepSeek model support.

### Alternatives

_No response_

### Additional context

_No response_

### Before submitting a new issue...

- [x] Make sure you already searched for relevant issues, and checked the [documentation](https://nvidia.github.io/TensorRT-LLM/) and [examples](https://github.com/NVIDIA/TensorRT-LLM/tree/main/examples) for answers to frequently asked questions.

## PR Review Comments

**[user]** on `tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py`:

_⚠️ Potential issue_ | _🟡 Minor_

<details>
<summary>🧩 Analysis chain</summary>

🏁 Script executed:

```shell
# First, let's view the file to understand the structure and find the base_model_tp_plan
wc -l tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py
```

Repository: NVIDIA/TensorRT-LLM

Length of output: 158

---

🏁 Script executed:

```shell
# Read the base_model_tp_plan definition around line 44
sed -n '30,80p' tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py
```

Repository: NVIDIA/TensorRT-LLM

Length of output: 1668

---

🏁 Script executed:

```shell
# Read the MLA_Block pattern detection section (lines 549-573 and surrounding context)
sed -n '540,580p' tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py
```

Repository: NVIDIA/TensorRT-LLM

Length of output: 1749

---

🏁 Script executed:

```shell
# Also check if there's any other reference to q_a_proj in the file
rg "q_a_proj" tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py -n -B 2 -A 2
```

Repository: NVIDIA/TensorRT-LLM

Length of output: 1251

---

</details>

**Add explicit skip condition for `q_a_proj` in MLA_Block pattern detection.**

The pattern detection expects `q_a_proj` to be sharded column-wise (falls into the `else` branch at line 561), but `base_model_tp_plan` at line 44 defines `"q_a_proj": "gather"` (no sharding). The comment at lines 552-554 also omits `q_a_proj`, only mentioning `q_b_proj`, `kv_b_proj`, and `kv_a_proj_with_mqa`, which suggests it may have been overlooked.

Add an explicit condition to skip `q_a_proj` sharding:

<details>
<summary>Fix</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]

Also update the comment at lines 552-554 to explicitly document `q_a_proj: gather (no sharding)`.

</details>

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
        elif model_cls == MLA_Block:
            for node in gm.graph.nodes:
                if is_linear_op(node):
                    # kv_a_proj_with_mqa: gather (no sharding)
                    # q_b_proj/kv_b_proj: column-wise
                    # o_proj: row-wise with all_reduce
                    if "o_proj" in node.args[1].name:
                        dim = SplitDimension.ROW
                        dist_op = "all_reduce"
                    elif "kv_a_proj_with_mqa" in node.args[1].name:
                        # This is gather, skip sharding
                        continue
                    elif "q_a_proj" in node.args[1].name:
                        # This is gather, skip sharding
                        continue
                    else:
                        dim = SplitDimension.COLUMN
                        dist_op = None
                    expected_transformations.append(
                        WeightShardingInfo(
                            target_node=node.name,
                            split_dim=dim,
                            config=config,
                            dist_op=dist_op,
                            min_local_shape=1,
                            layer_type=LayerType.ATTENTION,
                        )
                    )
```

</details>

<!-- suggestion_end -->

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In
tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py
around lines 549 to 573, the MLA_Block handling currently skips
kv_a_proj_with_mqa but mistakenly treats q_a_proj as column-sharded; add an
explicit condition before the else to skip nodes whose name contains "q_a_proj"
(i.e., continue when "q_a_proj" in node.args[1].name), and update the nearby
comment at lines ~552-554 to list "q_a_proj: gather (no sharding)" along with
the other projections.
```

</details>

<!-- fingerprinting:phantom:medusa:ocelot -->

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py`:

left on purpose?

**[user]** on `tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py`:

Fixed

**[user]** on `tests/integration/defs/accuracy/test_llm_api_autodeploy.py`:

Nit: is there any way we could mark `4` as `pytest.mark.skipif` when the available world size is not large enough?

**[user]** on `tests/unittest/_torch/auto_deploy/unit/multigpu/transformations/library/test_tp_sharding.py`:

Just out of curiosity - was this change related to the mamba issue, or "just" added for more test coverage? If the former, could you explain how it affected the mamba mixer layer?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
