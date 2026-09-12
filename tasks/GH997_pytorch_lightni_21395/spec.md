# GH997_pytorch_lightni_21395: Sanitize profile filename — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/21365
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

When using the AdvancedProfiler to create and persist a profile of a training, it is not possible to have a ModelCheckpoint which monitors a variable with a slash in it, e.g. "val/JaccardIndex". The training run will result in a "No such file or directory" error.


### What version are you seeing the problem on?

v2.5

### Reproduced in studio

_No response_

### How to reproduce the bug

```python
profiler_dir.mkdir(parents=True, exist_ok=True)
profiler = AdvancedProfiler(dirpath=profiler_dir, filename="perf_logs", dump_stats=True)

checkpoint_callback = ModelCheckpoint(
            filename="epoch={epoch}-step={step}-val_iou={val/JaccardIndex:.2f}",
            auto_insert_metric_name=False,
            verbose=True,
            monitor="val/JaccardIndex",
            mode="max",
            save_last="link",
            save_top_k=training_config.save_top_k,
        )
L.Trainer(
        callbacks=[checkpoint_callback],
        profiler=profiler,
        ...
    )
```

### Error messages and logs

It seems like the `action_name` of the ModelCheckpoint profiler is `action_name = "[Callback]ModelCheckpoint{'monitor': 'val/JaccardIndex', 'mode': 'max', 'every_n"+73`

```
FileNotFoundError: [Errno 2] No such file or directory: ".../profiler/fit-perf_logs-[Callback]ModelCheckpoint{'monitor': 'val/JaccardIndex', 'mode': 'max', 'every_n_train_steps': 0,'every_n_epochs': 1, 'train_time_interval': None}.setup.prof"
```


### Environment

<details>
  <summary>Current environment</summary>

* CUDA:
        - GPU:
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
                - NVIDIA A100-SXM4-40GB
        - available:         True
        - version:           12.1
* Lightning:
        - lightning:         2.5.5
        - lightning-utilities: 0.15.2
        - pytorch-lightning: 2.5.5
        - segmentation-models-pytorch: 0.5.0
        - torch:             2.5.1+cu121
        - torchmetrics:      1.8.2
        - torchvision:       0.20.1+cu121
