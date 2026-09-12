# GH859_transformers_17936: Fix all is_torch_tpu_available issues — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/huggingface/transformers/issues/17752
- Repo: https://github.com/huggingface/transformers

## Issue Description

### System Info

```shell
transformer > 4.15.0
Vertex AI Notebook with Pytorch 1.11 using A100
```


### Who can help?

I am very unlucky to have encountered this issue where a TPU device is assumed to be present on the machine, which it doesn't. 
It prompted this error `RuntimeError: tensorflow/compiler/xla/xla_client/computation_client.cc:274 : Missing XLA configuration` and hinted me that something related to TPU is causing the error.

After some debugging, I realized that 

https://github.com/huggingface/transformers/blob/3c7e56fbb11f401de2528c1dcf0e282febc031cd/src/transformers/utils/import_utils.py#L395

is simply checking if `torch_xla` is present as opposed to actually checking whether a TPU device is present. I managed to get it work by simply removing the `torch_xla` package. Yet, I also find it bizarre that there is no way to manually turn off TPU training. I hope that the library can be made to actually check the presence of the TPU.

### Information

- [ ] The official example scripts
- [X] My own modified scripts

### Tasks

- [ ] An officially supported task in the `examples` folder (such as GLUE/SQuAD, ...)
- [X] My own task or dataset (give details below)

### Reproduction

Launch an A100 notebook on GCP Vertex AI and train any model using `Trainer`.

### Expected behavior

```shell
No error.
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'm not sure what the bug is: when you have `torch_xla` installed, the `Trainer` will use it (the terminology uses TPU internally but it works on GPU and CPU as well). Could you give us a reproducer of your error?

### Comment 2 ([user]):

[user] 
Thank you for the response! Below is an example how I reproduced the problem

The only difference is the presence of the `torch_xla` package, installed via 
`!pip install cloud-tpu-client==0.10 https://storage.googleapis.com/tpu-pytorch/wheels/torch_xla-1.11-cp37-cp37m-linux_x86_64.whl`
Models, datasets, nor the versions of the installed packages matter.

## Error
```
!pip list | grep torch

pytorch-lightning              1.5.7
torch                          1.11.0
torch-xla                      1.11
torchmetrics                   0.6.2
torchvision                    0.10.0+cu111
```
### Error message
`RuntimeError: tensorflow/compiler/xla/xla_client/computation_client.cc:273 : Missing XLA configuration`
In certain scenarios, which I don't know how to reproduce right now, it also gives a error resembling `package 'xm' is not found`.

## No error
The template code gives a known error as expected`TypeError: forward() got an unexpected keyword argument 'labels'` . It's ok to ignore this because this is a piece of crude code.

```
!pip uninstall torch_xla -y
!pip list | grep torch
Found existing installation: torch-xla 1.11
Uninstalling torch-xla-1.11:
  Successfully uninstalled torch-xla-1.11
pytorch-lightning              1.5.7
torch                          1.11.0
torchmetrics                   0.6.2
torchvision                    0.10.0+cu111
```


## Training 
``` python
from datasets import load_dataset
   
from transformers import (
 AutoModel, AutoTokenizer, TrainingArguments, Trainer
    )
import gc
import torch

model_name = "distilroberta-base"
ds = load_dataset('rotten_tomatoes', split='train')

default_train_args = {
        "learning_rate": 6e-5,
        "per_device_train_batch_size": 64,
        "per_device_eval_batch_size": 128,
        "num_train_epochs": 7,
        "weight_decay": 1e-6,
        "evaluation_strategy": "steps",
        "eval_steps": 50,
        "save_strategy": "epoch",
        "remove_unused_columns": False,
    }

model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

trainer = Trainer(model=model, args=TrainingArguments("./", **default_train_args), train_dataset=ds)
trainer.train()
```

### Comment 3 ([user]):

I have reproduced this error in multiple environments, here is one of the example, a Vertex AI Notebook.

```
Environment version
M82
Machine type 
n1-standard-16 (16 vCPUs, 60 GB RAM)
GPU 
NVIDIA Tesla T4 x 1
```

### Comment 4 ([user]):

Should be fixed via (withheld: the upstream fix is not part of the task)

### Comment 5 ([user]):

Thank you all so much!

### Comment 6 ([user]):

I get the same error while training a SWIN transformer. It's probably related to the pytorch version. I had a older GCP VM with PyTorch 1.9 and its working fine in it
But with newer Vertex VMs (Pytorch 1.11) it's giving me the same error. 

Uninstalling torch-xla does the work.

### Comment 7 ([user]):

> I get the same error while training a SWIN transformer. It's probably related to the pytorch version. I had a older GCP VM with PyTorch 1.9 and its working fine in it
> But with newer Vertex VMs (Pytorch 1.11) it's giving me the same error. 
> 
> Uninstalling torch-xla does the work. 

Yes, exactly the same scenario. The main reason is that Google's Pytorch 1.11 image is now pre-installed with `torch_xla` in addition to `Trainer`'s unconventional way of checking TPU devices.

### Comment 8 ([user]):

Can you try with installing transformers from git to see if the problem still exists?

E.g.:

`pip install git+https://github.com/huggingface/transformers`

### Comment 9 ([user]):

[user] 
Hi, I ran the same code on the previously mentioned notebook instance with both the dev version `transformers` and `torch_xla` installed, but it stuck indefinitely instead of prompting the expected error `TypeError: forward() got an unexpected keyword argument 'labels'`. The only way I can pause this is restarting/shutdown the notebook.

<img width="869" alt="image" src="https://user-images.githubusercontent.com/42510606/176066277-a902bb69-a2a2-466a-ba65-0eabb154c428.png">

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
