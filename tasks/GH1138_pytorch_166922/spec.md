# GH1138_pytorch_166922: [Inductor] No longer throw error in bmm out_dtype lowering due to tem… — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/165892
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

```
import torch

A = torch.rand((1, 1024, 1024), device="cuda", dtype=torch.float16)
B = torch.rand((1, 1024, 1024), device="cuda", dtype=torch.float16)

@torch.compile
def linear(weight, input):
    return torch.bmm(input, weight, out_dtype=torch.float32)

linear(A, B)
```

Output:
```
...
  File "/usr/local/lib/python3.10/dist-packages/torch/_inductor/graph.py", line 1279, in call_function
    out = lowerings[target](*args, **kwargs)  # type: ignore[index]
  File "/usr/local/lib/python3.10/dist-packages/torch/_inductor/lowering.py", line 488, in wrapped
    out = decomp_fn(*args, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/torch/_inductor/kernel/bmm.py", line 213, in tuned_bmm
    assert out_dtype is None, "out_dtype is not supported for Triton"
torch._inductor.exc.InductorError: LoweringException: AssertionError: out_dtype is not supported for Triton
  target: aten.bmm.dtype
  args[0]: TensorBox(StorageBox(
    InputBuffer(name='arg0_1', layout=FixedLayout('cuda:0', torch.float16, size=[1, 1024, 1024], stride=[1048576, 1024, 1]))
  ))
  args[1]: TensorBox(StorageBox(
    InputBuffer(name='arg1_1', layout=FixedLayout('cuda:0', torch.float16, size=[1, 1024, 1024], stride=[1048576, 1024, 1]))
  ))
  args[2]: torch.float32
```

See #163275 for when it worked.

### Versions

```
PyTorch version: 2.9.0
Is debug build: False
CUDA used to build PyTorch: 13.0
ROCM used to build PyTorch: N/A

OS: Ubuntu 22.04.5 LTS (x86_64)
GCC version: (Ubuntu 11.4.0-1ubuntu1~22.04.2) 11.4.0
Clang version: Could not collect
CMake version: version 4.1.0
Libc version: glibc-2.35

Python version: 3.10.12 (main, Aug 15 2025, 14:32:43) [GCC 11.4.0] (64-bit runtime)
Python platform: Linux-6.5.13-65-650-4141-22041-coreweave-amd64-85c45edc-x86_64-with-glibc2.35
Is CUDA available: True
CUDA runtime version: 13.0.88
CUDA_MODULE_LOADING set to: 
GPU models and configuration: GPU 0: NVIDIA H100 80GB HBM3
Nvidia driver version: 570.172.08
cuDNN version: Probably one of the following:
/usr/lib/x86_64-linux-gnu/libcudnn.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_adv.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_cnn.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_engines_precompiled.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_engines_runtime_compiled.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_graph.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_heuristic.so.9.13.0
/usr/lib/x86_64-linux-gnu/libcudnn_ops.so.9.13.0
HIP runtime version: N/A
MIOpen runtime version: N/A
Is XNNPACK available: True

CPU:
Architecture:                       x86_64
CPU op-mode(s):                     32-bit, 64-bit
Address sizes:                      46 bits physical, 57 bits virtual
Byte Order:                         Little Endian
CPU(s):                             128
On-line CPU(s) list:                0-127
Vendor ID:                          GenuineIntel
Model name:                         Intel(R) Xeon(R) Platinum 8462Y+
CPU family:                         6
Model:                              143
Thread(s) per core:                 2
Core(s) per socket:                 32
Socket(s):                          2
Stepping:                           8
CPU max MHz:                        4100.0000
CPU min MHz:                        800.0000
BogoMIPS:                           5600.00
Flags:                              fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cat_l2 cdp_l3 invpcid_single cdp_l2 ssbd mba ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a avx512f avx512dq rdseed adx smap avx512ifma clflushopt clwb intel_pt avx512cd sha_ni avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local split_lock_detect avx_vnni avx512_bf16 wbnoinvd dtherm ida arat pln pts hfi vnmi avx512vbmi umip pku ospke waitpkg avx512_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg tme avx512_vpopcntdq la57 rdpid bus_lock_detect cldemote movdiri movdir64b enqcmd fsrm md_clear serialize tsxldtrk pconfig arch_lbr ibt amx_bf16 avx512_fp16 amx_tile amx_int8 flush_l1d arch_capabilities
Virtualization:                     VT-x
L1d cache:                          3 MiB (64 instances)
L1i cache:                          2 MiB (64 instances)
L2 cache:                           128 MiB (64 instances)
L3 cache:                           120 MiB (2 instances)
NUMA node(s):                       2
NUMA node0 CPU(s):                  0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100,102,104,106,108,110,112,114,116,118,120,122,124,126
NUMA node1 CPU(s):                  1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63,65,67,69,71,73,75,77,79,81,83,85,87,89,91,93,95,97,99,101,103,105,107,109,111,113,115,117,119,121,123,125,127
Vulnerability Gather data sampling: Not affected
Vulnerability Itlb multihit:        Not affected
Vulnerability L1tf:                 Not affected
Vulnerability Mds:                  Not affected
Vulnerability Meltdown:             Not affected
Vulnerability Mmio stale data:      Not affected
Vulnerability Retbleed:             Not affected
Vulnerability Spec rstack overflow: Not affected
Vulnerability Spec store bypass:    Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:           Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:           Mitigation; Enhanced / Automatic IBRS; IBPB conditional; RSB filling; PBRSB-eIBRS SW sequence; BHI BHI_DIS_S
Vulnerability Srbds:                Not affected
Vulnerability Tsx async abort:      Not affected

Versions of relevant libraries:
[pip3] clip-anytorch==2.6.0
[pip3] dctorch==0.1.2
[pip3] DISTS-pytorch==0.1
[pip3] gpytorch==1.14.2
[pip3] lovely-numpy==0.2.16
[pip3] mypy_extensions==1.1.0
[pip3] numpy==1.24.4
[pip3] onnx==1.19.1
[pip3] onnx-ir==0.1.11
[pip3] onnxscript==0.3.1
[pip3] torch==2.9.0
[pip3] torchaudio==2.9.0
[pip3] torchdata==0.11.0
[pip3] torchdiffeq==0.2.5
[pip3] torchsde==0.2.6
[pip3] torchtitan==0.1.0
[pip3] torchvision==0.24.0
[pip3] triton==3.5.0+gitbbb06c03
[pip3] welford-torch==0.2.5
[conda] Could not collect
```

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I think I have a similar problem. I have a Python training script:

