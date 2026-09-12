# GH864_pytorch_lightni_21108: Fix rich progress bar crashing on empty val dataloader sanity checking — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/20605
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description


When using the `RichProgressBar` callback and setting `num_sanity_val_steps > 0`, but not providing a validation dataloader in the `LightningDataModule`, the training crashes. This only happens when explicitly returning an empty list in val_dataloader.

### What version are you seeing the problem on?

v2.5

### How to reproduce the bug

```python
import lightning as pl
from lightning.pytorch.callbacks import RichProgressBar
from torch.utils.data import DataLoader, Dataset
import torch


class RandomDataset(Dataset):
    def __init__(self, size):
        self.data = torch.randn(size, 10)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], torch.tensor(0)  # Dummy target


class MinimalDataModule(pl.LightningDataModule):
    def train_dataloader(self):
        return DataLoader(RandomDataset(100), batch_size=10)

    # when removing the val_dataloader method completely, the error is not raised
    def val_dataloader(self):
        return []


class MinimalModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 1)

    def forward(self, x):
        return self.linear(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        loss = torch.nn.functional.mse_loss(self(x), y.float().unsqueeze(1))
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        loss = torch.nn.functional.mse_loss(self(x), y.float().unsqueeze(1))
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=0.01)


trainer = pl.Trainer(
    max_epochs=1,
    num_sanity_val_steps=1,  # Set this to 0 to avoid the error
    callbacks=[RichProgressBar()]
)

model = MinimalModel()
data = MinimalDataModule()

trainer.fit(model, datamodule=data)
```

### Error messages and logs

File "C:\Users\tscha\.conda\envs\GRIPSS\lib\site-packages\lightning\pytorch\callbacks\progress\rich_progress.py", line 379, in on_sanity_check_end
    assert self.val_sanity_progress_bar_id is not None
AssertionError



### Environment

<details>
  <summary>Current environment</summary>

* CUDA:
	- GPU:
		- NVIDIA GeForce RTX 4080 Laptop GPU
	- available:         True
	- version:           12.6
* Lightning:
	- lightning:         2.5.0.post0
	- lightning-utilities: 0.12.0
	- pytorch-lightning: 2.5.0.post0
	- torch:             2.6.0+cu126
	- torchaudio:        2.6.0+cu126
	- torchmetrics:      1.6.1
	- torchvision:       0.21.0+cu126
