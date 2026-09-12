# GH263_astropy_16550: Fix bug for integer compressed images with blanks — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/astropy/astropy/issues/15236
- Repo: https://github.com/astropy/astropy

## Issue Description

### Description

The code for reading compressed FITS files in 5.3 is crashing on loading the images from Pan-STARRS. It was working nicely in 5.2.

The problem manifests like that:
```
$ python -c 'from astropy.io import fits; fits.getdata("http://ps1images.stsci.edu/rings.v3.skycell/1004/016/rings.v3.skycell.1004.016.stk.g.unconv.fits")'
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/ltzfs/ASTRO101/anaconda3/envs/astro101/lib/python3.11/site-packages/astropy/io/fits/convenience.py", line 232, in getdata
    data = hdu.data
           ^^^^^^^^
  File "/ltzfs/ASTRO101/anaconda3/envs/astro101/lib/python3.11/site-packages/astropy/utils/decorators.py", line 837, in __get__
    val = self.fget(obj)
          ^^^^^^^^^^^^^^
  File "/ltzfs/ASTRO101/anaconda3/envs/astro101/lib/python3.11/site-packages/astropy/io/fits/hdu/compressed.py", line 1558, in data
    data = self.section[...]
           ~~~~~~~~~~~~^^^^^
  File "/ltzfs/ASTRO101/anaconda3/envs/astro101/lib/python3.11/site-packages/astropy/io/fits/hdu/compressed.py", line 2189, in __getitem__
    data = decompress_hdu_section(self.hdu, first_tile_index, last_tile_index)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/ltzfs/ASTRO101/anaconda3/envs/astro101/lib/python3.11/site-packages/astropy/io/fits/_tiled_compression/tiled_compression.py", line 442, in decompress_hdu_section
    tile_data[blank_mask] = np.nan
    ~~~~~~~~~^^^^^^^^^^^^
ValueError: cannot convert float NaN to integer
```

### Expected behavior

The images from Pan-STARRS were loading without issues in pre-5.3

### How to Reproduce

```python
from astropy.io import fits
fits.getdata("http://ps1images.stsci.edu/rings.v3.skycell/1004/016/rings.v3.skycell.1004.016.stk.g.unconv.fits")
```

### Versions

Linux-4.18.0-372.9.1.el8.x86_64-x86_64-with-glibc2.28
Python 3.11.4 (main, Jul  5 2023, 13:45:01) [GCC 11.2.0]
astropy 5.3.2
Numpy 1.25.2
pyerfa 2.0.0.3
Scipy 1.11.2
Matplotlib 3.7.2

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail [email redacted].

### Comment 2 ([user]):

Submitted a quick fix to ignore `ZBLANK` in this case so the normal scaling code handles it as before. Note that according to the spec for tile compression, `ZBLANK` shouldn't be set on integer HDUs

https://fits.gsfc.nasa.gov/registry/tilecompression/tilecompression2.3.pdf

> If the uncompressed image has an integer datatype (ZBITPIX > 0) then the reserved BLANK keyword, which already serves this purpose, should be used instead of ZBLANK.

### Comment 3 ([user]):

Hi all - is there a plan to release this fix? Ran into the same issue today with Astropy 5.3.3. Tried upgrading to Astropy 6 with no luck. Ended up downgrading to Astropy 5.2.2 and all worked OK.

### Comment 4 ([user]):

(withheld: the upstream fix is not part of the task) needs a rebase and final review, so unfortunately this problem still stands.

### Comment 5 ([user]):

I just ran into this problem on astropy 5.3.4 and also 6.*. Downgrading to astropy 5.2.2 following [user] solved the problem.

### Comment 6 ([user]):

Hmm! (withheld: the upstream fix is not part of the task) was marked as fixing this issue and should have been released in 6.1.2.

### Comment 7 ([user]):

Ah, I think that is my real issue. I am pegged at astropy 6.0.1 working in python 3.9.16. Sorry for any confusion! Thanks.

## PR Review Comments

**[user]** on `astropy/io/fits/hdu/compressed/compressed.py`:

Shouldn't this warning also tell *what* default value was set so it can more easily be fixed upstream by users who also control the fits-writing code ?

**[user]** on `astropy/io/fits/hdu/compressed/tests/test_tiled_compression.py`:

going full `record` style is only needed in cases where more than one warning is expected, but here we should simplify as
```suggestion
    with pytest.warns(
        AstropyUserWarning, 
        match="Setting default value -32768 for missing BLANK keyword in compressed extension",
    ):
```

**[user]** on `astropy/io/fits/hdu/compressed/tests/test_tiled_compression.py`:

All of this becomes unnecessary with my suggestion above
```suggestion
```

**[user]** on `docs/changes/io.fits/16550.bugfix.rst`:

```suggestion
Fix a spurious exception when reading integer compressed images with blanks.
```

**[user]** on `docs/changes/io.fits/16550.bugfix.rst`:

It is in fact a bug, but I'll accept this anyway!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