```
# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
# Assuming 'model.py' and 'dataset.py' are in the same directory.
# If not, you might need to adjust the import paths.
from model import DeepCondResUNet3D
from dataset import VoxelDeblurDatasetMultiLevel
from pytorch_msssim import ssim

# -----------------------------
# Speed-up Settings
# -----------------------------
# Enable cuDNN auto-tuner to find the best algorithm for the hardware.
torch.set_float32_matmul_precision('high')
torch.backends.cudnn.benchmark = True

# Check for native AMP support (PyTorch 1.6+)
USE_NEW_AMP = hasattr(torch, "amp") and hasattr(torch.amp, "autocast")


def get_autocast(dtype):
    """
    Returns the appropriate autocast context manager based on PyTorch version.
    This enables automatic mixed-precision training.

    Args:
        dtype: The desired floating-point type for autocasting (e.g., torch.float16).

    Returns:
        A torch autocast context manager.
    """
    if USE_NEW_AMP:
        return torch.amp.autocast("cuda", dtype=dtype)
    else:
        # Fallback for older PyTorch versions
        return torch.cuda.amp.autocast(dtype=dtype)


def get_gradscaler():
    """
    Returns the appropriate GradScaler based on PyTorch version.
    GradScaler helps prevent underflow with mixed-precision training.

    Returns:
        A torch GradScaler instance.
    """
    if USE_NEW_AMP:
        return torch.amp.GradScaler("cuda")
    else:
        # Fallback for older PyTorch versions
        return torch.cuda.amp.GradScaler()


# -----------------------------
# Metrics
# -----------------------------
def ssim3D(x, y):
    """
    Computes the Structural Similarity Index (SSIM) for 3D volumes.
    It calculates SSIM slice-by-slice along the depth dimension and averages the results.

    Args:
        x (torch.Tensor): The predicted tensor of shape (B, C, D, H, W).
        y (torch.Tensor): The ground truth tensor of shape (B, C, D, H, W).

    Returns:
        torch.Tensor: A scalar tensor containing the average SSIM score.
    """
    x = x.float()
    y = y.float()
    _, _, D, _, _ = x.shape
    scores = []
    # Iterate over the depth dimension (D)
    for i in range(D):
        # Calculate SSIM for each 2D slice
        scores.append(ssim(x[:, :, i, :, :], y[:, :, i, :, :], data_range=1.0))
    return torch.stack(scores).mean()


def psnr3D(pred, target):
    """
    Computes the Peak Signal-to-Noise Ratio (PSNR) for 3D volumes.

    Args:
        pred (torch.Tensor): The predicted tensor.
        target (torch.Tensor): The ground truth tensor.

    Returns:
        torch.Tensor: A scalar tensor containing the PSNR value.
    """
    pred = pred.float()
    target = target.float()
    mse = torch.mean((pred - target) ** 2)
    # Add a small epsilon to prevent log(0)
    return 20 * torch.log10(1.0 / torch.sqrt(mse + 1e-8))


def mae3D(pred, target):
    """
    Computes the Mean Absolute Error (MAE) for 3D volumes.

    Args:
        pred (torch.Tensor): The predicted tensor.
        target (torch.Tensor): The ground truth tensor.

    Returns:
        torch.Tensor: A scalar tensor containing the MAE value.
    """
    return torch.mean(torch.abs(pred.float() - target.float()))


def mape3D(pred, target):
    """
    Computes the Mean Absolute Percentage Error (MAPE) for 3D volumes.

    Args:
        pred (torch.Tensor): The predicted tensor.
        target (torch.Tensor): The ground truth tensor.

    Returns:
        torch.Tensor: A scalar tensor containing the MAPE value.
    """
    # Add a small epsilon to prevent division by zero
    return torch.mean(torch.abs((target.float() - pred.float()) / (target.float() + 1e-8))) * 100


# -----------------------------
# Asynchronous Checkpointing
# -----------------------------
def save_checkpoint_async(state, path):
    """
    Saves a checkpoint to disk in a separate thread to avoid blocking the main training loop.

    Args:
        state (dict): The state dictionary to save (e.g., model, optimizer).
        path (str): The file path to save the checkpoint to.
    """
    def _save():
        torch.save(state, path)

    # Start the save operation in a daemon thread
    t = threading.Thread(target=_save, daemon=True)
    t.start()


# -----------------------------
# Training Function
# -----------------------------
def train(model, dataloader, optimizer, criterion, scaler, device, autocast_dtype,
          last_ckpt_time, checkpoint_interval_sec, checkpoint_dir, epoch,
          start_batch):
    """
    Executes one training epoch.

    Args:
        model (nn.Module): The model to train.
        dataloader (DataLoader): The data loader for training data.
        optimizer: The optimization algorithm.
        criterion: The loss function.
        scaler (GradScaler): The gradient scaler for mixed-precision.
        device (torch.device): The device to train on (e.g., 'cuda').
        autocast_dtype: The data type for autocasting.
        last_ckpt_time (float): Timestamp of the last intra-epoch checkpoint.
        checkpoint_interval_sec (int): How often to save intra-epoch checkpoints.
        checkpoint_dir (str): Directory to save checkpoints.
        epoch (int): The current epoch number.
        start_batch (int): The batch index to start from (for resuming mid-epoch).

    Returns:
        tuple: A tuple containing (average_loss, last_checkpoint_time).
    """
    model.train()
    total_loss = 0.0

    # Create a progress bar for the dataloader
    pbar = tqdm(dataloader, desc=f"Training Epoch {epoch+1}", leave=False)
    for batch_idx, (x, blur_level, y) in enumerate(pbar):
        # If resuming, skip batches that have already been processed in this epoch
        if batch_idx < start_batch:
            continue

        # Move data to the target device and normalize pixel values to [0, 1]
        x = x.to(device, non_blocking=True).float().div_(255.0)
        y = y.to(device, non_blocking=True).float().div_(255.0)
        blur_level = blur_level.to(device, non_blocking=True)

        # Reset gradients
        optimizer.zero_grad(set_to_none=True)

        # Automatic mixed-precision context
        with get_autocast(autocast_dtype):
            output = model(x, blur_level)
            loss = criterion(output, y)

        # Scale the loss and perform backward pass
        scaler.scale(loss).backward()
        # Update model weights
        scaler.step(optimizer)
        # Update the scaler for the next iteration
        scaler.update()

        total_loss += loss.item()
        pbar.set_postfix(loss=loss.item())

        # --- Periodic intra-epoch checkpointing ---
        current_time = time.time()
        if current_time - last_ckpt_time >= checkpoint_interval_sec:
            ckpt_path = os.path.join(
                checkpoint_dir, f"ckpt_epoch{epoch+1}_batch{batch_idx+1}.pt"
            )
            save_checkpoint_async(
                {
                    "epoch": epoch,
                    "batch_idx": batch_idx,
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scaler": scaler.state_dict(),
                },
                ckpt_path,
            )
            last_ckpt_time = current_time

    # Return the average loss for the epoch and the last checkpoint time
    return total_loss / max(1, len(dataloader)), last_ckpt_time


# -----------------------------
# Validation Function
# -----------------------------
@torch.no_grad()
def validate(model, dataloader, criterion, device, autocast_dtype):
    """
    Executes validation on the validation dataset.

    Args:
        model (nn.Module): The model to evaluate.
        dataloader (DataLoader): The data loader for validation data.
        criterion: The loss function.
        device (torch.device): The device to run validation on.
        autocast_dtype: The data type for autocasting.

    Returns:
        tuple: A tuple of average metrics (loss, ssim, psnr, mae, mape).
    """
    model.eval()
    total_loss = total_ssim = total_psnr = total_mae = total_mape = 0.0

    for x, blur_level, y in tqdm(dataloader, desc="Validation", leave=False):
        # Move data to the target device and normalize
        x = x.to(device, non_blocking=True).float().div_(255.0)
        y = y.to(device, non_blocking=True).float().div_(255.0)
        blur_level = blur_level.to(device, non_blocking=True)

        # Use autocast for inference as well
        with get_autocast(autocast_dtype):
            output = model(x, blur_level)
            loss = criterion(output, y)

        # Accumulate metrics
        total_loss += loss.item()
        total_ssim += ssim3D(output, y).item()
        total_psnr += psnr3D(output, y).item()
        total_mae += mae3D(output, y).item()
        total_mape += mape3D(output, y).item()

    # Calculate average metrics
    n = max(1, len(dataloader))
    return total_loss / n, total_ssim / n, total_psnr / n, total_mae / n, total_mape / n


# -----------------------------
# Main Execution Function
# -----------------------------
def main():
    """
    Main function to set up and run the training process.
    This script is designed to run one epoch at a time and then restart itself.
    """
    # --- Configuration ---
    data_dir_train = "train_dataset"
    data_dir_val = "val_dataset"
    batch_size = 52
    num_epochs = 30  # Total number of epochs to train for
    validate_every = 1
    checkpoint_interval_sec = 3600  # Save a checkpoint every hour
    checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    log_file = "training_log.txt"

    # --- Setup Device and Data Type ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    autocast_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    print(f"Using device: {device}, with dtype: {autocast_dtype}")

    # --- Datasets and DataLoaders ---
    blur_levels = [1, 2, 3]
    train_dataset = VoxelDeblurDatasetMultiLevel(data_dir_train, blur_levels)
    val_dataset = VoxelDeblurDatasetMultiLevel(data_dir_val, blur_levels)

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=4,
        persistent_workers=True, pin_memory=True, prefetch_factor=2
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=4,
        persistent_workers=True, pin_memory=True, prefetch_factor=2
    )

    # --- Model, Optimizer, Loss, Scaler ---
    model = DeepCondResUNet3D().to(device)
    try:
        # Compile the model for a significant speed-up (PyTorch 2.0+)
        model = torch.compile(model)
        print("Model compiled successfully.")
    except Exception:
        print("Model compilation failed, running in eager mode.")
        pass

    optimizer = optim.AdamW(model.parameters(), lr=1e-6)
    criterion = nn.MSELoss()
    scaler = get_gradscaler()

    # --- Checkpoint Loading & State Restoration ---
    epoch_to_run = 0
    batch_to_start = 0
    # Find the most recent checkpoint file
    last_ckpts = sorted(
        glob.glob(os.path.join(checkpoint_dir, "ckpt_epoch*.pt")),
        key=os.path.getmtime,
    )
    if last_ckpts:
        latest_ckpt_path = last_ckpts[-1]
        print(f"Loading checkpoint: {latest_ckpt_path}")
        state = torch.load(latest_ckpt_path, map_location=device)
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        scaler.load_state_dict(state["scaler"])
        
        # Determine which epoch to run next
        saved_epoch = state["epoch"]
        saved_batch_idx = state.get("batch_idx", 0) # Use .get for backward compatibility

        # If the last save was mid-epoch (batch_idx > 0), we continue that epoch.
        # Otherwise, we start the next epoch.
        if saved_batch_idx > 0:
             epoch_to_run = saved_epoch
             batch_to_start = saved_batch_idx
             print(f"Resuming mid-epoch run. Starting epoch {epoch_to_run + 1} from batch {batch_to_start + 1}.")
        else:
             epoch_to_run = saved_epoch + 1
             batch_to_start = 0
             print(f"Resuming from end of epoch {saved_epoch + 1}. Starting epoch {epoch_to_run + 1}.")


    # --- Termination Condition ---
    if epoch_to_run >= num_epochs:
        print(f"Training already completed for {num_epochs} epochs. Exiting.")
        return

    # --- Logging Setup ---
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("epoch,train_loss,val_loss,ssim,psnr,mae,mape\n")

    # --- Run a Single Epoch ---
    last_ckpt_time = time.time()

    train_loss, _ = train(
        model, train_loader, optimizer, criterion, scaler, device,
        autocast_dtype, last_ckpt_time, checkpoint_interval_sec,
        checkpoint_dir, epoch_to_run, batch_to_start
    )

    # --- Validation ---
    if (epoch_to_run + 1) % validate_every == 0:
        val_loss, val_ssim, val_psnr, val_mae, val_mape = validate(
            model, val_loader, criterion, device, autocast_dtype
        )
        print(f"Epoch {epoch_to_run+1}/{num_epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | SSIM: {val_ssim:.4f} | PSNR: {val_psnr:.4f}")
    else:
        val_loss = val_ssim = val_psnr = val_mae = val_mape = 0.0
        print(f"Epoch {epoch_to_run+1}/{num_epochs} | Train Loss: {train_loss:.6f} | Validation skipped")

    # --- Log Results ---
    with open(log_file, "a") as f:
        f.write(
            f"{epoch_to_run+1},{train_loss:.6f},{val_loss:.6f},{val_ssim:.4f},{val_psnr:.4f},{val_mae:.6f},{val_mape:.4f}\n"
        )

    # --- Save Final End-of-Epoch Checkpoint ---
    ckpt_path = os.path.join(checkpoint_dir, f"ckpt_epoch{epoch_to_run+1}.pt")
    torch.save(
        {
            "epoch": epoch_to_run, # Save as the completed epoch number
            "batch_idx": 0,  # Indicates end of epoch, so next run starts a new one
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scaler": scaler.state_dict(),
        },
        ckpt_path,
    )
    print(f"Saved end-of-epoch checkpoint to {ckpt_path}")

    # --- Clean up GPU memory ---
    torch.cuda.empty_cache()

    # --- Restart the script for the next epoch ---
    print(f"Epoch {epoch_to_run + 1} finished. Restarting script for the next epoch...")
    # os.execv replaces the current process with a new one, running the same script.
    # This ensures a clean state for the next epoch.
    os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == "__main__":
    main()
```

