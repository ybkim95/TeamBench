# GH434_napari_8098: Fix effect of scaling when converting shapes to labels — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/7962
- Repo: https://github.com/napari/napari

## Issue Description

## 🧰 Task
If you open an image and then annotate it using Shapes, because this is more performant or you need defined shapes e.g. straight lines and rectangles, etc., and then use the contextual menu to convert to Labels, the Shapes.extent will be used, so you will get a Labels layer that does not match the size of the image layer.

This is really confusing, because you can't see what's not there, but yet you can't paint in certain areas and when you save the layer for using later it doesn't match what you expect.

When you do this programmatically, you'd typically pass `shape=viewer.layers['image layer']` to `to_labels` so everything is gucci.

I think we should consider that the contextual menu option for Shapes to Labels pass the LayerList.extent to the `shape` kwarg. There will be edge cases where this is unexpected, but I think it's the most obvious and logical behavior because a Shapes layer effectively has infinite extent while annotating.

Edit: this is from my notes from my workshop last year.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

100% agree that this should be the default behavior in the contextual menu. I think this is a good first issue. If anyone wants to tackle this, don't be afraid to reach out!

### Comment 2 ([user]):

For anyone following along, I think this is the place to change the `to_labels` method call to add the `shape` kwarg:
https://github.com/napari/napari/blob/6cd03c044226ba2311cdd4e3423c59fd97053656/src/napari/layers/_layer_actions.py#L53-L60
The layer list is already being accessed, so it's available for the `extent` method.

### Comment 3 ([user]):

Looking into at Scipy

## PR Review Comments

**[user]** on `src/napari/layers/_layer_actions.py`:

```suggestion
            data = lay.to_labels(labels_shape=lay.world_to_data(ll.extent.world[-1]) + 1)
```
I thought about this a bit more and I think transforming from world back to data for setting the **shape** of the labels layer is the correct way to handle this.
I tested with a translation and scale -- not both at the same time -- and it worked as expected!
Would be good to sanity check a bit more, it's a bit late 😴 

Also, it took me a while to get the `+1` -- I was very confused.
Then I realized that extent goes from 0 to `shape - 1` while this kwarg is **shape** so we need the `+1` my suggestion is to add a comment about that, unless folks feel it's too obvious and trivial and i'm just 😴

**[user]** on `src/napari/layers/_layer_actions.py`:

If I understand this comment correctly, what you want here is the `ll._extent_world_augmented` (extent which accounts for data voxel/point sizes).

```suggestion
            ll_shape = ll._extent_world_augmented[1] - ll._extent_world_augmented[0]
            data = lay.to_labels(
                labels_shape=lay.world_to_data(ll_shape)
            )
```

Looks like there's no need for converting to int because this already happens in the `to_labels()` method.

**[user]** on `src/napari/layers/_layer_actions.py`:

no matter what, I sympathize [user], this part of the code base is really hard for me to understand, and I've mucked about quite a few times. 🙃

**[user]** on `src/napari/layers/_layer_actions.py`:

Thanks [user] ! I knew there had to be a better way. [user] was a trooper for working through all the caveats in synthetic tests and a real viewer. I will try to find some time to look more carefully -- i'm frantically trying to catch up on a week worth of missed work right now.

**[user]** on `src/napari/layers/_layer_actions.py`:

I played with this some more and I think the suggestion here is close, but then I ran into issues, but they're on main:
https://github.com/napari/napari/issues/8115
I will try to clean up what I have and make suggestion.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