* Packages:
	- aiofiles:          24.1.0
	- aiohappyeyeballs:  2.4.0
	- aiohttp:           3.10.5
	- aiosignal:         1.3.1
	- annotated-types:   0.7.0
	- antlr4-python3-runtime: 4.9.3
	- anyio:             4.4.0
	- argon2-cffi:       23.1.0
	- argon2-cffi-bindings: 21.2.0
	- arrow:             1.3.0
	- astroid:           3.2.4
	- asttokens:         2.4.1
	- async-lru:         2.0.4
	- async-timeout:     4.0.3
	- attrs:             24.2.0
	- autocommand:       2.2.2
	- azure-core:        1.31.0
	- azure-eventhub:    5.12.1
	- azure-identity:    1.17.1
	- babel:             2.14.0
	- backports.tarfile: 1.2.0
	- beautifulsoup4:    4.12.3
	- black:             24.8.0
	- blackdoc:          0.3.9
	- bleach:            6.1.0
	- brotli:            1.1.0
	- bump2version:      1.0.1
	- cached-property:   1.5.2
	- cachetools:        5.5.0
	- certifi:           2024.8.30
	- cffi:              1.17.0
	- cfgv:              3.3.1
	- chardet:           5.2.0
	- charset-normalizer: 3.3.2
	- click:             8.1.7
	- colorama:          0.4.6
	- comm:              0.2.2
	- contourpy:         1.2.1
	- coverage:          7.6.1
	- cryptography:      43.0.1
	- cycler:            0.12.1
	- dataclasses-json:  0.6.7
	- debugpy:           1.8.5
	- decorator:         5.1.1
	- defusedxml:        0.7.1
	- deprecated:        1.2.14
	- detox:             0.19
	- dill:              0.3.8
	- dirtyjson:         1.0.8
	- distlib:           0.3.8
	- distro:            1.9.0
	- dnspython:         2.6.1
	- email-validator:   2.2.0
	- entrypoints:       0.4
	- eventlet:          0.36.1
	- exceptiongroup:    1.2.2
	- execnet:           2.1.1
	- executing:         2.0.1
	- fastapi:           0.112.2
	- fastapi-cli:       0.0.5
	- fastjsonschema:    2.20.0
	- filelock:          3.15.4
	- flake8:            7.1.1
	- fonttools:         4.53.1
	- fqdn:              1.5.1
	- frozenlist:        1.4.1
	- fsspec:            2024.6.1
	- greenlet:          3.0.3
	- gripss-extraction-service: 0.1.0
	- gripss-list-matching: 0.1.2
	- gripss-service-matching-api: 0.1.0
	- gripss-service-matching-backend: 0.1.0
	- gripss-service-matching-helpers: 0.1.0
	- h11:               0.14.0
	- h2:                4.1.0
	- hpack:             4.0.0
	- httpcore:          1.0.5
	- httptools:         0.6.1
	- httpx:             0.27.0
	- hydra-core:        1.3.2
	- hyperframe:        6.0.1
	- identify:          2.6.0
	- idna:              3.8
	- importlib-metadata: 8.4.0
	- importlib-resources: 6.4.4
	- inflect:           7.3.1
	- iniconfig:         2.0.0
	- ipykernel:         6.29.5
	- ipython:           8.26.0
	- ipywidgets:        8.1.5
	- isoduration:       20.11.0
	- isort:             5.13.2
	- jaraco.context:    5.3.0
	- jaraco.functools:  4.0.1
	- jaraco.text:       3.12.1
	- jedi:              0.19.1
	- jinja2:            3.1.4
	- jiter:             0.5.0
	- joblib:            1.4.2
	- json5:             0.9.25
	- jsonpatch:         1.33
	- jsonpointer:       3.0.0
	- jsonschema:        4.23.0
	- jsonschema-specifications: 2023.12.1
	- jupyter-client:    8.6.2
	- jupyter-core:      5.7.2
	- jupyter-events:    0.10.0
	- jupyter-lsp:       2.2.5
	- jupyter-server:    2.14.2
	- jupyter-server-terminals: 0.5.3
	- jupyterlab:        4.2.4
	- jupyterlab-pygments: 0.3.0
	- jupyterlab-server: 2.27.3
	- jupyterlab-widgets: 3.0.13
	- kafka-python-ng:   2.2.2
	- kiwisolver:        1.4.5
	- langchain:         0.2.14
	- langchain-community: 0.2.12
	- langchain-core:    0.2.35
	- langchain-text-splitters: 0.2.2
	- langsmith:         0.1.104
	- lightning:         2.5.0.post0
	- lightning-utilities: 0.12.0
	- llama-index-core:  0.10.56
	- llama-index-embeddings-openai: 0.1.11
	- llama-index-llms-openai: 0.1.26
	- lxml:              5.3.0
	- markdown-it-py:    3.0.0
	- markupsafe:        2.1.5
	- marshmallow:       3.22.0
	- matplotlib:        3.9.2
	- matplotlib-inline: 0.1.7
	- mccabe:            0.7.0
	- mdurl:             0.1.2
	- mistune:           3.0.2
	- mongoengine:       0.28.2
	- more-itertools:    10.4.0
	- motor:             3.5.1
	- mpmath:            1.3.0
	- msal:              1.31.0
	- msal-extensions:   1.2.0
	- multidict:         6.0.5
	- munkres:           1.1.4
	- mypy-extensions:   1.0.0
	- nbclient:          0.10.0
	- nbconvert:         7.16.4
	- nbformat:          5.10.4
	- nest-asyncio:      1.6.0
	- networkx:          3.3
	- nltk:              3.9.1
	- nodeenv:           1.9.1
	- notebook-shim:     0.2.4
	- numpy:             1.26.4
	- omegaconf:         2.3.0
	- openai:            1.42.0
	- ordered-set:       4.1.0
	- orjson:            3.10.7
	- overrides:         7.7.0
	- packaging:         24.1
	- pandas:            2.2.2
	- pandocfilters:     1.5.0
	- parso:             0.8.4
	- pathspec:          0.12.1
	- pickleshare:       0.7.5
	- pillow:            10.4.0
	- pip:               24.2
	- pkgutil-resolve-name: 1.3.10
	- platformdirs:      4.2.2
	- pluggy:            0.13.1
	- portalocker:       2.10.1
	- pre-commit:        3.8.0
	- prometheus-client: 0.20.0
	- prompt-toolkit:    3.0.47
	- psutil:            6.0.0
	- pure-eval:         0.2.3
	- py:                1.11.0
	- pycodestyle:       2.12.1
	- pycparser:         2.22
	- pydantic:          2.8.2
	- pydantic-core:     2.20.1
	- pyflakes:          3.2.0
	- pygments:          2.18.0
	- pyjwt:             2.9.0
	- pylint:            3.2.6
	- pymongo:           4.8.0
	- pymupdf:           1.24.9
	- pymupdfb:          1.24.9
	- pyparsing:         3.1.4
	- pyproject-api:     1.7.1
	- pyside6:           6.7.2
	- pysocks:           1.7.1
	- pytest:            8.3.2
	- pytest-cov:        5.0.0
	- pytest-xdist:      3.6.1
	- python-dateutil:   2.9.0
	- python-docx:       1.1.2
	- python-dotenv:     1.0.1
	- python-json-logger: 2.0.7
	- python-multipart:  0.0.9
	- pytorch-lightning: 2.5.0.post0
	- pytz:              2024.1
	- pywin32:           306
	- pywinpty:          2.0.13
	- pyyaml:            6.0.2
	- pyzmq:             26.2.0
	- referencing:       0.35.1
	- regex:             2024.7.24
	- requests:          2.32.3
	- rfc3339-validator: 0.1.4
	- rfc3986-validator: 0.1.1
	- rich:              13.7.1
	- rpds-py:           0.20.0
	- send2trash:        1.8.3
	- setuptools:        71.0.4
	- shellingham:       1.5.4
	- shiboken6:         6.7.2
	- six:               1.16.0
	- sniffio:           1.3.1
	- soupsieve:         2.5
	- sqlalchemy:        2.0.32
	- stack-data:        0.6.2
	- starlette:         0.38.2
	- sympy:             1.13.1
	- tenacity:          8.5.0
	- tender-service-apis: 0.1.0
	- terminado:         0.18.1
	- tiktoken:          0.7.0
	- tinycss2:          1.3.0
	- toml:              0.10.2
	- tomli:             2.0.1
	- tomlkit:           0.13.2
	- torch:             2.6.0+cu126
	- torchaudio:        2.6.0+cu126
	- torchmetrics:      1.6.1
	- torchvision:       0.21.0+cu126
	- tornado:           6.4.1
	- tox:               3.6.1
	- tqdm:              4.66.5
	- traitlets:         5.14.3
	- typeguard:         4.3.0
	- typer:             0.12.5
	- typer-slim:        0.12.5
	- types-python-dateutil: 2.9.0.20240821
	- typing-extensions: 4.12.2
	- typing-inspect:    0.9.0
	- typing-utils:      0.1.0
	- tzdata:            2024.1
	- ukkonen:           1.0.1
	- unicodedata2:      15.1.0
	- uri-template:      1.3.0
	- urllib3:           2.2.2
	- uvicorn:           0.30.6
	- virtualenv:        20.26.3
	- watchfiles:        0.23.0
	- wcwidth:           0.2.13
	- webcolors:         24.8.0
	- webencodings:      0.5.1
	- websocket-client:  1.8.0
	- websockets:        13.0
	- wheel:             0.44.0
	- widgetsnbextension: 4.0.13
	- win-inet-pton:     1.1.0
	- wrapt:             1.16.0
	- yarl:              1.9.4
	- zipp:              3.20.0
	- zstandard:         0.23.0
* System:
	- OS:                Windows
	- architecture:
		- 64bit
		- WindowsPE
	- processor:         Intel64 Family 6 Model 183 Stepping 1, GenuineIntel
	- python:            3.10.14
	- release:           10
	- version:           10.0.26100

</details>

### More info

I recreated this issue on a Windows machine and on a Mac.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
