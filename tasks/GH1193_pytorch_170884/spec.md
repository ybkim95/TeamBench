# GH1193_pytorch_170884: [inductor] Fix cudagraph skip for index_put_ with boolean indices, gr… — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/169951
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

Runner: A10 single GPU

### Install transformers

```bash
git clone https://github.com/huggingface/transformers.git && cd transformers && git fetch origin && git checkout 745ad8c7&& pip install -e .[torch,testing]
```


### Install

```bash
python3 -m pip uninstall -y torch torchvision torchaudio codecarbon torchcodec
python3 -m pip install --no-cache-dir --pre torch --index-url https://download.pytorch.org/whl/nightly/cu126
```

### What we get

```bash
2.10.0.dev20251208+cu126
```

### Run test

> RUN_SLOW=1 python3 -m pytest -v  tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_generate_compile_model_forward_fullgraph

### Error (short)

```bash


============================================================================================================================================================================================================ FAILURES ============================================================================================================================================================================================================
________________________________________________________________________________________________________________________________________________________________________________ T5Gemma2ModelTest.test_generate_compile_model_forward_fullgraph _________________________________________________________________________________________________________________________________________________________________________________

self = <torch._inductor.cudagraph_trees.CUDAGraphNode object at 0x7fd5e97f1ea0>, model = <function partition_0 at 0x7fd5e54e2ef0>, inputs = []

    def _record(self, model: ModelType, inputs: list[InputType]) -> OutputType:
        "Record the model"                                                                                                                                                                                                                                                                                                                                                                                                        
        assert self.graph is not None                                                                                                                                                                                                                                                                                                                                                                                             

        def static_input_iter() -> Generator[torch.Tensor, None, None]:
            for i in self.wrapped_function.static_input_idxs:
                _inp = inputs[i]
                if isinstance(
                    _inp, torch.Tensor
                ) and not self._is_cuda_graph_recorded_tensor(_inp):
                    yield _inp

        # see: output_is_alias_of_persistent_static_inputs above                                                                                                                                                                                                                                                                                                                                                                  
        static_input_persistent_storage_ptrs: dict[int, StorageWeakRefWrapper] = {
            inp.untyped_storage().data_ptr(): StorageWeakRefWrapper(inp)
            for inp in itertools.chain(
                static_input_iter(), self.wrapped_function.constants
            )
        }

        if config.triton.slow_path_cudagraph_asserts:
            # need to use parent live weakrefs because live_indices isn't set yet
            memory = (
                [] if self.parent is None else list(self.parent.path_live_weakrefs())
            )
            memory += [
                StorageWeakRefWrapper(elem)
                for i, elem in enumerate(inputs)
                if isinstance(elem, torch.Tensor)
                and i not in self.wrapped_function.static_input_idxs
                and elem.untyped_storage().data_ptr() != 0                                                                                                                                                                                                                                                                                                                                                                        
            ]
            check_memory_pool(self.device, self.cuda_graphs_pool, memory)

        with (
            preserve_rng_state(),
            torch.cuda.device(self.device),
            clear_cublas_manager(),
            torch.cuda.graph(
                self.graph,
                stream=self.stream,
                pool=self.cuda_graphs_pool,
                capture_error_mode="thread_local",
            ),
            get_history_recording(),
        ):
>           static_outputs = model(inputs)

/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:1285:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/tmp/torchinductor_root/fy/cfyonsx65sydovsaad4kjiv7kinhcb6ciipbxolrf4y6hjt7tjwj.py:1651: in partition_0
    aten.index_put_(buf0, [buf1], arg3_1, False)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <OpOverloadPacket(op='aten.index_put_')>, args = (tensor([[[-0.0277, -0.0873, -0.0395,  0.0644, -0.0063,  0.1301,  0.0902,
          -0.0460, -0.0505, -0.0705, -0.0257..., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0.], device='cuda:0', requires_grad=True), False), kwargs = {}

    def __call__(self, /, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        # overloading __call__ to ensure torch.ops.foo.bar()                                                                                                                                                                                                                                                                                                                                                                      
        # is still callable from JIT                                                                                                                                                                                                                                                                                                                                                                                              
        # We save the function ptr as the `op` attribute on                                                                                                                                                                                                                                                                                                                                                                       
        # OpOverloadPacket to access it here.                                                                                                                                                                                                                                                                                                                                                                                     

        # Directly calling OverloadPacket goes into C++, which will check                                                                                                                                                                                                                                                                                                                                                         
        # the schema and cause an error for torchbind op when inputs consist of FakeScriptObject so we                                                                                                                                                                                                                                                                                                                            
        # intercept it here and call TorchBindOpverload instead.                                                                                                                                                                                                                                                                                                                                                                  
        if self._has_torchbind_op_overload and _must_dispatch_in_python(args, kwargs):
            # pyrefly: ignore [bad-argument-type]                                                                                                                                                                                                                                                                                                                                                                                 
            return _call_overload_packet_from_python(self, *args, **kwargs)
>       return self._op(*args, **kwargs)
E       torch.AcceleratorError: CUDA error: operation not permitted when stream is capturing
E       Search for `cudaErrorStreamCaptureUnsupported' in https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html for more information.
E       CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
E       For debugging consider passing CUDA_LAUNCH_BLOCKING=1
E       Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.

