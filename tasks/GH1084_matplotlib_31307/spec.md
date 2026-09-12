# GH1084_matplotlib_31307: FIX: avoid applying dashed patterns to zero-width lines and patches — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/31302
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

If you change `test_stairs_options` to `mpl20` style, then it crashes. What we have worked out is that it is due to artist "G", which sets `ls='--', fill=True`, but does _not_ set a `linewidth`.

The setup for `stairs` sets a default `linewidth=0` if `fill=True`. The difference between classic and mpl20 styles is that the latter performs `linewidth`-scaling on the `linestyle`. So in mpl20 style, the dashes are scaled to 0, which raises in the backend.

> ```
> __________________ test_stairs_options[png] ___________________
> 
> args = (), kwds = {'extension': 'png', 'request': <FixtureRequest for <Function test_stairs_options[png]>>}
> 
>     @wraps(func)
>     def inner(*args, **kwds):
>         with self._recreate_cm():
>           return func(*args, **kwds)
> 
> /usr/lib64/python3.13/contextlib.py:85: 
>  _ _ _ _ _ _ _ _ _ _ _ _
> lib/matplotlib/figure.py:3508: in savefig
>     self.canvas.print_figure(fname, **kwargs)
> lib/matplotlib/backend_bases.py:2275: in print_figure
>     result = print_method(
> lib/matplotlib/backend_bases.py:2132: in <lambda>
>     print_method = functools.wraps(meth)(lambda *args, **kwargs: meth(
> lib/matplotlib/backends/backend_agg.py:539: in print_png
>     self._print_pil(filename_or_obj, "png", pil_kwargs, metadata)
> lib/matplotlib/backends/backend_agg.py:487: in _print_pil
>     FigureCanvasAgg.draw(self)
> lib/matplotlib/backends/backend_agg.py:440: in draw
>     self.figure.draw(self.renderer)
> lib/matplotlib/artist.py:94: in draw_wrapper
>     result = draw(artist, renderer, *args, **kwargs)
> lib/matplotlib/artist.py:71: in draw_wrapper
>     return draw(artist, renderer)
> lib/matplotlib/figure.py:3275: in draw
>     mimage._draw_list_compositing_images(
> lib/matplotlib/image.py:133: in _draw_list_compositing_images
>     a.draw(renderer)
> lib/matplotlib/artist.py:71: in draw_wrapper
>     return draw(artist, renderer)
> lib/matplotlib/axes/_base.py:3282: in draw
>     mimage._draw_list_compositing_images(
> lib/matplotlib/image.py:133: in _draw_list_compositing_images
>     a.draw(renderer)
> lib/matplotlib/artist.py:71: in draw_wrapper
>     return draw(artist, renderer)
> lib/matplotlib/patches.py:740: in draw
>     self._draw_paths_with_artist_properties(
> lib/matplotlib/patches.py:723: in _draw_paths_with_artist_properties
>     gc.set_dashes(*self._dash_pattern)
> _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
> 
> self = <matplotlib.backend_bases.GraphicsContextBase object at 0x7f3016ba3750>, dash_offset = 0.0, dash_list = [0.0, 0.0]
> 
>     def set_dashes(self, dash_offset, dash_list):
>         """
>         Set the dash style for the gc.
>     
>         Parameters
>         ----------
>         dash_offset : float
>             Distance, in points, into the dash pattern at which to
>             start the pattern. It is usually set to 0.
>         dash_list : array-like or None
>             The on-off sequence as points.  None specifies a solid line. All
>             values must otherwise be non-negative (:math:`\\ge 0`).
>     
>         Notes
>         -----
>         See p. 666 of the PostScript
>         `Language Reference
>         <https://www.adobe.com/jp/print/postscript/pdfs/PLRM.pdf>`_
>         for more info.
>         """
>         if dash_list is not None:
>             dl = np.asarray(dash_list)
>             if np.any(dl < 0.0):
>                 raise ValueError(
>                     "All values in the dash list must be non-negative")
>             if dl.size and not np.any(dl > 0.0):
>               raise ValueError(
>                     'At least one value in the dash list must be positive')
> E               ValueError: At least one value in the dash list must be positive
> 
> lib/matplotlib/backend_bases.py:897: ValueError
> ``` 

 _Originally posted by [user] in [#31300]((withheld: the upstream fix is not part of the task)changes/d1d3d894a39e79b6d740a6586909714cd68fc3ef#r2932743766)_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Could be something similar to #28298, where [user] had originally written #29302, but I think that was closed as it was leaking out into user code.

### Comment 2 ([user]):

I opened a PR for this

I was able to reproduce the failure locally with:

```python
plt.style.use("mpl20")
fig, ax = plt.subplots()
ax.stairs([1, 2, 3, 4], [1, 2, 3, 4, 5], fill=True, ls="--")
fig.canvas.draw()
```
The PR fixes this at draw time by avoiding application of dash patterns when the effective linewidth is zero, so it stays narrowly scoped to rendering and does not change stored linestyle state or getter behavior.

### Comment 3 ([user]):

I think we’ve discussed in several places that our linestyle handling is kind of a mess, and properly sorting it out will be complicated.  For the current issue, it seems to me that if a user sets a linestyle then they want to see the line, so we should just not set the width to zero in that case.

### Comment 4 ([user]):

I took the narrower draw-time approach here because I wanted to avoid changing stored linestyle/linewidth behavior more broadly, especially given the earlier concerns around linestyle handling leaking into user state.

If that direction seems preferable, I’m happy to rework the PR accordingly. This is my first contribution here, so I’d appreciate the guidance on the preferred fix direction.

### Comment 5 ([user]):

IMHO, draw-time is the the right solution approach here.

## PR Review Comments

**[user]** on `lib/matplotlib/tests/test_lines.py`:

You should use `fig.draw_without_rendering()` instead of reaching in to the internals.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
