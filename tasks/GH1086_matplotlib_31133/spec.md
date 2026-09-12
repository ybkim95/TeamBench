# GH1086_matplotlib_31133: fix: resolve FigureCanvasTkAgg clipping on Windows HiDPI — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/31126
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

When `FigureCanvasTkAgg` is embedded in a layout-managed container (e.g., a `Frame` with `pack(fill=BOTH, expand=True)`), the plot is rendered larger than the visible canvas area on Windows with HiDPI display scaling (>100%). The right and bottom portions of the figure are clipped/cropped.

The root cause is in `FigureCanvasTk._update_device_pixel_ratio()`: it updates `figure.dpi` via `_set_device_pixel_ratio()` and then calls `self._tkcanvas.configure(width=physical_w, height=physical_h)`. When the canvas is constrained by a geometry manager (`pack`/`grid`), the actual displayed size does not change, so `<Configure>` does not fire, and `resize()` is never called to recalculate `figure.size_inches` with the new DPI. This results in a render buffer that is `device_pixel_ratio` times larger than the visible area.

### Code for reproduction

```Python
"""
Run on Windows with display scaling > 100%.
Expected: Plot fills the visible canvas area correctly.
Actual: Plot is rendered larger than visible area; right/bottom portions are clipped.
"""
import ctypes
import tkinter as tk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Standard Windows HiDPI setup
ctypes.windll.shcore.SetProcessDpiAwareness(1)

root = tk.Tk()
root.geometry("800x600")

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

fig = Figure(dpi=96)
ax = fig.add_subplot(111)
x = np.linspace(0, 2 * np.pi, 100)
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)")
ax.set_xlabel("X Axis - may be clipped")
ax.set_ylabel("Y Axis - may be clipped")
ax.set_title("Embedded FigureCanvasTkAgg - HiDPI clipping bug")
ax.legend()
ax.grid(True)
fig.tight_layout()

canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Diagnostic output
def diagnostics(event=None):
    w = canvas.get_tk_widget()
    cfg_w, cfg_h = int(w["width"]), int(w["height"])
    act_w, act_h = w.winfo_width(), w.winfo_height()
    sz = fig.get_size_inches()
    render_w, render_h = int(sz[0] * fig.dpi), int(sz[1] * fig.dpi)
    print(f"device_pixel_ratio: {canvas.device_pixel_ratio}")
    print(f"figure.dpi: {fig.dpi} (original: {fig._original_dpi})")
    print(f"figure.get_size_inches(): [{sz[0]:.2f}, {sz[1]:.2f}]")
    print(f"Render size: {render_w}x{render_h}")
    print(f"Canvas configured: {cfg_w}x{cfg_h}")
    print(f"Canvas actual:     {act_w}x{act_h}")
    if render_w != act_w or render_h != act_h:
        print(f"BUG: render size ({render_w}x{render_h}) != "
              f"actual size ({act_w}x{act_h})")

root.after(500, diagnostics)
canvas.draw()
root.mainloop()
```

### Actual outcome

On Windows 11 with 150% display scaling:

```
device_pixel_ratio: 1.5
figure.dpi: 144.0 (original: 96)
figure.get_size_inches(): [8.33, 6.25]
Render size: 1200x900
Canvas configured: 1200x900
Canvas actual:     800x600
BUG: render size (1200x900) != actual size (800x600)
```

The plot is rendered at 1200×900 pixels but only 800×600 pixels are visible. The bottom and right portions (axis labels, legend, etc.) are cropped.

Note: this also reproduces **without** manually setting `tk scaling` — just `SetProcessDpiAwareness(1)` is sufficient, because Tk automatically adjusts its scaling factor on HiDPI displays, and `_update_device_pixel_ratio` reads it.

### Expected outcome

The plot should be fully visible within the canvas area with no clipping, regardless of the display scaling factor. The render size should match the actual displayed size.

### Additional information

The chain of events:

