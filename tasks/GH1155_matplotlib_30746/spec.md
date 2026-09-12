# GH1155_matplotlib_30746: Fix PDF bloat for off-axis scatter with per-point colors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/2488
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

Scatter plotting a bunch of points while specifying the colour of each point, then changing the axes limits so none of the points are visible, and then saving the result to a PDF, results in a file just as big as if the points were all visible within their default axes limits. This doesn't seem to happen if the colour arg isn't passed to `scatter()`. I haven't tried, but specifying other kinds of point specific attributes, like size, might also trigger the problem . Also, I haven't tried any of the other vector backends, but they may be affected as well.

This came out of #2423.

Example code:

``` python
import numpy as np
x = np.random.random(20000)
y = np.random.random(20000)
c = np.random.random(20000)

figure()
scatter(x, y)
pyplot.savefig('scatter.pdf')
xlim(2, 3) # move axes away for empty plot
pyplot.savefig('scatter_empty.pdf')
'''
file sizes in bytes:
scatter.pdf:       324187
scatter_empty.pdf:   6617
'''
figure()
scatter(x, y, c=c)
pyplot.savefig('scatter_color.pdf')
xlim(2, 3) # move axes away for empty plot
pyplot.savefig('scatter_color_empty.pdf')
'''
file sizes in bytes:
scatter_color.pdf:       410722
scatter_color_empty.pdf: 413541
'''
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Closed as I believe that #2423 fixed this problem.

### Comment 2 ([user]):

I was under the impression from [user] that scatter() had a very different code path, and fixing this for scatter would be much more difficult than for plot():

(withheld: the upstream fix is not part of the task)#issuecomment-25535402

Has scatter been tested? I should pull from git to test it out again, but I'm not quite feeling up for that right now...

### Comment 3 ([user]):

[user] Yeah, you are right, closed this erroneously.

### Comment 4 ([user]):

Yes -- scatter is so much more flexible -- each item can have its own transform, and the only way to determine (in the general case) if a patch is off the axes is to actually transform all of its points anyway, which probably doesn't result in terribly large savings (though I suppose one save the stroking time).  If you pre-determine that all of the transformations scale/translation without rotation/skew, one could simply transform the bounding box of the patch to determine whether it's outside of the image, and this would probably be fast enough to be worth the effort.

### Comment 5 ([user]):

Sharing my results on 1.5.3 using TkAgg:

```
01/06/2017  11:31 PM           324,044 scatter.pdf
01/06/2017  11:31 PM           454,639 scatter_color.pdf
01/06/2017  11:31 PM           457,371 scatter_color_empty.pdf
01/06/2017  11:31 PM           326,419 scatter_empty.pdf
```

### Comment 6 ([user]):

This issue has been marked "inactive" because it has been 365 days since the last comment. If this issue is still present in recent Matplotlib releases, or the feature request is still wanted, please leave a comment and this label will be removed. If there are no updates in another 30 days, this issue will be automatically closed, but you are free to re-open or create a new issue if needed. We value issue reports, and this procedure is meant to help us resurface and prioritize issues that have not been addressed yet, not make them disappear.  Thanks for your help!

### Comment 7 ([user]):

This issue remains in matplotlib 3.7.1, Python 3.8, Qt5QAgg backend:

```python
import matplotlib.pyplot as plt
import numpy as np
x = np.random.random(20000)
y = np.random.random(20000)
c = np.random.random(20000)

plt.figure()
plt.scatter(x, y)
plt.savefig('scatter.pdf')
plt.xlim(2, 3) # move axes away for empty plot
plt.savefig('scatter_empty.pdf')
'''
file sizes in bytes:
scatter.pdf:       327682
scatter_empty.pdf:   6313
'''
plt.figure()
plt.scatter(x, y, c=c)
plt.savefig('scatter_color.pdf')
plt.xlim(2, 3) # move axes away for empty plot
plt.savefig('scatter_color_empty.pdf')
'''
file sizes in bytes:
scatter_color.pdf:       582991
scatter_color_empty.pdf: 583963  <--- should be much smaller
'''

