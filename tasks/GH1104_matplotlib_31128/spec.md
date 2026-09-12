# GH1104_matplotlib_31128: Fix relim() ignoring scatter PathCollection offsets — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/30859
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

**ax.relim()** completely ignores changes to scatterplots with **.set_offsets()**.

### Code for reproduction

```Python
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

class App:
    def __init__(self, root):
        self.root = root
        fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(fig, root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, root)

        # Create artists once
        self.scatter = self.ax.scatter([], [])
        self.line, = self.ax.plot([], [])

        root.after(1000, self.update_plot)

    def update_plot(self):
        # New data every update
        xs = np.linspace(0, 10, 100)
        ys = np.sin(xs) + np.random.normal(scale=0.1, size=100)

        # Update artists
        self.scatter.set_offsets(np.column_stack((xs, ys)))
        #self.line.set_data(xs, ys) #Uncomment this to see the expected behaviour

        # Autoscale (not working)
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw_idle()

        # Keep updating
        self.root.after(1000, self.update_plot)

root = tk.Tk()
App(root)
root.mainloop()
```

### Actual outcome

<img width="502" height="574" alt="Image" src="https://github.com/user-attachments/assets/320471a2-82d4-4263-aaa8-913feaf154e7" />

### Expected outcome

<img width="502" height="574" alt="Image" src="https://github.com/user-attachments/assets/9e3c9f7f-0506-4725-94d7-31baa68088ae" />

### Additional information

_No response_

### Operating system

Windows

### Matplotlib Version

3.9.1

### Matplotlib Backend

tkAgg

### Python version

3.11.9

### Jupyter version

None

### Installation

pip

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Limit handling has historically been quite a mess, unfortunately there is little consistency across artists. See (withheld: the upstream fix is not part of the task)#issuecomment-2666989213.

### Comment 2 ([user]):

[user] maybe it can help you, but I did an autoscale function to handle all kind of artist. You can have a look here: https://github.com/mp-007/kivy_matplotlib_widget/blob/main/kivy_matplotlib_widget/uix/graph_subplot_widget.py#L186

It is a built-in function inside my kivy widget, but it can give you some guidelines.

### Comment 3 ([user]):

Hi, I’d like to work on this issue.
I’ll start by reproducing the bug locally and then look into how `relim()` handles scatter artists.

### Comment 4 ([user]):

The PR that "fixed" this was only marked as merged because its commits were contained in a second PR that was merged, but that second PR reverted all the changes from the first PR, so this isn't actually fixed.

## PR Review Comments

**[user]** on `lib/matplotlib/axes/_base.py`:

Please create a method `_update_collection_limits(artist)` so that we have strutural similarity with the patch handling in (withheld: the upstream fix is not part of the task)#issuecomment-2666989213.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
