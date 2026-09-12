# GH147_pyyaml_820: fix `setup.py test`, issue deprecation warning update supported Python metadata — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/yaml/pyyaml/issues/810
- Repo: https://github.com/yaml/pyyaml

## Issue Description

FWICS tests were moved to `tests/legacy_tests` but `setup.py` wasn't updated in 6.0.2rc1:

```pytb
$ python3.12 setup.py test
running test
running build_py
running build_ext
No `pyyaml_build_config` setting found.
skipping 'yaml/_yaml.c' Cython extension (up-to-date)
BUILDING CYTHON EXT; self.include_dirs=['/usr/include/python3.12'] self.library_dirs=['/usr/lib64'] self.define=None
Traceback (most recent call last):
  File "/tmp/pyyaml-6.0.2rc1/setup.py", line 330, in <module>
    setup(
  File "/usr/lib/python3.12/site-packages/setuptools/__init__.py", line 103, in setup
    return distutils.core.setup(**attrs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/site-packages/setuptools/_distutils/core.py", line 184, in setup
    return run_commands(dist)
           ^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/site-packages/setuptools/_distutils/core.py", line 200, in run_commands
    dist.run_commands()
  File "/usr/lib/python3.12/site-packages/setuptools/_distutils/dist.py", line 969, in run_commands
    self.run_command(cmd)
  File "/usr/lib/python3.12/site-packages/setuptools/dist.py", line 968, in run_command
    super().run_command(command)
  File "/usr/lib/python3.12/site-packages/setuptools/_distutils/dist.py", line 988, in run_command
    cmd_obj.run()
  File "/tmp/pyyaml-6.0.2rc1/setup.py", line 309, in run
    import test_all
ModuleNotFoundError: No module named 'test_all'
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This issue emerged slightly differently in some of our failing legacy builds:

```
  Downloading pyyaml-6.0.2rc1.tar.gz (130 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 130.6/130.6 kB 1.6 MB/s eta 0:00:00
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: started
  Getting requirements to build wheel: finished with status 'error'
  error: subprocess-exited-with-error
  
  × Getting requirements to build wheel did not run successfully.
  │ exit code: 1
  ╰─> [19 lines of output]
      Traceback (most recent call last):
        File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 353, in <module>
          main()
        File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 335, in main
          json_out['return_val'] = hook(**hook_input['kwargs'])
        File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 118, in get_requires_for_build_wheel
          return hook(config_settings)
        File "/tmp/pip-download-sc0zai2g/pyyaml_f571e0c609cd4ea296560fe5a4814e47/packaging/_pyyaml_pep517.py", line 47, in _expose_config_settings
          return real_method(*args, **kwargs)
        File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 341, in get_requires_for_build_wheel
          return self._get_build_requires(config_settings, requirements=['wheel'])
        File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 323, in _get_build_requires
          self.run_setup()
        File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 338, in run_setup
          exec(code, locals())
        File "<fstring>", line 1
          (self.include_dirs=)
                            ^
      SyntaxError: invalid syntax
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
error: subprocess-exited-with-error

× Getting requirements to build wheel did not run successfully.
│ exit code: 1
╰─> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.
```

### Comment 2 ([user]):

> This issue emerged slightly differently in some of our failing legacy builds:
> 
> ```
>   Downloading pyyaml-6.0.2rc1.tar.gz (130 kB)
>      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 130.6/130.6 kB 1.6 MB/s eta 0:00:00
>   Installing build dependencies: started
>   Installing build dependencies: finished with status 'done'
>   Getting requirements to build wheel: started
>   Getting requirements to build wheel: finished with status 'error'
>   error: subprocess-exited-with-error
>   
>   × Getting requirements to build wheel did not run successfully.
>   │ exit code: 1
>   ╰─> [19 lines of output]
>       Traceback (most recent call last):
>         File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 353, in <module>
>           main()
>         File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 335, in main
>           json_out['return_val'] = hook(**hook_input['kwargs'])
>         File "/usr/local/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 118, in get_requires_for_build_wheel
>           return hook(config_settings)
>         File "/tmp/pip-download-sc0zai2g/pyyaml_f571e0c609cd4ea296560fe5a4814e47/packaging/_pyyaml_pep517.py", line 47, in _expose_config_settings
>           return real_method(*args, **kwargs)
>         File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 341, in get_requires_for_build_wheel
>           return self._get_build_requires(config_settings, requirements=['wheel'])
>         File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 323, in _get_build_requires
>           self.run_setup()
>         File "/tmp/pip-build-env-gt8xo81a/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 338, in run_setup
>           exec(code, locals())
>         File "<fstring>", line 1
>           (self.include_dirs=)
>                             ^
>       SyntaxError: invalid syntax
>       [end of output]
>   
>   note: This error originates from a subprocess, and is likely not a problem with pip.
> error: subprocess-exited-with-error
> 
> × Getting requirements to build wheel did not run successfully.
> │ exit code: 1
> ╰─> See above for output.
> 
> note: This error originates from a subprocess, and is likely not a problem with pip.
> ```

We have same issue also using py 3.7

### Comment 3 ([user]):

I could not reproduce the `python setup.py test` issue but I have `pip` install issues from pypi.

https://github.com/yaml/pyyaml/blob/a2d19c0234866dc9d4d55abf3009699c258bb72f/setup.py#L355

With _pip_ it installs for all python versions up to 3.12, except 3.6 and 3.7:

```bash
pip install -U pip setuptools
pip install --pre pyyaml
```

# Python 3.7 (fails)

```python
Python 3.7.17
pip        24.0
setuptools 68.0.0

Collecting pyyaml
  Downloading pyyaml-6.0.2rc1.tar.gz (130 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 130.6/130.6 kB 583.2 kB/s eta 0:00:00
  Installing build dependencies ... done
  Getting requirements to build wheel ... error
  error: subprocess-exited-with-error
  
  × Getting requirements to build wheel did not run successfully.
  │ exit code: 1
  ╰─> [19 lines of output]
      Traceback (most recent call last):
        File "/home/denolf/virtualenvs/pybox_PXIQMX/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 353, in <module>
          main()
        File "/home/denolf/virtualenvs/pybox_PXIQMX/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 335, in main
          json_out['return_val'] = hook(**hook_input['kwargs'])
        File "/home/denolf/virtualenvs/pybox_PXIQMX/lib/python3.7/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 118, in get_requires_for_build_wheel
          return hook(config_settings)
        File "/tmp/pip-install-fcb2lvwm/pyyaml_642b39d7e27b4fea961033c121943a5b/packaging/_pyyaml_pep517.py", line 47, in _expose_config_settings
          return real_method(*args, **kwargs)
        File "/tmp/pip-build-env-dpq0y_ow/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 341, in get_requires_for_build_wheel
          return self._get_build_requires(config_settings, requirements=['wheel'])
        File "/tmp/pip-build-env-dpq0y_ow/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 323, in _get_build_requires
          self.run_setup()
        File "/tmp/pip-build-env-dpq0y_ow/overlay/lib/python3.7/site-packages/setuptools/build_meta.py", line 338, in run_setup
          exec(code, locals())
        File "<fstring>", line 1
          (self.include_dirs=)
                            ^
      SyntaxError: invalid syntax
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
error: subprocess-exited-with-error

× Getting requirements to build wheel did not run successfully.
│ exit code: 1
╰─> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.
```  

caused by (f-string with '=' was introduced in python 3.8)

https://github.com/yaml/pyyaml/blob/a2d19c0234866dc9d4d55abf3009699c258bb72f/setup.py#L273

# Python 3.6 (falls back to 6.0.1)

```python
Python 3.6.15
pip        21.3.1
setuptools 59.6.0

Collecting pyyaml
  Downloading pyyaml-6.0.2rc1.tar.gz (130 kB)
     |████████████████████████████████| 130 kB 2.0 MB/s            
  Installing build dependencies ... done
  Getting requirements to build wheel ... error
  ERROR: Command errored out with exit status 1:
   command: /home/denolf/virtualenvs/pybox_mY2umA/bin/python /home/denolf/virtualenvs/pybox_mY2umA/lib/python3.6/site-packages/pip/_vendor/pep517/in_process/_in_process.py get_requires_for_build_wheel /tmp/tmpnoo4bm78
       cwd: /tmp/pip-install-4afg380b/pyyaml_cc0e7d6bd07742d9ac417689267335f5
  Complete output (10 lines):
  Traceback (most recent call last):
    File "/home/denolf/virtualenvs/pybox_mY2umA/lib/python3.6/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 363, in <module>
      main()
    File "/home/denolf/virtualenvs/pybox_mY2umA/lib/python3.6/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 345, in main
      json_out['return_val'] = hook(**hook_input['kwargs'])
    File "/home/denolf/virtualenvs/pybox_mY2umA/lib/python3.6/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 130, in get_requires_for_build_wheel
      return hook(config_settings)
    File "/tmp/pip-install-4afg380b/pyyaml_cc0e7d6bd07742d9ac417689267335f5/packaging/_pyyaml_pep517.py", line 36, in _expose_config_settings
      from contextlib import nullcontext
  ImportError: cannot import name 'nullcontext'
  ----------------------------------------
WARNING: Discarding https://files.pythonhosted.org/packages/ff/08/b6768d9f2da231c1396490e91471ffebb12b299a65cb369c27ec0e2a50c6/pyyaml-6.0.2rc1.tar.gz#sha256=826fb4d5ac2c48b9d6e71423def2669d4646c93b6c13612a71b3ac7bb345304b (from https://pypi.org/simple/pyyaml/) (requires-python:>=3.6). Command errored out with exit status 1: /home/denolf/virtualenvs/pybox_mY2umA/bin/python /home/denolf/virtualenvs/pybox_mY2umA/lib/python3.6/site-packages/pip/_vendor/pep517/in_process/_in_process.py get_requires_for_build_wheel /tmp/tmpnoo4bm78 Check the logs for full command output.
  Using cached PyYAML-6.0.1-cp36-cp36m-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (677 kB)
Installing collected packages: pyyaml
Successfully installed pyyaml-6.0.1
```

caused by (contextlib.nullcontext was introduced in python 3.7)

https://github.com/yaml/pyyaml/blob/a2d19c0234866dc9d4d55abf3009699c258bb72f/packaging/_pyyaml_pep517.py#L36

### Comment 4 ([user]):

Since it was an unintentional regression, PyYAML 6.0.2 restores `setup.py test` to its previous level of functionality (only runs the non-pytest subset of the legacy tests, as before), but also includes a deprecation warning, since `setuptools` long-ago deprecated all direct invocations of `setup.py` commands.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
