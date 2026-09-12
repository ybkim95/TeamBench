# GH1209_pytorch_176603: Fix the torch.Stream context manager reentrance — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/176560
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

We're introducing torch.accelerator in vLLM. RFC: https://github.com/vllm-project/vllm/issues/30679.
One of the tasks is to change `with torch.cuda.stream(astream):` to `with astream:`. With the change in PR (withheld: the upstream fix is not part of the task), we got such error.

```
RuntimeError: Stream's context should not be initialized.
```

A simple reproducer can be:

```python
import torch
from abc import ABC
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class GraphCaptureContext:
    stream: torch.Stream

class GraphCaptureGroup(ABC):        

    @contextmanager
    def fn(self, graph_capture_context: GraphCaptureContext | None = None):
        if graph_capture_context is None:
            stream = torch.Stream()
            graph_capture_context = GraphCaptureContext(stream)
        else:
            stream = graph_capture_context.stream

        curr_stream = torch.accelerator.current_stream()
        if curr_stream != stream:
            stream.wait_stream(curr_stream)

        # with torch.xpu/cuda.stream(stream): # This work
        with stream: # This doesn't work
            yield graph_capture_context


ctx_a = GraphCaptureGroup()
ctx_b = GraphCaptureGroup()


@contextmanager
def graph_capture(device: torch.device):
    context = GraphCaptureContext(torch.Stream(device=device))
    with ctx_a.fn(context), ctx_b.fn(context):
        yield context

device = torch.device(torch.accelerator.current_accelerator())
t = torch.ones(10, device=device)
with graph_capture(device=device):
    for i in range(10):
        t = t + 1
    torch.accelerator.synchronize()

```

### Versions

```
PyTorch version: 2.11.0+xpu
Is debug build: False
CUDA used to build PyTorch: None
ROCM used to build PyTorch: N/A

OS: Ubuntu 24.04.3 LTS (x86_64)
GCC version: (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0
Clang version: Could not collect
CMake version: version 4.2.1
Libc version: glibc-2.39

Python version: 3.12.3 (main, Jan 22 2026, 20:57:42) [GCC 13.3.0] (64-bit runtime)
Python platform: Linux-6.17.0-14-generic-x86_64-with-glibc2.39
Is CUDA available: False
CUDA runtime version: No CUDA
CUDA_MODULE_LOADING set to: N/A
GPU models and configuration: No CUDA
Nvidia driver version: No CUDA
cuDNN version: No CUDA
Is XPU available: True
XPU used to build PyTorch: 20250302
Intel GPU driver version:
* libze1:       1.27.0-1~24.04~ppa1
* intel-opencl-icd:     25.44.36015.8-0
Intel GPU models onboard:
N/A
Intel GPU models detected:
* [0] _XpuDeviceProperties(name='Intel(R) Arc(TM) Pro B60 Graphics', platform_name='Intel(R) oneAPI Unified Runtime over Level-Zero V2', type='gpu', device_id=0xE211, uuid=868011e2-0000-0000-0300-000000000000, driver_version='1.13.36015+8', total_memory=23256MB, local_mem_size=128KB, max_compute_units=160, gpu_eu_count=160, gpu_subslice_count=20, max_work_group_size=1024, max_num_sub_groups=64, sub_group_sizes=[16 32], has_fp16=1, has_fp64=1, has_atomic64=1)
HIP runtime version: N/A
MIOpen runtime version: N/A
Is XNNPACK available: True
Caching allocator config: N/A

CPU:
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           46 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  20
On-line CPU(s) list:                     0-19
Vendor ID:                               GenuineIntel
BIOS Vendor ID:                          Intel(R) Corporation
Model name:                              Intel(R) Core(TM) Ultra 7 265K
BIOS Model name:                         Intel(R) Core(TM) Ultra 7 265K To Be Filled By O.E.M. CPU @ 3.9GHz
BIOS CPU family:                         774
CPU family:                              6
Model:                                   198
Thread(s) per core:                      1
Core(s) per socket:                      20
Socket(s):                               1
Stepping:                                2
CPU(s) scaling MHz:                      30%
CPU max MHz:                             5500.0000
CPU min MHz:                             800.0000
BogoMIPS:                                7756.80
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdt_a rdseed adx smap clflushopt clwb intel_pt sha_ni xsaveopt xsavec xgetbv1 xsaves split_lock_detect user_shstk avx_vnni lam wbnoinvd dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp hwp_pkg_req hfi vnmi umip pku ospke waitpkg gfni vaes vpclmulqdq rdpid bus_lock_detect movdiri movdir64b fsrm md_clear serialize arch_lbr ibt flush_l1d arch_capabilities
Virtualization:                          VT-x
L1d cache:                               704 KiB (18 instances)
L1i cache:                               1.1 MiB (18 instances)
L2 cache:                                36 MiB (11 instances)
L3 cache:                                30 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-19
Vulnerability Gather data sampling:      Not affected
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             Not affected
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Not affected
Vulnerability Old microcode:             Not affected
Vulnerability Reg file data sampling:    Not affected
Vulnerability Retbleed:                  Not affected
Vulnerability Spec rstack overflow:      Not affected
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Enhanced / Automatic IBRS; IBPB conditional; PBRSB-eIBRS Not affected; BHI BHI_DIS_S
Vulnerability Srbds:                     Not affected
Vulnerability Tsa:                       Not affected
Vulnerability Tsx async abort:           Not affected
Vulnerability Vmscape:                   Mitigation; IBPB before exit to userspace

Versions of relevant libraries:
[pip3] dpcpp-cpp-rt==2025.3.2
[pip3] impi-rt==2021.17.2
[pip3] intel-cmplr-lib-rt==2025.3.2
[pip3] intel-cmplr-lib-ur==2025.3.2
[pip3] intel-cmplr-lic-rt==2025.3.2
[pip3] intel-opencl-rt==2025.3.2
[pip3] intel-openmp==2025.3.2
[pip3] intel-pti==0.16.0
[pip3] intel-sycl-rt==2025.3.2
[pip3] mkl==2025.3.1
[pip3] numpy==2.4.2
[pip3] oneccl==2021.17.2
[pip3] oneccl-devel==2021.17.2
[pip3] onemkl-license==2025.3.1
[pip3] onemkl-sycl-blas==2025.3.1
[pip3] onemkl-sycl-dft==2025.3.1
[pip3] onemkl-sycl-lapack==2025.3.1
[pip3] onemkl-sycl-rng==2025.3.1
[pip3] onemkl-sycl-sparse==2025.3.1
[pip3] tbb==2022.3.1
[pip3] tcmlib==1.4.1
[pip3] torch==2.11.0+xpu
[pip3] torchaudio==2.11.0+xpu
[pip3] torchvision==0.26.0+xpu
[pip3] triton-xpu==3.7.0
[pip3] umf==1.0.3
[conda] Could not collect
```

