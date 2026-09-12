# GH337_napari_7018: [bugfix] Adjust scale bar position based on font_size when at top — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/napari/napari

## PR Description

# References and relevant issues
Closes: https://github.com/napari/napari/issues/7009

# Description
This PR aims to fix the visual issues with the scale bar text when the scale bar is positioned at the top, instead of default down.
If the size of the text is changed, the offset from the top of the canvas is increased proportionally.

In the process, this PR does two main things:
- accounts for the canvas DPI when scaling the text size. The defaults (font_size, box height, etc.) were all hard coded around 96 dpi. This PR corrects for that by getting the actual canvas DPI from vispy. A side effect of this is that users with >96 DPI will see the text get smaller -- we may wish to bump up the default from 10 to 11 or 12. 
This has another side effect: partially addressing https://github.com/napari/napari/issues/7516 but just for default font_size, not when font_size is increased.

- computes the logical pixel height of the text in order to account for it in the y_offset from the top of the screen.

Default settings with this PR (just setting top_right):
<img width="852" alt="image" src="https://github.com/user-attachments/assets/a1fd9aa7-1c53-4b97-8e9e-06f112e8d3ac" />
Current napari main:
<img width="836" alt="image" src="https://github.com/napari/napari/assets/76622105/af6e66a6-93b0-4bba-9283-544a8476241e">

Change to font_size 30 with this PR:
<img width="869" alt="image" src="https://github.com/user-attachments/assets/0a59a9e3-b333-4aa7-aacc-aca6f74d5deb" />
versus current napari main:
<img width="841" alt="image" src="https://github.com/napari/napari/assets/76622105/b590855d-baf6-4f78-abb3-30f18b97d226">

Edit: I tested this with my personal mac DPI 149 and with an external display 108. The rendering of the scale_bar was identical to my eyes, side by side.

## PR Review Comments

**[user]** on `napari/_vispy/overlays/scale_bar.py`:

Is this doing anything? If the only time _on_position_change is called is during `on_text_change` if `top` then this will never get called. 

Would it make sense to remove the if/else? Something was throwing me off about the `if 'top'` being used twice. And I can find no other calls to `on_position_change`. Unless, L186 is the mistake and `self._on_position_change()` is always intended to be called after `_on_text_change()`

**[user]** on `napari/_vispy/overlays/scale_bar.py`:

Perhaps this is the intent? 
```suggestion
        self._update_y_offset()
        super()._on_position_change()

    def _update_y_offset(self):
        """Update the y_offset based on the font size and position."""
        if 'top' in self.overlay.position:
            # convert font_size to logical pixels as vispy does
            # 96 dpi is used as the reference dpi
            font_logical_pix = self.overlay.font_size * 96 / 72
            # 7 is base value for the default 10 font size
            self.y_offset = 7 + font_logical_pix
        else:
            self.y_offset = 20
```

**[user]** on `napari/_vispy/overlays/scale_bar.py`:

Well, whatever I have done different just always sets `y_offset` ... which I don't understand, because it should continue to use the same if 'top' functionality... Enjoy my musings after trying to understand why the two `if 'top'`'s lol

**[user]** on `napari/_vispy/overlays/scale_bar.py`:

Not quite, This overlay class inherits from VispyCanvasOverlay and `_on_position_change` is part of the class VispyCanvasOverlay:
https://github.com/napari/napari/blob/2df936857146c3133859345d11251e24a881c700/napari/_vispy/overlays/base.py#L82
which also has events connected to it. (For there record, I find navigating all of the class inheritances really really hard. But, when it's all working well, it does tend to let you focus on just a subset of the problem!)
You can check this by adding a print statement in this `if` and see that it will print whenever the position is changed which includes for example resizing the window.

**[user]** on `napari/_vispy/overlays/scale_bar.py`:

We'd still need to implement a `_on_position_change` that would also call this `_update_y_offset`, because you want to adjust the relative positioning when the scale bar is repositioned to the top, so something like:
```
def _on_position_change(self, event=None):
        self._update_y_offset()
        super()._on_position_change()

```
I'm not sure this refactor is worth it? I think if `_on_position_changed` was a busy callback, then it would make it more readable, but as is, it's just adding boiler plate?
Let's see what Lorenzo has in mind as the architect of all this 😄

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
