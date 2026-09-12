# GH1136_pytorch_176783: [inductor] Fix Identity comparability and evalf recursion — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/175856
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

```python benchmarks/dynamo/timm_models.py --inference --amp --amp-dtype float16 -d cuda -n10 --accuracy --disable-cudagraphs --only volo_d1_224 --cold-start-latency --backend=inductor```

Both cuda and xpu will run into maximum recursion depth exceeded error. guilty pr is (withheld: the upstream fix is not part of the task). to run this model, you will need add ```volo_d1_224 128``` in https://github.com/pytorch/pytorch/blob/main/benchmarks/dynamo/timm_models_list.txt

### Error logs

```
~/jianyi/pytorch# python benchmarks/dynamo/timm_models.py --inference --amp --amp-dtype float16 -d cuda -n10 --accuracy --disable-cudagraphs --only volo_d1_224 --cold-start-latency --backend=inductor
loading model: 0it [00:02, ?it/s]
cuda eval  volo_d1_224
ERROR:common:
Traceback (most recent call last):
  File "/mnt/ssd1/jianyi/pytorch/benchmarks/dynamo/common.py", line 2337, in check_accuracy
    new_result = self.run_n_iterations(
  File "/mnt/ssd1/jianyi/pytorch/benchmarks/dynamo/common.py", line 2044, in run_n_iterations
    model_iter_fn(mod, inputs, collect_outputs=False)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_dynamo/eval_frame.py", line 1034, in compile_wrapper
    raise e.remove_dynamo_frames() from None  # see TORCHDYNAMO_VERBOSE=1
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/compile_fx.py", line 1053, in _compile_fx_inner
    raise InductorError(e, currentframe()).with_traceback(
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/compile_fx.py", line 1037, in _compile_fx_inner
    mb_compiled_graph = fx_codegen_and_compile(
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/compile_fx.py", line 1798, in fx_codegen_and_compile
    return scheme.codegen_and_compile(gm, example_inputs, inputs_to_check, graph_kwargs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/compile_fx.py", line 1570, in codegen_and_compile
    compiled_module = graph.compile_to_module()
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/graph.py", line 2499, in compile_to_module
    return self._compile_to_module()
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/graph.py", line 2505, in _compile_to_module
    self.codegen_with_cpp_wrapper() if self.cpp_wrapper else self.codegen()
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/graph.py", line 2437, in codegen
    self._update_scheduler()
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/graph.py", line 2431, in _update_scheduler
    self.scheduler = Scheduler(self.operations)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 2875, in __init__
    self._init(nodes)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 2892, in _init
    self.nodes = [self.create_scheduler_node(n) for n in nodes]
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 2892, in <listcomp>
    self.nodes = [self.create_scheduler_node(n) for n in nodes]
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 3131, in create_scheduler_node
    return SchedulerNode(self, node)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 1507, in __init__
    self._compute_attrs()
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/scheduler.py", line 1515, in _compute_attrs
    self._sizes, body = self.node.simplify_and_reorder(
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 4962, in simplify_and_reorder
    ) = self.get_default_sizes_body()
  File "<string>", line 6, in get_default_sizes_body_cache_on_self
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 4915, in get_default_sizes_body
    body = LoopBody(
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 133, in __init__
    self._init_with_tracing(fn, args)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 163, in _init_with_tracing
    self.root_block = LoopBodyBlock(self, fn, args)  # traces
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 546, in __init__
    ops.output(fn(*args))
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 1117, in store_output
    return ops.store(output_name or "unnamed", indexer(vars), loader(vars))
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/lowering.py", line 681, in inner_fn
    out = load(index)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 2880, in loader
    return inner(reindex(idx))
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/lowering.py", line 1495, in inner_fn
    ops.masked(
  File "<string>", line 260, in masked
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/virtualized.py", line 325, in _default
    return OpsWrapper._wrap(getattr(_ops, name)(*new_args, **new_kwargs))
  File "<string>", line 260, in masked
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/index_propagation.py", line 303, in _default
    return self.fallback(name, args, kwargs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/index_propagation.py", line 278, in fallback
    return self.wrap(getattr(self._inner, name)(*new_args, **new_kwargs))
  File "<string>", line 260, in masked
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 612, in _default
    return getattr(self._inner, name)(*args, **kwargs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 740, in masked
    self.body.subblocks[name] = LoopBodyBlock(self.body, masked_body, [])
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 546, in __init__
    ops.output(fn(*args))
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/lowering.py", line 1497, in <lambda>
    lambda: inputs_loaders[i](idx_load),
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 2880, in loader
    return inner(reindex(idx))
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/lowering.py", line 681, in inner_fn
    out = load(index)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/ir.py", line 4578, in loader
    return ops.load(self.name or "unnamed", indexer(index))
  File "<string>", line 221, in load
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/virtualized.py", line 325, in _default
    return OpsWrapper._wrap(getattr(_ops, name)(*new_args, **new_kwargs))
  File "<string>", line 221, in load
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/index_propagation.py", line 303, in _default
    return self.fallback(name, args, kwargs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/index_propagation.py", line 278, in fallback
    return self.wrap(getattr(self._inner, name)(*new_args, **new_kwargs))
  File "<string>", line 221, in load
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 612, in _default
    return getattr(self._inner, name)(*args, **kwargs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 640, in load
    index = self._simplify(index)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/loop_body.py", line 637, in _simplify
    return V.graph.sizevars.simplify_with_ranges(expr, self.body.var_ranges)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/sizevars.py", line 125, in simplify_with_ranges
    result = self._simplify_with_ranges(expr, var_ranges)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/sizevars.py", line 230, in _simplify_with_ranges
    expr = expr.replace(
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1749, in replace
    rv = walk(self, rec_replace)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1724, in walk
    newargs = tuple([walk(a, F) for a in args])
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1724, in <listcomp>
    newargs = tuple([walk(a, F) for a in args])
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1724, in walk
    newargs = tuple([walk(a, F) for a in args])
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1724, in <listcomp>
    newargs = tuple([walk(a, F) for a in args])
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1734, in walk
    rv = F(rv)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1742, in rec_replace
    v = _value(expr, result)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 1694, in <lambda>
    _value = lambda expr, result: (value(**
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/sizevars.py", line 219, in visit_modular_indexing
    base = remove_zero_terms(base, divisor)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/_inductor/sizevars.py", line 199, in remove_zero_terms
    if not statically_known(base >= 0):
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
 


....

  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1393, in is_ge
    return n2 >= 0
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/decorators.py", line 236, in _func
    return func(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 350, in __ge__
    return GreaterThan(self, other)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 852, in __new__
    return cls._eval_relation(lhs, rhs, **options)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 859, in _eval_relation
    val = cls._eval_fuzzy_relation(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1134, in _eval_fuzzy_relation
    return is_ge(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1387, in is_ge
    n2 = _n2(lhs, rhs)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/relational.py", line 1221, in _n2
    if a.is_comparable and b.is_comparable:
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/torch/utils/_sympy/functions.py", line 1340, in is_comparable
    return bool(self.args[0].is_comparable)
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/basic.py", line 831, in is_comparable
    for p in self.as_real_imag()]
  File "/root/miniforge3/envs/jianyi/lib/python3.10/site-packages/sympy/core/expr.py", line 1919, in as_real_imag
    if hints.get('ignore') == self:
torch._inductor.exc.InductorError: RecursionError: maximum recursion depth exceeded while calling a Python object

Set TORCHDYNAMO_VERBOSE=1 for the internal stack trace (please do this especially if you're reporting a bug to PyTorch). For even more developer context, set TORCH_LOGS="+dynamo"

TorchDynamo optimized model failed to run because of following error
fail_to_run
```

### Versions

torch                    2.12.0.dev20260225+cu128

cc [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] looks like this error appears after #172707, could you help take a look?

### Comment 2 ([user]):

[user] If you want to verify this fix quickly on nightly without rebuilding, you can hotpatch the PR directly:

```bash
python tools/nightly_hotpatch.py 172707
```
let me know if it is still reproducible

### Comment 3 ([user]):

New PR at (withheld: the upstream fix is not part of the task)

### Comment 4 ([user]):

Tested with release 2.11:
```
python benchmarks/dynamo/timm_models.py --inference --amp --amp-dtype float16 -d cuda -n10 --accuracy --disable-cudagraphs --only volo_d1_224 --cold-start-latency --backend=inductor
loading model: 0it [00:01, ?it/s]
cuda eval  volo_d1_224                        
pass
```

### Comment 5 ([user]):

[user] [user]  Next release we need to plan benchmarks like these earlier as this was reverting a >1 month old merged PR already in main just with 1 day action margin. That it could be ok for an internal team member contribution but it is not the right policy  for third party contributors.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
