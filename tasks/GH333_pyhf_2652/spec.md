# GH333_pyhf_2652: build: Require NumPy v1.22.0 or later — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-hep/pyhf/issues/1772
- Repo: https://github.com/scikit-hep/pyhf

## Issue Description

### Summary

In NumPy `v1.22.0` the `interpolation` argument of [`numpy.percentile`](https://numpy.org/doc/1.22/reference/generated/numpy.percentile.html) was deprecated in favor of `method`. `method` now defaults to `'linear'` but has a total of 9 options, and `interpolation` values of `'nearest'`, `'lower'`, `'higher'`, and `'midpoint'` can only be used when the default `'linear'` method is used.

Running with the deprecated use of `interpolation` now results in the following `DeprecationWarning` being raised.

```pytb
tests/test_validation.py: 1 warning
  /opt/hostedtoolcache/Python/3.9.10/x64/lib/python3.9/site-packages/pyhf/tensor/numpy_backend.py:300: DeprecationWarning: the `interpolation=` argument to percentile was renamed to `method=`, which has additional options.
  Users of the modes 'nearest', 'lower', 'higher', or 'midpoint' are encouraged to review the method they. (Deprecated NumPy 1.22)
    return np.percentile(tensor_in, q, axis=axis, interpolation=interpolation)
```

There isn't any immediate action that should be taken here (in February of 2022) as this change happened in [`numpy` `v1.22.0`](https://pypi.org/project/numpy/1.22.0/) which was released on 2021-12-31. So updating to this new API would force the oldest version of NumPy that could work with `pyhf` to be `v1.22.0`.

The way that `pyhf` installs NumPy is through installing SciPy as [SciPy caps both the oldest and newest versions of NumPy it will work with](https://github.com/scipy/scipy/blob/13b02c7410d63e98113767636f03f979996a2546/setup.py#L446-L461). For the oldest version of Python that `pyhf` supports ([currently Python 3.7](https://github.com/scikit-hep/pyhf/blob/9c9d4d096073793936deac9458f1df85928d7ac7/setup.cfg#L35)) SciPy caps NumPy to `numpy<1.23.0,>=1.16.5`.

```console
$ docker run --rm -ti python:3.7 /bin/bash
root@13658a56a2a3:/# python -m venv venv && . venv/bin/activate
(venv) root@13658a56a2a3:/# python -m pip --quiet install --upgrade pip setuptools wheel
(venv) root@13658a56a2a3:/# python -m pip install scipy
Collecting scipy
  Downloading scipy-1.7.3-cp37-cp37m-manylinux_2_12_x86_64.manylinux2010_x86_64.whl (38.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 38.1/38.1 MB 18.6 MB/s eta 0:00:00
Collecting numpy<1.23.0,>=1.16.5
  Downloading numpy-1.21.5-cp37-cp37m-manylinux_2_12_x86_64.manylinux2010_x86_64.whl (15.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 15.7/15.7 MB 24.5 MB/s eta 0:00:00
Installing collected packages: numpy, scipy
Successfully installed numpy-1.21.5 scipy-1.7.3
```

Note that the upper bound of `numpy<1.23.0` is actually tighter in reality **for Python 3.7** and is effectively `numpy<=1.21.5` given [NEP 29](https://numpy.org/neps/nep-0029-deprecation_policy.html) as NumPy and SciPy both dropped support for Python 3.7 on 2021-12-26. The last Python 3.7 releases were: [`numpy` `v1.21.5`](https://pypi.org/project/numpy/1.21.5/) and [`scipy` `v1.7.3`](https://pypi.org/project/scipy/1.7.3/).

So for Python 3.7, the `numpy` `v1.21.5` API is permanent and the only way to adopt the new `np.percentile`/`np.quantile` API is to also drop support for Python 3.7.

As of the end of 2021, most of the downloads of `pyhf` were coming from Python 3.8+ (according to [PyPI Stats](https://pypistats.org/packages/pyhf), but for many people in physics they are still working on Python 3.7 machines.

[![pypi_stats](https://user-images.githubusercontent.com/5142394/153139197-bdf59084-7582-4573-9dfe-9882075463a7.png)](https://pypistats.org/packages/pyhf)

It would probably be a good idea to wait to update this API and to drop Python 3.7 support until the end of 2022, but we should get early community feedback on this as well. Note that from [PEP 537](https://www.python.org/dev/peps/pep-0537/) we're currently at Python 3.7.12 (released 2021-09-04) and so are in the security fix only stage of the Python 3.7 lifespan with EOL coming in 2023-06.

This also hits JAX as well given it's NumPy dependency

```pytb
  /opt/hostedtoolcache/Python/3.9.10/x64/lib/python3.9/site-packages/jax/_src/numpy/lax_numpy.py:6374: DeprecationWarning: The interpolation= argument to 'quantile' is deprecated. Use 'method=' instead.
    warnings.warn("The interpolation= argument to 'quantile' is deprecated. "
```

### What to do when we do update

When we do update the current API

https://github.com/scikit-hep/pyhf/blob/9c9d4d096073793936deac9458f1df85928d7ac7/src/pyhf/tensor/numpy_backend.py#L300

should get updated to something like the following

```python
        return np.percentile(
            tensor_in, q, axis=axis, method="linear", interpolation=interpolation
        )
```

### Additional Information

This is a good reminder for people to read these two excellent blog posts:
* [Semantic Versioning Will Not Save You](https://hynek.me/articles/semver-will-not-save-you/) by Hynek Schlawack
* [Should You Use Upper Bound Version Constraints?](https://iscinumpy.dev/post/bound-version-constraints/) by Henry Schreiner

### Code of Conduct

- [X] I agree to follow the Code of Conduct

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user]        
 return np.percentile(
            tensor_in, q, axis=axis, method="linear", interpolation=interpolation
        )
so do we have to only update this one ?

### Comment 2 ([user]):

[user] Thanks for your interest, but please read the full Issue. This Issue is meant to be a reminder for the core devs when we address this at the end of 2022.

### Comment 3 ([user]):

> It would probably be a good idea to wait to update this API and to drop Python 3.7 support until the end of 2022, but we should get early community feedback on this as well.

Python 3.7 support has been dropped in PR #2044 and so the next minor release of `pyhf` (`v0.8.0`) will support Python 3.8+. Any `v0.7.x` patch releases will still support Python 3.7.

## PR Review Comments

**[user]** on `src/pyhf/tensor/numpy_backend.py`:

The Sphinx directive should be `versionchanged` instead of `version-changed`. The correct format based on other uses in the codebase should be:

```
.. versionchanged:: 0.8.0
   Argument renamed from *interpolation* to *method* to align with NumPy.
```

The hyphenated form `version-changed` is not a valid Sphinx directive and may not be rendered correctly in documentation.
```suggestion
        .. versionchanged:: 0.8.0
```

**[user]** on `src/pyhf/tensor/jax_backend.py`:

The Sphinx directive should be `versionchanged` instead of `version-changed`. The correct format based on other uses in the codebase should be:

```
.. versionchanged:: 0.8.0
   Argument renamed from *interpolation* to *method* to align with NumPy and JAX.
```

The hyphenated form `version-changed` is not a valid Sphinx directive and may not be rendered correctly in documentation.
```suggestion
        .. versionchanged:: 0.8.0
```

**[user]** on `src/pyhf/tensor/jax_backend.py`:

Bad review. From Sphinx docs: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-version-changed

> Changed in version 9.0: The [versionchanged](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged) directive was renamed to [version-changed](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-version-changed). The previous name is retained as an alias.

**[user]** on `src/pyhf/tensor/numpy_backend.py`:

Bad review. From Sphinx docs: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-version-changed

> Changed in version 9.0: The [versionchanged](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged) directive was renamed to [version-changed](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-version-changed). The previous name is retained as an alias.

**[user]** on `src/pyhf/tensor/jax_backend.py`:

we shouldn't change api here

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
