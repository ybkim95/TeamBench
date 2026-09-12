# GH221_astropy_19294: Support for fsspec filesystem configuration via fits.open — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/astropy/astropy/issues/19292
- Repo: https://github.com/astropy/astropy

## Issue Description

### Description

The astropy [docs for cloud FITS](https://docs.astropy.org/en/stable/io/fits/usage/cloud.html#configuring-the-fsspec-block-size-and-download-strategy) suggests that the user can set the cache block size like so:
```python
fsspec_kwargs = {"block_size": 1_000_000, "cache_type": "bytes"}
with fits.open(url, use_fsspec=True, fsspec_kwargs=fsspec_kwargs) as hdul:
    cutout = hdul[1].section[10:20, 30:50]
```
When I try running the above example using data in an S3 bucket
```python
url = "s3://stpubdata/jwst/public/jw01345/jw01345001001/jw01345001001_10201_00001_nrca2_cal.fits"
```
the `block_size` kwarg isn't recognized.

Full traceback below:
<details>

<summary>Traceback</summary>

```
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[11], line 4
      1 prefix = "s3://stpubdata/jwst/public/jw01345/jw01345001001/jw01345001001_10201_00001_nrca2_cal.fits"
      2 fsspec_kwargs = {"anon": True, "blocksize": 1_000_000, "cache_type": "bytes"}
----> 4 with fits.open(prefix, fsspec_kwargs=fsspec_kwargs) as hdus:
      5     cutout2 = hdus[1].section[:2, :2]

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py:220](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py#line=219), in fitsopen(name, mode, memmap, save_backup, cache, lazy_load_hdus, ignore_missing_simple, use_fsspec, fsspec_kwargs, decompress_in_memory, **kwargs)
    217 if not name:
    218     raise ValueError(f"Empty filename: {name!r}")
--> 220 return HDUList.fromfile(
    221     name,
    222     mode,
    223     memmap,
    224     save_backup,
    225     cache,
    226     lazy_load_hdus,
    227     ignore_missing_simple,
    228     use_fsspec=use_fsspec,
    229     fsspec_kwargs=fsspec_kwargs,
    230     decompress_in_memory=decompress_in_memory,
    231     **kwargs,
    232 )

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py:484](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py#line=483), in HDUList.fromfile(cls, fileobj, mode, memmap, save_backup, cache, lazy_load_hdus, ignore_missing_simple, **kwargs)
    465 @classmethod
    466 def fromfile(
    467     cls,
   (...)    475     **kwargs,
    476 ):
    477     """
    478     Creates an `HDUList` instance from a file-like object.
    479 
   (...)    482     documentation for details of the parameters accepted by this method).
    483     """
--> 484     return cls._readfrom(
    485         fileobj=fileobj,
    486         mode=mode,
    487         memmap=memmap,
    488         save_backup=save_backup,
    489         cache=cache,
    490         ignore_missing_simple=ignore_missing_simple,
    491         lazy_load_hdus=lazy_load_hdus,
    492         **kwargs,
    493     )

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py:1186](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/hdu/hdulist.py#line=1185), in HDUList._readfrom(cls, fileobj, data, mode, memmap, cache, lazy_load_hdus, ignore_missing_simple, use_fsspec, fsspec_kwargs, decompress_in_memory, **kwargs)
   1183 if fileobj is not None:
   1184     if not isinstance(fileobj, _File):
   1185         # instantiate a FITS file object (ffo)
-> 1186         fileobj = _File(
   1187             fileobj,
   1188             mode=mode,
   1189             memmap=memmap,
   1190             cache=cache,
   1191             use_fsspec=use_fsspec,
   1192             fsspec_kwargs=fsspec_kwargs,
   1193             decompress_in_memory=decompress_in_memory,
   1194         )
   1195     # The Astropy mode is determined by the _File initializer if the
   1196     # supplied mode was None
   1197     mode = fileobj.mode

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/file.py:212](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/io/fits/file.py#line=211), in _File.__init__(self, fileobj, mode, memmap, overwrite, cache, use_fsspec, fsspec_kwargs, decompress_in_memory)
    202 # Handle cloud-hosted files using the optional ``fsspec`` dependency
    203 if (use_fsspec or _requires_fsspec(fileobj)) and mode != "ostream":
    204     # Note: we don't use `get_readable_fileobj` as a context manager
    205     # because io.fits takes care of closing files itself
    206     fileobj = get_readable_fileobj(
    207         fileobj,
    208         encoding="binary",
    209         use_fsspec=use_fsspec,
    210         fsspec_kwargs=fsspec_kwargs,
    211         close_files=False,
--> 212     ).__enter__()
    214 # Handle raw URLs
    215 if (
    216     isinstance(fileobj, (str, bytes))
    217     and mode not in ("ostream", "append", "update")
    218     and _is_url(fileobj)
    219 ):

File [/opt/conda/envs/roman-cal/lib/python3.12/contextlib.py:137](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/contextlib.py#line=136), in _GeneratorContextManager.__enter__(self)
    135 del self.args, self.kwds, self.func
    136 try:
--> 137     return next(self.gen)
    138 except StopIteration:
    139     raise RuntimeError("generator didn't yield") from None

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/utils/data.py:351](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/astropy/utils/data.py#line=350), in get_readable_fileobj(name_or_obj, encoding, cache, show_progress, remote_timeout, sources, http_headers, use_fsspec, fsspec_kwargs, close_files)
    349     openfileobj = fsspec.open(name_or_obj, **fsspec_kwargs)
    350     close_fds.append(openfileobj)
--> 351     fileobj = openfileobj.open()
    352     close_fds.append(fileobj)
    353 else:

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/core.py:147](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/core.py#line=146), in OpenFile.open(self)
    140 def open(self):
    141     """Materialise this as a real open file without context
    142 
    143     The OpenFile object should be explicitly closed to avoid enclosed file
    144     instances persisting. You must, therefore, keep a reference to the OpenFile
    145     during the life of the file-like it generates.
    146     """
--> 147     return self.__enter__()

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/core.py:105](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/core.py#line=104), in OpenFile.__enter__(self)
    102 mode = self.mode.replace("t", "").replace("b", "") + "b"
    104 try:
--> 105     f = self.fs.open(self.path, mode=mode)
    106 except FileNotFoundError as e:
    107     if has_magic(self.path):

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py:1349](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py#line=1348), in AbstractFileSystem.open(self, path, mode, block_size, cache_options, compression, **kwargs)
   1347 else:
   1348     ac = kwargs.pop("autocommit", not self._intrans)
-> 1349     f = self._open(
   1350         path,
   1351         mode=mode,
   1352         block_size=block_size,
   1353         autocommit=ac,
   1354         cache_options=cache_options,
   1355         **kwargs,
   1356     )
   1357     if compression is not None:
   1358         from fsspec.compression import compr

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py:733](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py#line=732), in S3FileSystem._open(self, path, mode, block_size, acl, version_id, fill_cache, cache_type, autocommit, size, requester_pays, cache_options, **kwargs)
    730 if cache_type is None:
    731     cache_type = self.default_cache_type
--> 733 return S3File(
    734     self,
    735     path,
    736     mode,
    737     block_size=block_size,
    738     acl=acl,
    739     version_id=version_id,
    740     fill_cache=fill_cache,
    741     s3_additional_kwargs=kw,
    742     cache_type=cache_type,
    743     autocommit=autocommit,
    744     requester_pays=requester_pays,
    745     cache_options=cache_options,
    746     size=size,
    747 )

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py:2295](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py#line=2294), in S3File.__init__(self, s3, path, mode, block_size, acl, version_id, fill_cache, s3_additional_kwargs, autocommit, cache_type, requester_pays, cache_options, size)
   2293         self.details = s3.info(path)
   2294         self.version_id = self.details.get("VersionId")
-> 2295 super().__init__(
   2296     s3,
   2297     path,
   2298     mode,
   2299     block_size,
   2300     autocommit=autocommit,
   2301     cache_type=cache_type,
   2302     cache_options=cache_options,
   2303     size=size,
   2304 )
   2305 self.s3 = self.fs  # compatibility
   2307 # when not using autocommit we want to have transactional state to manage

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py:1923](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py#line=1922), in AbstractBufferedFile.__init__(self, fs, path, mode, block_size, autocommit, cache_type, cache_options, size, **kwargs)
   1921         self.size = size
   1922     else:
-> 1923         self.size = self.details["size"]
   1924     self.cache = caches[cache_type](
   1925         self.blocksize, self._fetch_range, self.size, **cache_options
   1926     )
   1927 else:

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py:1936](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/spec.py#line=1935), in AbstractBufferedFile.details(self)
   1933 @property
   1934 def details(self):
   1935     if self._details is None:
-> 1936         self._details = self.fs.info(self.path)
   1937     return self._details

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py:118](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py#line=117), in sync_wrapper.<locals>.wrapper(*args, **kwargs)
    115 @functools.wraps(func)
    116 def wrapper(*args, **kwargs):
    117     self = obj or args[0]
--> 118     return sync(self.loop, func, *args, **kwargs)

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py:103](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py#line=102), in sync(loop, func, timeout, *args, **kwargs)
    101     raise FSTimeoutError from return_result
    102 elif isinstance(return_result, BaseException):
--> 103     raise return_result
    104 else:
    105     return return_result

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py:56](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/fsspec/asyn.py#line=55), in _runner(event, coro, result, timeout)
     54     coro = asyncio.wait_for(coro, timeout=timeout)
     55 try:
---> 56     result[0] = await coro
     57 except Exception as ex:
     58     result[0] = ex

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py:1471](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py#line=1470), in S3FileSystem._info(self, path, bucket, key, refresh, version_id)
   1469 if key:
   1470     try:
-> 1471         out = await self._call_s3(
   1472             "head_object",
   1473             self.kwargs,
   1474             Bucket=bucket,
   1475             Key=key,
   1476             **version_id_kw(version_id),
   1477             **self.req_kw,
   1478         )
   1479         return {
   1480             "ETag": out.get("ETag", ""),
   1481             "LastModified": out.get("LastModified", ""),
   (...)   1487             "ContentType": out.get("ContentType"),
   1488         }
   1489     except FileNotFoundError:

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py:377](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py#line=376), in S3FileSystem._call_s3(self, method, *akwarglist, **kwargs)
    376 async def _call_s3(self, method, *akwarglist, **kwargs):
--> 377     await self.set_session()
    378     s3 = await self.get_s3(kwargs.get("Bucket"))
    379     method = getattr(s3, method)

File [/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py:560](https://roman.science.stsci.edu/opt/conda/envs/roman-cal/lib/python3.12/site-packages/s3fs/core.py#line=559), in S3FileSystem.set_session(self, refresh, kwargs)
    558 conf = AioConfig(**config_kwargs)
    559 if self.session is None or refresh:
--> 560     self.session = aiobotocore.session.AioSession(**self.kwargs)
    562 for parameters in (config_kwargs, self.kwargs, init_kwargs, client_kwargs):
    563     for option in ("region_name", "endpoint_url"):

TypeError: AioSession.__init__() got an unexpected keyword argument 'blocksize'
```

</details>

### Expected behavior

The expected section of the remote FITS file should be retrieved in blocks of size `block_size`

### Versions

```python
import astropy
astropy.system_info()
```
```
platform
--------
platform.platform() = 'Linux-6.1.141-155.222.amzn2023.x86_64-x86_64-with-glibc2.39'
platform.version() = '#1 SMP PREEMPT_DYNAMIC Tue Jun 17 10:29:47 UTC 2025'
platform.python_version() = '3.12.12'

packages
--------
astropy              7.2.0
numpy                2.3.5
scipy                1.16.3
matplotlib           3.10.8
pandas               2.3.3
pyerfa               2.0.1.5
```
fsspec version: `2025.12.0`.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The example seems to be enabled for remote data doctest. Is this bucket of yours set up the same as the bucket in example?

```python
s3_uri = "s3://stpubdata/hst/public/j8pu/j8pu0y010/j8pu0y010_drc.fits"
```

### Comment 2 ([user]):

I can't be sure, I'll see what I can find out.

It works when you call the same code block but skip astropy fits in favor of `fsspec` to open the file stream:
```python
import fsspec
from astropy.io import fits

url = "s3://stpubdata/jwst/public/jw01345/jw01345001001/jw01345001001_10201_00001_nrca2_cal.fits"

fsspec_kwargs = {"anon": True, "block_size": 1_000_000, "cache_type": "bytes"}

fs = fsspec.filesystem('s3', anon=True)
file_obj = fs.open(url, **fsspec_kwargs)
fits_hdus = fits.open(file_obj)
print(fits_hdus[1].section[:4, :4])
```

### Comment 3 ([user]):

Using the prefix you mentioned above:
```python
prefix = "s3://stpubdata/hst/public/j8pu/j8pu0y010/j8pu0y010_drc.fits"
fsspec_kwargs = {"anon": True, "block_size": 1_000_000, "cache_type": "bytes"}

with fits.open(prefix, fsspec_kwargs=fsspec_kwargs) as hdus:
    cutout2 = hdus[1].section[:2, :2]
```
gives the same traceback.

### Comment 4 ([user]):

It seems to stem from using `fsspec.open` here:

https://github.com/astropy/astropy/blob/a7a30429a72f181b981899c29f755a8b1db32b5a/astropy/utils/data.py#L349

If you first specify the `filesystem` and then call `filesystem.open` with the same kwargs, it works:
```python
fsspec_kwargs = {"block_size": 1_000_000, "cache_type": "bytes"}

## this fails:
# with fsspec.open(prefix, **fsspec_kwargs) as hdul:
#     cutout = hdul[1].section[10:20, 30:50]

## this works:
with fsspec.filesystem('s3', anon=True).open(prefix, **fsspec_kwargs) as file_obj:
    hdul = fits.open(file_obj)
    cutout = hdul[1].section[:4, :4]
```

### Comment 5 ([user]):

Okay, now I am confused. The code being tested is actually using

```python
url = "https://mast.stsci.edu/api/v0.1/Download/file/?uri=mast:HST/product/j8pu0y010_drc.fits"
```

and not `s3_uri`. The `url` works. This example was added in (withheld: the upstream fix is not part of the task). Is this a bug in the example, [user] ?

### Comment 6 ([user]):

I can think of >1 reason we may not want to do this, but replacing 

https://github.com/astropy/astropy/blob/a7a30429a72f181b981899c29f755a8b1db32b5a/astropy/utils/data.py#L349

with
```python
            if isinstance(name_or_obj, str) and name_or_obj.lower().startswith('s3'):
                fs = fsspec.filesystem('s3', anon=True)
                openfileobj = fileobj = fs.open(name_or_obj, **fsspec_kwargs)

            else:
                openfileobj = fsspec.open(name_or_obj, **fsspec_kwargs)
                fileobj = openfileobj.open()
```
solves the problem.

### Comment 7 ([user]):

Not sure if hardcoding `anon=True` is a good idea. Feel free to open a PR for discussion. Thanks!

### Comment 8 ([user]):

Agreed, it could be a kwarg. Alternatively/better: let the user pass in the `filesystem`.

## PR Review Comments

**[user]** on `astropy/utils/data.py`:

what about making this even more explicit, e.g. `fsspec_filesystem_kwargs`?

**[user]** on `docs/io/fits/usage/cloud.rst`:

Please update this documentation

**[user]** on `astropy/utils/data.py`:

I'm ok with that, only opted to drop `fsspec_` because all together it's a lot of characters.

**[user]** on `astropy/utils/data.py`:

I think the clarity is worth the extra characters; and if abbreviation is needed then I would instead drop `filesystem` for `fs`; but still think the whole spell out is worth it for this case.

**[user]** on `astropy/utils/data.py`:

The order should match signature above.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