### Comment 8 ([user]):

[user] this should probably (unfortunately) be re-opened :)

### Comment 9 ([user]):

I'm going to re-open this and label it as "good first issue" but with medium difficulty.  It is good first issue in that there is no API design choices to be made and two clear metrics to look at (the file size goes down in the special case and the run time does not go up (too much) in the general case).  It is medium difficulty because this will likely require understanding the `draw` code in both `collections.py` and in the pdf generation code.

I think Mike's description in https://github.com/matplotlib/matplotlib/issues/2488#issuecomment-32886813 is still accurate.  We do not know until the very (very) end if a given marker will be clipped or not.

Concretely I see two places we might want to do this:
 - in the `draw` method in `collection.py` that scatter goes through.  We may have to pre-emptively compute the full transform stack to do it, but we could filter the patches there before passing off to the renderers `draw_path_collection` method.  The pro of doing it here is that all backends will get a speed up (the best performance increase is to not do work you do not have to!) but the con is a bunch of extra complexity in the `Collection.draw` method and possibly extra run time.
 - in the `draw_path_collection` in the pdf backend.  At some point we will have the fully computed path for each marker and right before we write it out to the pdf stream we can make a choice to emit it or drop it on the floor.  The pro of this that it is much less unlikely to impose a computational cost we are not already paying, but the con is that in only helps the pdf (and maybe eps/ps as they are all coupled) backends.   The SVG backend may benefit from a similar bit of logic and the Agg backend _might_.


Without actually implementing both of them I do not have a good sense of which is the better approach.  The exact work:

 1. investigate both approaches and verify that they are tractable
 2. if no clear winner yet, implement both
 3. bench mark both that it makes the files smaller in the edge case and the impact on run-time in the general case
 4. add tests

### Comment 10 ([user]):

This issue has been marked "inactive" because it has been 365 days since the last comment. If this issue is still present in recent Matplotlib releases, or the feature request is still wanted, please leave a comment and this label will be removed. If there are no updates in another 30 days, this issue will be automatically closed, but you are free to re-open or create a new issue if needed. We value issue reports, and this procedure is meant to help us resurface and prioritize issues that have not been addressed yet, not make them disappear. Thanks for your help!

## PR Review Comments

**[user]** on `lib/matplotlib/tests/test_backend_pdf.py`:

The 50kb padding is confusing to me.  The axes should be the same output either way (as the limits are the same etc).  If there was anything extra I would expect it to be the structures for the scatter that has no paths (there are some open/close group stuff emitted if I recall correctly).  To account for that we could ad `ax2.scatter([], [])` to the empty test.

It is probably worth also adding a third example where there are markers in in the plot (`ax3.scatter(x+20, y+20, c=c)`) to test that fully off axis one is about the same size as the empty one and both are smaller than the one with visible markers.

**[user]** on `lib/matplotlib/backends/backend_pdf.py`:

Why did you use a maximum extent rather than doing the computation here and having per-maker and per-direction filtering?

We have to compute the extent of every maker no matter what so might as well get the better behavior by doing it here.

**[user]** on `lib/matplotlib/backends/backend_pdf.py`:

Does this write something into the file our only update our Python side sate?

**[user]** on `lib/matplotlib/backends/backend_pdf.py`:

Did you test that this works as expected with log scale and polar?

**[user]** on `lib/matplotlib/tests/test_backend_pdf.py`:

I've updated the tests per your suggestions:
  1. Added `ax2.scatter([], [])` to the baseline test to match the axes structure exactly
  2. Reduced tolerance from 50KB to 5KB since axes output is now identical
  3. Added a third test case with visible markers (x + 20, y + 20, c=c) that validates:
     - Visible scatter is >50KB larger than empty
     - Visible scatter is >50KB larger than off-axis
   
Now, we can compare all three outputs:
* fully off-axis scatter --> small file
* empty scatter --> small file
* visible scatter --> larger file

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