I use Ubuntu 24, an Nvidia RTX 5080, and Python 3.12. When I run it with PyTorch 2.8 and CUDA 12.9, I get 3.25 it/s. When I run it with PyTorch 2.9 and CUDA 13.0, 12.8, or the preview version, I get only 1.01 it/s. I have updated Ubuntu and the Nvidia driver.

### Comment 2 ([user]):

[user] it looks like we added this assert in (withheld: the upstream fix is not part of the task). Did we expect things to work before?

### Comment 3 ([user]):

[user] is looking at the issue.

### Comment 4 ([user]):

[user] [user] [user] this is actually expected behavior! I am ensuring that we do not max-autotune triton templates with out_dtype, which will lead to completely different numerical outputs. I have (withheld: the upstream fix is not part of the task) which just skips the bmm autotuning silently, though I feel like actually erroring out is better in this case. Essentially, you do not want to use max-autotune torch.compile with bmm out_dtype overload

### Comment 5 ([user]):

Erroring on max-autotune is fine. The existing behavior produced an error with default `torch.compile` too (i.e. max-autotune off). You can narrow the allowed path if desired.

### Comment 6 ([user]):

Ah I see, some template heuristics changes exposed this bug, where it does fire the assert even without max-autotune. Let me put out a fix. I think having it where we silently don't autotune and emit a warning is fine too actually

### Comment 7 ([user]):

(withheld: the upstream fix is not part of the task) should fix

### Comment 8 ([user]):

Confirmed with 2.9.1 it works:
```
(py312) dev@gpu-dev-0f3beb97:~$ python3 test.py 
/home/dev/miniconda3/envs/py312/lib/python3.12/site-packages/torch/_subclasses/functional_tensor.py:279: UserWarning: Failed to initialize NumPy: No module named 'numpy' (Triggered internally at /pytorch/torch/csrc/utils/tensor_numpy.cpp:84.)
  cpu = _conversion_method_template(device=torch.device("cpu"))
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