cc [user] [user] [user] [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This is because `torch.Stream` currently doesn't support reentrance on `with statement`. A simple reproducer is
```python
import torch
s = torch.Stream()
with s, s:
    print("hello world!")
```
It will raise 
```bash
Traceback (most recent call last):
  File "/home/guangyey/repos/test_stream.py", line 3, in <module>
    with s, s:
RuntimeError: Stream's context should not be initialized.
```
I will try to fix it.
A workaround is always creating a new torch.Stream object in line `with stream: # This doesn't work`
```python
            with torch.Stream(stream.stream_id, stream.device_index, stream.device_type)
```

### Comment 2 ([user]):

[user] thank you for the WA, I've applied in (withheld: the upstream fix is not part of the task)changes/8bc880283eccbbc8e88d638ff94c3610f9b86182

### Comment 3 ([user]):

Will be fixed in (withheld: the upstream fix is not part of the task).

### Comment 4 ([user]):

> This is because `torch.Stream` currently doesn't support reentrance on `with statement`. A simple reproducer is
> 
> import torch
> s = torch.Stream()
> with s, s:
>     print("hello world!")
> It will raise
> 
> Traceback (most recent call last):
>   File "/home/guangyey/repos/test_stream.py", line 3, in <module>
>     with s, s:
> RuntimeError: Stream's context should not be initialized.
> I will try to fix it. A workaround is always creating a new torch.Stream object in line `with stream: # This doesn't work`
> 
>             with torch.Stream(stream.stream_id, stream.device_index, stream.device_type)

seems the WA causes correctness regression. Will it creates a fresh context manager object each time or share the same?

### Comment 5 ([user]):

It would create a fresh context manager.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