/usr/local/lib/python3.10/dist-packages/torch/_ops.py:1209: AcceleratorError

During handling of the above exception, another exception occurred:

self = <tests.models.t5gemma2.test_modeling_t5gemma2.T5Gemma2ModelTest testMethod=test_generate_compile_model_forward_fullgraph>

    @pytest.mark.generate
    @pytest.mark.torch_compile_test
    @require_torch_greater_or_equal("2.6")  # Uses torch.compiler.set_stance                                                                                                                                                                                                                                                                                                                                                      
    def test_generate_compile_model_forward_fullgraph(self):
        """                                                                                                                                                                                                                                                                                                                                                                                                                       
        Tests that `.generate` is compatible with torch.compile, keeping the same results. Also confirms that                                                                                                                                                                                                                                                                                                                     
        `.forward` called from `.generate` sees no graph breaks or recompilations when compiled.                                                                                                                                                                                                                                                                                                                                  

        ⚠️ Runs two sequential generations to ensure the cache doesn't get stuck after the first compiled run! ⚠️                                                                                                                                                                                                                                                                                                                 
        """                                                                                                                                                                                                                                                                                                                                                                                                                       
        for model_class in self.all_generative_model_classes:
            # 1. Test exclusion criteria                                                                                                                                                                                                                                                                                                                                                                                          
            if not model_class._can_compile_fullgraph:
                self.skipTest("This model doesn't support compilation without graph breaks")

            # 2. Prepares two sets of inputs                                                                                                                                                                                                                                                                                                                                                                                      
            config, inputs_dict = self.prepare_config_and_inputs_for_generate(batch_size=4)
            set_config_for_less_flaky_test(config)
            model = model_class(config).to(torch_device)
            set_model_for_less_flaky_test(model)
            model.eval()  # otherwise `self.training` is `True` -- this flag is used at attn mask creation time                                                                                                                                                                                                                                                                                                                   

            # Some composite models have a custom generate and will call an inner model's generate -> that inner model                                                                                                                                                                                                                                                                                                            
            # is the one that gets compiled.                                                                                                                                                                                                                                                                                                                                                                                      
            # (Note for the future: if BLIP starts causing problems, let's stop testing it)                                                                                                                                                                                                                                                                                                                                       
            if "blip" in model.__class__.__name__.lower():
                model_to_be_compiled = model.language_model
            else:
                model_to_be_compiled = model

            # creates two sets of *different* inputs with the same shape                                                                                                                                                                                                                                                                                                                                                          
            main_input = inputs_dict[model.main_input_name].to(torch_device)
            half_batch_size = main_input.shape[0] // 2                                                                                                                                                                                                                                                                                                                                                                            
            input_1 = {}
            input_2 = {}
            for key, value in inputs_dict.items():
                if isinstance(value, torch.Tensor):
                    input_1[key] = value[:half_batch_size, :].to(torch_device)
                    input_2[key] = value[half_batch_size : half_batch_size * 2, :].to(torch_device)
                else:
                    input_1[key] = value
                    input_2[key] = value
            model_input_sets = [input_1, input_2]
            self.assertTrue(
                model_input_sets[0][model.main_input_name].shape == model_input_sets[1][model.main_input_name].shape
            )

            # 3. compilation-specific setup and generation parameterization                                                                                                                                                                                                                                                                                                                                                       
            torch.compiler.reset()  # prevent cached compilation from being used in the test                                                                                                                                                                                                                                                                                                                                      
            has_defined_cache_implementation = model.generation_config.cache_implementation is not None                                                                                                                                                                                                                                                                                                                           
            compile_config = CompileConfig(fullgraph=True, dynamic=False)  # Error out on dynamic shapes                                                                                                                                                                                                                                                                                                                          
            compile_config._compile_all_devices = True  # force compilation (e.g. fast CI, CPU)                                                                                                                                                                                                                                                                                                                                   

            generation_kwargs = {
                "use_cache": True,
                "do_sample": False,
                "max_new_tokens": 5,
                "return_dict_in_generate": True,
                "output_scores": True,
                "compile_config": compile_config,
            }

            # 4. get eager + dynamic cache results for future comparison                                                                                                                                                                                                                                                                                                                                                          
            dynamic_outputs = []
            # Ignores all `torch.compile` usage, useful to test models that that have non-default compilable caches                                                                                                                                                                                                                                                                                                               
            # (who would have used compilation in this section)                                                                                                                                                                                                                                                                                                                                                                   
            with torch.compiler.set_stance("force_eager"):
                for model_inputs in model_input_sets:
                    gen_out = model.generate(**model_inputs, **generation_kwargs)
                    dynamic_outputs.append(gen_out)
                    # sanity checks for the default cache implementation                                                                                                                                                                                                                                                                                                                                                          
                    if not has_defined_cache_implementation:
                        decoder_cache = (
                            gen_out.past_key_values.self_attention_cache
                            if config.is_encoder_decoder
                            else gen_out.past_key_values
                        )
                        self.assertTrue(isinstance(decoder_cache, DynamicCache))
                        self.assertFalse(decoder_cache.is_compileable)
                        # our auto compile should NOT have been called                                                                                                                                                                                                                                                                                                                                                            
                        self.assertFalse(hasattr(model_to_be_compiled, "_compiled_call"))

            # 5. get compiled results -- relies on the automatic compilation triggered by specific compilable caches                                                                                                                                                                                                                                                                                                              
            if not has_defined_cache_implementation:
                generation_kwargs["cache_implementation"] = "static"                                                                                                                                                                                                                                                                                                                                                              

            compiled_outputs = []
            # Uses a context manager to catch recompilation logs. If there is any recompilation, this test fails.                                                                                                                                                                                                                                                                                                                 
            # Try/Finally is used to ensure that the log options are reset even if an error is raised.                                                                                                                                                                                                                                                                                                                            
            try:
                torch._logging.set_logs(recompiles_verbose=True)
                logger = logging.get_logger("torch._dynamo.guards")
                with CaptureLogger(logger) as cl:
                    for model_inputs in model_input_sets:
                        # with torch.compiler.set_stance("fail_on_recompile"):                                                                                                                                                                                                                                                                                                                                                    