* Packages:
        - affine:            2.4.0
        - aiohappyeyeballs:  2.6.1
        - aiohttp:           3.13.1
        - aiohttp-cors:      0.8.1
        - aiosignal:         1.4.0
        - albucore:          0.0.24
        - albumentations:    2.0.8
        - alembic:           1.17.0
        - annotated-types:   0.7.0
        - appdirs:           1.4.4
        - asttokens:         3.0.0
        - attrs:             25.4.0
        - autocommand:       2.2.2
        - babel:             2.17.0
        - backports.tarfile: 1.2.0
        - backrefs:          5.9
        - beautifulsoup4:    4.14.2
        - bleach:            6.2.0
        - bokeh:             3.8.0
        - boto3:             1.40.55
        - botocore:          1.40.55
        - branca:            0.8.2
        - cachetools:        6.2.1
        - cairocffi:         1.7.1
        - cairosvg:          2.8.2
        - cartopy:           0.25.0
        - certifi:           2025.10.5
        - cffi:              2.0.0
        - charset-normalizer: 3.4.4
        - click:             8.2.1
        - click-plugins:     1.1.1.2
        - cligj:             0.7.2
        - cloudpickle:       3.1.1
        - cmdkit:            2.7.7
        - colorama:          0.4.6
        - colorcet:          3.1.0
        - colorful:          0.5.7
        - colorlog:          6.10.1
        - comm:              0.2.3
        - contourpy:         1.3.3
        - cql2:              0.4.0
        - crc32c:            2.8
        - cssselect2:        0.8.0
        - cucim-cu12:        25.10.0
        - cuda-bindings:     13.0.2
        - cuda-pathfinder:   1.3.1
        - cuda-python:       13.0.2
        - cupy-cuda12x:      14.0.0a1
        - cupy-xarray:       0.1.4+14.g1c50016
        - cycler:            0.12.1
        - cyclopts:          3.24.0
        - darts-acquisition: 0.1.0
        - darts-ensemble:    0.1.0
        - darts-export:      0.1.0
        - darts-nextgen:     0.10.0.post13+bf81304
        - darts-postprocessing: 0.1.0
        - darts-preprocessing: 0.1.0
        - darts-segmentation: 0.1.0
        - darts-superresolution: 0.1.0
        - darts-utils:       0.1.0
        - dask:              2025.2.0
        - datashader:        0.18.2
        - debugpy:           1.8.17
        - decorator:         5.2.1
        - defusedxml:        0.7.1
        - deprecated:        1.2.18
        - distlib:           0.4.0
        - distributed:       2025.2.0
        - docstring-parser:  0.17.0
        - docutils:          0.22.2
        - donfig:            0.8.1.post1
        - earthengine-api:   1.6.12
        - executing:         2.2.1
        - fastcore:          1.8.13
        - fastjsonschema:    2.21.2
        - fastrlock:         0.8.3
        - filelock:          3.20.0
        - folium:            0.20.0
        - fonttools:         4.60.1
        - frozenlist:        1.8.0
        - fsspec:            2025.9.0
        - geocube:           0.7.1
        - geopandas:         1.1.1
        - geoviews:          1.14.1
        - ghp-import:        2.1.0
        - gitdb:             4.0.12
        - gitpython:         3.1.45
        - google-api-core:   2.26.0
        - google-api-python-client: 2.185.0
        - google-auth:       2.41.1
        - google-auth-httplib2: 0.2.0
        - google-cloud-core: 2.4.3
        - google-cloud-storage: 3.4.1
        - google-crc32c:     1.7.1
        - google-resumable-media: 2.7.2
        - googleapis-common-protos: 1.71.0
        - greenlet:          3.2.4
        - griffe:            1.14.0
        - grpcio:            1.75.1
        - h5netcdf:          1.7.2
        - h5py:              3.15.1
        - hf-xet:            1.1.10
        - holoviews:         1.21.0
        - httplib2:          0.31.0
        - huggingface-hub:   0.35.3
        - hvplot:            0.12.1
        - icechunk:          0.2.18
        - idna:              3.11
        - imageio:           2.37.0
        - importlib-metadata: 8.7.0
        - importlib-resources: 6.5.2
        - inflect:           7.3.1
        - iniconfig:         2.3.0
        - ipykernel:         7.0.1
        - ipython:           9.6.0
        - ipython-pygments-lexers: 1.1.1
        - ipywidgets:        8.1.7
        - jaraco.collections: 5.1.0
        - jaraco.context:    5.3.0
        - jaraco.functools:  4.0.1
        - jaraco.text:       3.12.1
        - jedi:              0.19.2
        - jinja2:            3.1.6
        - jmespath:          1.0.1
        - joblib:            1.5.2
        - jsonschema:        4.25.1
        - jsonschema-specifications: 2025.9.1
        - jupyter-bokeh:     4.0.5
        - jupyter-client:    8.6.3
        - jupyter-core:      5.9.1
        - jupyterlab-pygments: 0.3.0
        - jupyterlab-widgets: 3.0.15
        - kiwisolver:        1.4.9
        - lazy-loader:       0.4
        - lightning:         2.5.5
        - lightning-utilities: 0.15.2
        - linkify-it-py:     2.0.3
        - llvmlite:          0.45.1
        - locket:            1.0.0
        - lovely-numpy:      0.2.16
        - lovely-tensors:    0.1.19
        - lz4:               4.4.4
        - mako:              1.3.10
        - mapclassify:       2.10.0
        - markdown:          3.9
        - markdown-it-py:    4.0.0
        - markupsafe:        3.0.3
        - matplotlib:        3.10.7
        - matplotlib-inline: 0.1.7
        - mdit-py-plugins:   0.5.0
        - mdurl:             0.1.2
        - mergedeep:         1.3.4
        - mike:              2.1.3
        - mistune:           3.1.4
        - mkdocs:            1.6.1
        - mkdocs-api-autonav: 0.4.0
        - mkdocs-autorefs:   1.4.3
        - mkdocs-get-deps:   0.2.0
        - mkdocs-git-committers-plugin-2: 2.5.0
        - mkdocs-git-revision-date-localized-plugin: 1.4.7
        - mkdocs-glightbox:  0.5.1
        - mkdocs-material:   9.6.22
        - mkdocs-material-extensions: 1.3.1
        - mkdocstrings:      0.30.1
        - mkdocstrings-python: 1.18.2
        - more-itertools:    10.3.0
        - mpmath:            1.3.0
        - msgpack:           1.1.2
        - multidict:         6.7.0
        - multipledispatch:  1.0.0
        - names-generator:   0.2.0
        - narwhals:          2.9.0
        - nbclient:          0.10.2
        - nbconvert:         7.16.6
        - nbformat:          5.10.4
        - nest-asyncio:      1.6.0
        - networkx:          3.5
        - nodeenv:           1.9.1
        - numba:             0.62.1
        - numcodecs:         0.15.1
        - numpy:             2.3.4
        - nvidia-cublas-cu12: 12.1.3.1
        - nvidia-cuda-cupti-cu12: 12.1.105
        - nvidia-cuda-nvrtc-cu12: 12.1.105
        - nvidia-cuda-runtime-cu12: 12.1.105
        - nvidia-cudnn-cu12: 9.1.0.70
        - nvidia-cufft-cu12: 11.0.2.54
        - nvidia-curand-cu12: 10.3.2.106
        - nvidia-cusolver-cu12: 11.4.5.107
        - nvidia-cusparse-cu12: 12.1.0.106
        - nvidia-nccl-cu12:  2.21.5
        - nvidia-nvjitlink-cu12: 12.8.93
        - nvidia-nvtx-cu12:  12.1.105
        - odc-geo:           0.4.10
        - odc-loader:        0.5.1
        - odc-stac:          0.4.0
        - opencensus:        0.11.4
        - opencensus-context: 0.1.3
        - opencv-python-headless: 4.11.0.86
        - opentelemetry-api: 1.38.0
        - opentelemetry-exporter-prometheus: 0.59b0
        - opentelemetry-proto: 1.38.0
        - opentelemetry-sdk: 1.38.0
        - opentelemetry-semantic-conventions: 0.59b0
        - optuna:            4.5.0
        - packaging:         25.0
        - paginate:          0.5.7
        - pandas:            2.3.3
        - pandocfilters:     1.5.1
        - panel:             1.8.2
        - param:             2.2.1
        - parso:             0.8.5
        - partd:             1.4.2
        - pathspec:          0.12.1
        - pexpect:           4.9.0
        - pillow:            11.3.0
        - platformdirs:      4.5.0
        - pluggy:            1.6.0
        - prometheus-client: 0.23.1
        - prompt-toolkit:    3.0.52
        - propcache:         0.4.1
        - proto-plus:        1.26.1
        - protobuf:          6.33.0
        - psutil:            7.1.1
        - psycopg2-binary:   2.9.11
        - ptyprocess:        0.7.0
        - pure-eval:         0.2.3
        - py-spy:            0.4.1
        - pyarrow:           21.0.0
        - pyasn1:            0.6.1
        - pyasn1-modules:    0.4.2
        - pycparser:         2.23
        - pyct:              0.6.0
        - pydantic:          2.12.3
        - pydantic-core:     2.41.4
        - pygments:          2.19.2
        - pymdown-extensions: 10.16.1
        - pynvml:            11.4.1
        - pyogrio:           0.11.1
        - pypalettes:        0.2.1
        - pyparsing:         3.2.5
        - pyperclip:         1.11.0
        - pyproj:            3.7.2
        - pyright:           1.1.406
        - pyshp:             3.0.2.post1
        - pystac:            1.14.1
        - pystac-client:     0.9.0
        - pytest:            8.4.2
        - python-box:        7.3.2
        - python-dateutil:   2.9.0.post0
        - pytorch-lightning: 2.5.5
        - pytz:              2025.2
        - pyviz-comms:       3.0.6
        - pyyaml:            6.0.3
        - pyyaml-env-tag:    1.1
        - pyzmq:             27.1.0
        - rasterio:          1.4.3
        - ray:               2.50.1
        - referencing:       0.37.0
        - requests:          2.32.5
        - rich:              14.2.0
        - rich-rst:          1.3.2
        - rioxarray:         0.19.0
        - rpds-py:           0.27.1
        - rsa:               4.9.1
        - ruff:              0.14.4
        - s3transfer:        0.14.0
        - safetensors:       0.6.2
        - scikit-image:      0.25.2
        - scikit-learn:      1.7.2
        - scipy:             1.16.2
        - seaborn:           0.13.2
        - segmentation-models-pytorch: 0.5.0
        - selectolax:        0.3.29
        - sentry-sdk:        2.42.1
        - setuptools:        80.9.0
        - shapely:           2.1.2
        - simsimd:           6.5.3
        - six:               1.17.0
        - smart-geocubes:    0.0.9
        - smart-open:        7.4.0
        - smmap:             5.0.2
        - sortedcontainers:  2.4.0
        - soupsieve:         2.8
        - spyndex:           0.8.0
        - sqlalchemy:        2.0.44
        - stack-data:        0.6.3
        - stopuhr:           0.0.10
        - stringzilla:       4.2.1
        - sympy:             1.13.1
        - tblib:             3.1.0
        - threadpoolctl:     3.6.0
        - tifffile:          2025.10.16
        - timm:              1.0.20
        - tinycss2:          1.4.0
        - toml:              0.10.2
        - tomli:             2.0.1
        - toolz:             1.1.0
        - torch:             2.5.1+cu121
        - torchmetrics:      1.8.2
        - torchvision:       0.20.1+cu121
        - tornado:           6.5.2
        - tqdm:              4.67.1
        - traitlets:         5.14.3
        - triton:            3.1.0
        - typeguard:         4.3.0
        - typing-extensions: 4.15.0
        - typing-inspection: 0.4.2
        - tzdata:            2025.2
        - uc-micro-py:       1.0.3
        - ultraplot:         1.65.1
        - uritemplate:       4.2.0
        - urllib3:           2.5.0
        - verspec:           0.1.0
        - virtualenv:        20.35.3
        - wandb:             0.22.2
        - watchdog:          6.0.0
        - wcwidth:           0.2.14
        - webencodings:      0.5.1
        - wheel:             0.45.1
        - widgetsnbextension: 4.0.14
        - wrapt:             1.17.3
        - xarray:            2025.10.1
        - xarray-spatial:    0.4.0
        - xee:               0.0.22
        - xpystac:           0.5.0
        - xyzservices:       2025.4.0
        - yarl:              1.22.0
        - zarr:              3.0.10
        - zict:              3.0.0
        - zipp:              3.23.0
* System:
        - OS:                Linux
        - architecture:
                - 64bit
                - ELF
        - processor:         x86_64
        - python:            3.12.9
        - release:           5.15.0-1076-nvidia
        - version:           #77-Ubuntu SMP Tue Mar 25 23:43:36 UTC 2025

</details>

### More info

It seems like having the configuration of the callback in the filename is desired behavior: (withheld: the upstream fix is not part of the task)

However, maybe this should be done differently. Maybe by sanitizing the `action_name` or by doing something similar like `ModelCheckpoint` with `auto_insert_metric_name`.

cc [user] [user]

## PR Review Comments

**[user]** on `src/lightning/pytorch/profilers/profiler.py`:

This looks like an internal flag, and it’s unclear how a user is meant to turn it off.

We should either sanitize unconditionally or treat this as a proper configuration option: pass it through the constructor and store it as an instance attribute so it can be used consistently later.

**[user]** on `src/lightning/pytorch/profilers/profiler.py`:

You are right, I was following the structure of the `split_token` argument which is also purely internal.
Let me correct both arguments.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