1. Canvas is packed → `<Configure>` fires with actual size (800×600) → `resize()` sets `figure.size_inches = (800/96, 600/96) = (8.33, 6.25)`
2. Canvas becomes visible → `<Map>` fires → `_update_device_pixel_ratio()` runs
3. `_set_device_pixel_ratio(1.5)` changes `figure.dpi` from 96 to 144
4. `configure(width=1200, height=900)` sets the canvas **requested** size
5. `pack(fill=BOTH, expand=True)` constrains the **actual** size to 800×600
6. Since actual size didn't change, `<Configure>` does NOT fire
7. `figure.size_inches` is still `(8.33, 6.25)` (calculated with the old dpi=96)
8. Render size = `size_inches × new_dpi = (8.33×144, 6.25×144) = (1200, 900)`
9. But only 800×600 is visible → **right and bottom portions are clipped**

This works correctly in `FigureManagerTk` (matplotlib's own window) because the canvas is packed directly in the top-level window, and `configure()` causes the window to resize, which triggers `<Configure>` → `resize()`. But when the canvas is embedded in a user-managed layout, the geometry manager constrains the size and `<Configure>` may not fire.

### Suggested fix 

After `_set_device_pixel_ratio` changes the DPI and `configure` sets the new requested size, `_update_device_pixel_ratio` should ensure `resize()` is called even if `<Configure>` doesn't fire. For example:

```python
def _update_device_pixel_ratio(self, event=None):
    ratio = None
    if sys.platform == 'win32':
        ratio = round(self._tkcanvas.tk.call('tk', 'scaling') / (96 / 72), 2)
    elif sys.platform == "linux":
        ratio = self._tkcanvas.winfo_fpixels('1i') / 96
    if ratio is not None and self._set_device_pixel_ratio(ratio):
        w, h = self.get_width_height(physical=True)
        self._tkcanvas.configure(width=w, height=h)
        # If the actual displayed size is constrained by a layout manager
        # and didn't change, <Configure> won't fire and resize() won't run.
        # Force a resize to recalculate figure.size_inches with the new DPI.
        self._tkcanvas.update_idletasks()
        actual_w = self._tkcanvas.winfo_width()
        actual_h = self._tkcanvas.winfo_height()
        if actual_w > 0 and actual_h > 0 and (actual_w != w or actual_h != h):
            self.resize(type('Event', (), {'width': actual_w, 'height': actual_h})())
```

### Operating system

Windows 11 (10.0.26200)

### Matplotlib Version

3.10.7 

### Matplotlib Backend

TkAgg

### Python version

3.12.12

### Jupyter version

_No response_

### Installation

conda

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user]  pls assign this to me

### Comment 2 ([user]):

[user] We not assign issues to anyone here read https://matplotlib.org/devdocs/devel/index.html 
if you willing to solve wait for issue to be reviewed and then open the PR directly

### Comment 3 ([user]):

[user] If you resize the window on your machine does the sizing get fixed?  On linux (X11) with hi-dpi I see the initial render come up wrong, but if I manually resize the window it fixes itself.

### Comment 4 ([user]):

> [user] If you resize the window on your machine does the sizing get fixed? On linux (X11) with hi-dpi I see the initial render come up wrong, but if I manually resize the window it fixes itself.

[user] Same here (on Win11), only the initial size is wrong.

### Comment 5 ([user]):

Thank you for confirming that (I use a weird window manager so had some concerns it was something else on my system causing problems and this was a windows-only bug)!

## PR Review Comments

**[user]** on `lib/matplotlib/backends/_backend_tk.py`:

This should have a docstring
```suggestion
    def _resize_canvas(self, width, height):
        """Update figure size and redraw based on a given canvas size."""
```

Also, the name `_resize_canvas` is a bit vague. Should this be `_resize_figure_for_canvas_size`?

**[user]** on `lib/matplotlib/backends/_backend_tk.py`:

Is the description correct? Isn't it primarily that we set the canvas size and then explicitly update the figure size using `_resize_canvas` (or possibly better named `_resize_figure_for_canvas_size()`)? The event seems now an implementation detail of the called `_resize_...` method and seems to not be relevant here anymore.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