>                       gen_out = model.generate(**model_inputs, **generation_kwargs)

tests/generation/test_utils.py:1588:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.10/dist-packages/torch/utils/_contextlib.py:124: in decorate_context
    return func(*args, **kwargs)
src/transformers/generation/utils.py:2684: in generate
    result = decoding_method(
src/transformers/generation/utils.py:2882: in _sample
    outputs = model_forward(**model_inputs, return_dict=True)
/usr/local/lib/python3.10/dist-packages/torch/_dynamo/eval_frame.py:926: in compile_wrapper
    return fn(*args, **kwargs)
/usr/local/lib/python3.10/dist-packages/torch/nn/modules/module.py:1776: in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
/usr/local/lib/python3.10/dist-packages/torch/nn/modules/module.py:1787: in _call_impl
    return forward_call(*args, **kwargs)
src/transformers/utils/generic.py:758: in wrapper
    @wraps(func)
/usr/local/lib/python3.10/dist-packages/torch/_dynamo/eval_frame.py:1154: in _fn
    return fn(*args, **kwargs)
/usr/local/lib/python3.10/dist-packages/torch/_functorch/aot_autograd.py:1148: in forward
    return compiled_fn(full_args)
/usr/local/lib/python3.10/dist-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:357: in runtime_wrapper
    all_outs = call_func_at_runtime_with_args(
/usr/local/lib/python3.10/dist-packages/torch/_functorch/_aot_autograd/utils.py:134: in call_func_at_runtime_with_args
    out = normalize_as_list(f(args))
/usr/local/lib/python3.10/dist-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:1962: in __call__
    return self.compiled_fn(*args, **kwargs)
/usr/local/lib/python3.10/dist-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:531: in wrapper
    return compiled_fn(runtime_args)
/usr/local/lib/python3.10/dist-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:729: in inner_fn
    outs = compiled_fn(args)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/output_code.py:627: in __call__
    return self.current_callable(inputs)
/tmp/torchinductor_root/fy/cfyonsx65sydovsaad4kjiv7kinhcb6ciipbxolrf4y6hjt7tjwj.py:1875: in call
    (buf69,) = self.partitions[0](partition0_args)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/compile_fx.py:1834: in run
    return compiled_fn(new_inputs)  # type: ignore[arg-type]                                                                                                                                                                                                                                                                                                                                                                      
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:388: in deferred_cudagraphify
    return fn(inputs)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/utils.py:3242: in run
    out = model(new_inputs)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:2033: in run
    out = self._run(new_inputs, function_id)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:2203: in _run
    return self.record_function(new_inputs, function_id)
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:2240: in record_function
    node = CUDAGraphNode(
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:1046: in __init__
    self.recording_outputs: Optional[OutputType] = self._record(
/usr/local/lib/python3.10/dist-packages/torch/_inductor/cudagraph_trees.py:1273: in _record
    with (
/usr/local/lib/python3.10/dist-packages/torch/cuda/graphs.py:268: in __exit__
    self.cuda_graph.capture_end()
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <torch.cuda.graphs.CUDAGraph object at 0x7fd5fed0a6b0>

    def capture_end(self) -> None:
        r"""End CUDA graph capture on the current stream.                                                                                                                                                                                                                                                                                                                                                                         

        After ``capture_end``, ``replay`` may be called on this instance.                                                                                                                                                                                                                                                                                                                                                         

        Typically, you shouldn't call ``capture_end`` yourself.                                                                                                                                                                                                                                                                                                                                                                   
        Use :class:`~torch.cuda.graph` or :func:`~torch.cuda.make_graphed_callables`,                                                                                                                                                                                                                                                                                                                                             
        which call ``capture_end`` internally.                                                                                                                                                                                                                                                                                                                                                                                    
        """                                                                                                                                                                                                                                                                                                                                                                                                                       
>       super().capture_end()
E       torch.AcceleratorError: CUDA error: operation failed due to a previous error during capture
E       Search for `cudaErrorStreamCaptureInvalidated' in https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html for more information.
E       CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
E       For debugging consider passing CUDA_LAUNCH_BLOCKING=1
E       Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.

/usr/local/lib/python3.10/dist-packages/torch/cuda/graphs.py:130: AcceleratorError
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ Captured stderr call ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Unrecognized keys in `rope_parameters` for 'rope_type'='default': {'sliding_attention', 'full_attention'}
Unrecognized keys in `rope_parameters` for 'rope_type'='default': {'sliding_attention', 'full_attention'}
You have set `compile_config`, but we are unable to meet the criteria for compilation. Compilation will be skipped.
V1209 13:53:58.028000 1893 torch/_dynamo/guards.py:4504] [0/1] [__recompiles_verbose] Recompiling function wrapper in /transformers/src/transformers/utils/generic.py:758
V1209 13:53:58.028000 1893 torch/_dynamo/guards.py:4504] [0/1] [__recompiles_verbose]     triggered by the following guard failure(s):
V1209 13:53:58.028000 1893 torch/_dynamo/guards.py:4504] [0/1] [__recompiles_verbose]     guard 0 failures:
V1209 13:53:58.028000 1893 torch/_dynamo/guards.py:4504] [0/1] [__recompiles_verbose]     - 0/0: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 1  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose] Recompiling function wrapper in /transformers/src/transformers/utils/generic.py:758
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]     triggered by the following guard failure(s):
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]     guard 0 failures:
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]     - 0/1: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 2  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]     guard 1 failures:
V1209 13:53:59.774000 1893 torch/_dynamo/guards.py:4504] [0/2] [__recompiles_verbose]     - 0/0: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 1  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose] Recompiling function wrapper in /transformers/src/transformers/utils/generic.py:758
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     triggered by the following guard failure(s):
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     guard 0 failures:
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     - 0/2: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 3  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     guard 1 failures:
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     - 0/1: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 2  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     guard 2 failures:
V1209 13:54:01.632000 1893 torch/_dynamo/guards.py:4504] [0/3] [__recompiles_verbose]     - 0/0: kwargs['past_key_values'].self_attention_cache.layers[0].cumulative_length == 1  # is_full = self.cumulative_length >= self.max_cache_len  # ransformers/src/transformers/cache_utils.py:467 in get_mask_sizes
======================================================================================================================================================================================================== warnings summary ========================================================================================================================================================================================================
<frozen importlib._bootstrap>:241
  <frozen importlib._bootstrap>:241: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:241
  <frozen importlib._bootstrap>:241: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

tests/models/t5gemma2/test_modeling_t5gemma2.py: 14 warnings
  /usr/local/lib/python3.10/dist-packages/torch/jit/_script.py:362: DeprecationWarning: `torch.jit.script_method` is deprecated. Please switch to `torch.compile` or `torch.export`.
    warnings.warn(

tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_generate_compile_model_forward_fullgraph
  /usr/local/lib/python3.10/dist-packages/torch/_inductor/compile_fx.py:321: UserWarning: TensorFloat32 tensor cores for float32 matrix multiplication available but not enabled. Consider setting `torch.set_float32_matmul_precision('high')` for better performance.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================================================================================================================================================================================== short test summary info =====================================================================================================================================================================================================
FAILED tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_generate_compile_model_forward_fullgraph - torch.AcceleratorError: CUDA error: operation failed due to a previous error during capture
================================================================================================================================================================================================ 1 failed, 17 warnings in 15.54s =================================================================================================================================================================================================
sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute

```



### Versions

Collecting environment information...
PyTorch version: 2.10.0.dev20251208+cu126
Is debug build: False
CUDA used to build PyTorch: 12.6
ROCM used to build PyTorch: N/A

OS: Ubuntu 22.04.4 LTS (x86_64)
GCC version: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0
Clang version: Could not collect
CMake version: Could not collect
Libc version: glibc-2.35

Python version: 3.10.12 (main, Nov  4 2025, 08:48:33) [GCC 11.4.0] (64-bit runtime)
Python platform: Linux-6.12.55-74.119.amzn2023.x86_64-x86_64-with-glibc2.35
Is CUDA available: True
CUDA runtime version: Could not collect
CUDA_MODULE_LOADING set to:
GPU models and configuration: GPU 0: NVIDIA A10G
Nvidia driver version: 580.105.08
cuDNN version: Probably one of the following:
/usr/lib/x86_64-linux-gnu/libcudnn.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_adv.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_cnn.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_engines_precompiled.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_engines_runtime_compiled.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_graph.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_heuristic.so.9.3.0
/usr/lib/x86_64-linux-gnu/libcudnn_ops.so.9.3.0
Is XPU available: False
HIP runtime version: N/A
MIOpen runtime version: N/A
Is XNNPACK available: True
Caching allocator config: N/A

CPU:
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           48 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  16
On-line CPU(s) list:                     0-15
Vendor ID:                               AuthenticAMD
Model name:                              AMD EPYC 7R32
CPU family:                              23
Model:                                   49
Thread(s) per core:                      2
Core(s) per socket:                      8
Socket(s):                               1
Stepping:                                0
BogoMIPS:                                5600.00
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid extd_apicid aperfmperf tsc_known_freq pni pclmulqdq ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c rdrand hypervisor lahf_lm cmp_legacy cr8_legacy abm sse4a misalignsse 3dnowprefetch topoext ssbd ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 clzero xsaveerptr rdpru wbnoinvd arat npt nrip_save rdpid
Hypervisor vendor:                       KVM
Virtualization type:                     full
L1d cache:                               256 KiB (8 instances)
L1i cache:                               256 KiB (8 instances)
L2 cache:                                4 MiB (8 instances)
L3 cache:                                32 MiB (2 instances)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-15
Vulnerability Gather data sampling:      Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             Not affected
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Not affected
Vulnerability Reg file data sampling:    Not affected
Vulnerability Retbleed:                  Mitigation; untrained return thunk; SMT enabled with STIBP protection
Vulnerability Spec rstack overflow:      Vulnerable: Safe RET, no microcode
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Retpolines; IBPB conditional; STIBP always-on; RSB filling; PBRSB-eIBRS Not affected; BHI Not affected
Vulnerability Srbds:                     Not affected
Vulnerability Tsa:                       Not affected
Vulnerability Tsx async abort:           Not affected
Vulnerability Vmscape:                   Not affected

Versions of relevant libraries:
[pip3] mypy_extensions==1.1.0
[pip3] numpy==1.26.4
[pip3] nvidia-cublas-cu12==12.6.4.1
[pip3] nvidia-cuda-cupti-cu12==12.6.80
[pip3] nvidia-cuda-nvrtc-cu12==12.6.77
[pip3] nvidia-cuda-runtime-cu12==12.6.77
[pip3] nvidia-cudnn-cu12==9.10.2.21
[pip3] nvidia-cufft-cu12==11.3.0.4
[pip3] nvidia-curand-cu12==10.3.7.77
[pip3] nvidia-cusolver-cu12==11.7.1.2
[pip3] nvidia-cusparse-cu12==12.5.4.2
[pip3] nvidia-cusparselt-cu12==0.7.1
[pip3] nvidia-nccl-cu12==2.27.5
[pip3] nvidia-nvjitlink-cu12==12.6.85
[pip3] nvidia-nvtx-cu12==12.6.77
[pip3] pytorch-triton==3.6.0+git5261b273
[pip3] torch==2.10.0.dev20251208+cu126
[pip3] torchaudio==2.10.0.dev20251208+cu126
[pip3] torchcodec==0.10.0.dev20251209
[pip3] torchvision==0.25.0.dev20251208+cu126
[pip3] triton==3.5.0
[conda] Could not collect

cc [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

other tests for this model shows similar issues

```txt
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_generate_compile_model_forward_fullgraph
(line 130)  torch.AcceleratorError: CUDA error: operation failed due to a previous error during capture
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_generate_with_past_key_values
(line 3109)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_prompt_lookup_decoding_stops_at_eos
(line 891)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_resize_embeddings_untied
(line 83)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_resize_tokens_embeddings
(line 83)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_sample_generate
(line 2923)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_sample_generate_dict_output
(line 2923)  RuntimeError: Offset increment outside graph capture encountered unexpectedly.
tests/models/t5gemma2/test_modeling_t5gemma2.py::T5Gemma2ModelTest::test_sdpa_can_compile_dynamic
(line 494)  torch._dynamo.exc.BackendCompilerFailed: backend='inductor' raised:
```

### Comment 2 ([user]):

cc [user]  [user]

### Comment 3 ([user]):

sorry, this title was wrong, the fact is

fails with torch 2.9.1 and 2.10.0 nightly but passes with torch 2.9.0

### Comment 4 ([user]):

The error when running with torch 2.9.1 is somehow different


```bash
   kernel = result.result()
/usr/local/lib/python3.10/dist-packages/torch/_inductor/codecache.py:4289: in result
    return self.result_fn()
/usr/local/lib/python3.10/dist-packages/torch/_inductor/async_compile.py:470: in get_result
    kernel.precompile(
/usr/local/lib/python3.10/dist-packages/torch/_inductor/runtime/triton_heuristics.py:451: in precompile
    self._make_launchers()
/usr/local/lib/python3.10/dist-packages/torch/_inductor/runtime/triton_heuristics.py:614: in _make_launchers
    launchers.append(result.make_launcher())
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <torch._inductor.runtime.triton_heuristics.TritonCompileResult object at 0x7f54f2aaffd0>

    def make_launcher(self) -> LauncherType:
        """                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        Launching triton kernels is performance sensitive, we compile                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
        a custom Python function get the grid() and reorder the args to                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
        the underlying wrapper.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        """                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        cfg = self.config
        compile_meta = self.compile_meta
        binary = self.kernel
        fn = binary.src.fn
        binary._init_handles()
        (call_args, def_args, none_args) = self._get_arg_lists(
            fn.arg_names, fn.constexprs
        )
        binary_shared = (
            binary.shared if hasattr(binary, "shared") else binary.metadata.shared
        )

        if knobs is None:
            launch_enter = binary.__class__.launch_enter_hook
            launch_exit = binary.__class__.launch_exit_hook
        else:
            launch_enter = knobs.runtime.launch_enter_hook
            launch_exit = knobs.runtime.launch_exit_hook

        import math as math_lib

        import triton as triton_lib

        import torch as torch_lib

        scope = {
            "grid_meta": cfg.kwargs,
            "bin": binary,
            "launch_enter_hook": launch_enter,
            "launch_exit_hook": launch_exit,
            "metadata": (
                binary.packed_metadata
                if hasattr(binary, "packed_metadata")
                else binary.metadata
            ),
            "shared": binary_shared,
            "num_warps": (
                binary.num_warps
                if hasattr(binary, "num_warps")
                else binary.metadata.num_warps
            ),
            "cta_args": (
                (
                    binary.num_ctas,
                    *get_first_attr(binary, "cluster_dims", "clusterDims"),
                )
                if hasattr(binary, "num_ctas")
                else (
>                   (binary.metadata.num_ctas, *binary.metadata.cluster_dims)
                    if hasattr(binary, "metadata")
                    else ()
                )
            ),
            "function": get_first_attr(binary, "function", "cu_function"),
            "runner": get_first_attr(binary, "run", "c_wrapper"),
            "math": math_lib,
            "torch": torch_lib,
            "triton": triton_lib,
        }
E       torch._inductor.exc.InductorError: AttributeError: 'KernelMetadata' object has no attribute 'cluster_dims'
E       
E       Set TORCHDYNAMO_VERBOSE=1 for the internal stack trace (please do this especially if you're reporting a bug to PyTorch). For even more developer context, set TORCH_LOGS="+dynamo"

/usr/local/lib/python3.10/dist-packages/torch/_inductor/runtime/triton_heuristics.py:1757: InductorError
-----------------------------------------------------------------------------------------------------------------------
```

### Comment 5 ([user]):

reopening since the fixing PR was reverted

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
