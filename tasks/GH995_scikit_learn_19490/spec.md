# GH995_scikit_learn_19490: EHN Support unit-variance whitening for `FastICA`  — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/13056
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

<!--
If your issue is a usage question, submit it here instead:
- StackOverflow with the scikit-learn tag: https://stackoverflow.com/questions/tagged/scikit-learn
- Mailing List: https://mail.python.org/mailman/listinfo/scikit-learn
For more information, see User Questions: http://scikit-learn.org/stable/support.html#user-questions
-->

<!-- Instructions For Filing a Bug: https://github.com/scikit-learn/scikit-learn/blob/master/CONTRIBUTING.md#filing-bugs -->

#### Description
<!-- Example: Joblib Error thrown when calling fit on LatentDirichletAllocation with evaluate_every > 0-->
When performing FastICA using whiten=True attribute, the resulted unmixed signals have a variance of 1/len(data). this can be handled by multiplying the unmixed signals by sqrt(len(data)) in source code before returning it. Also, the unmixing matrix and its inverse must be changed properly to fit the corrected signals

#### Steps/Code to Reproduce
<!--
Example:
```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

docs = ["Help I have a bug" for i in range(1000)]

vectorizer = CountVectorizer(input=docs, analyzer='word')
lda_features = vectorizer.fit_transform(docs)

lda_model = LatentDirichletAllocation(
    n_topics=10,
    learning_method='online',
    evaluate_every=10,
    n_jobs=4,
)
model = lda_model.fit(lda_features)
```
If the code is too long, feel free to put it in a public gist and link
it in the issue: https://gist.github.com
-->
    chnum = eeg_signal.shape[0]
    eeg_signal = eeg_signal.transpose()
    ica = FastICA(n_components=chnum, whiten=True)
    eeg_unmixed = ica.fit_transform(eeg_signal)  # Reconstruct signals
    print(var(eeg_unmixed))
    print(len(eeg_unmixed[0]))
    eeg_unmixed = eeg_unmixed / np.sqrt(np.var(eeg_unmixed))  # this is to handle the scikit learn bug!

#### Expected Results
<!-- Example: No error is thrown. Please paste or describe the expected results.-->
expected a variance = 1
#### Actual Results
<!-- Please paste or specifically describe the actual output or traceback. -->
resulted in variance = 1/len(eeg_signal)
#### Versions
<!--
Please run the following snippet and paste the output below.
For scikit-learn >= 0.20:
import sklearn; sklearn.show_versions()
For scikit-learn < 0.20:
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("NumPy", numpy.__version__)
import scipy; print("SciPy", scipy.__version__)
import sklearn; print("Scikit-Learn", sklearn.__version__)
-->

scikit-learn        0.20.2 
<!-- Thanks for contributing! -->
Thanks,
Hafez

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I don't know much about FastICA, but I agree that this is inconsistent with whiten=False which results in var approximately 1; and that it's bad for the variance of the transformed data to be dependent on sample size.

The question from the software maintenance perspective is: is this a sufficiently blatant bug for us to break backwards compatibility when fixing it? Or should we use a parameter to slowly deprecate the current behaviour?

### Comment 2 ([user]):

There seems to be some related ancient history such as #573 and #2178. I'm
sure [user] will have an opinion on whether the behaviour here is
to be expected.

### Comment 3 ([user]):

No strong opinion: I think that this is indeed a quirk (arguably a bug) that has no good reason. Not having this behavior would probably be desirable.

I don't think that it is a blatant bug that can be changed without some form of smooth evolution to avoid breaking users code.

### Comment 4 ([user]):

Thanks for your help and considerations guys.
In my opinion, anyone who has used this function and didn't consider the bug, maybe had nothing to do with the scaling of the ICA components. The users of the function are mainly digital signal processing experts whose work is to decompose some combined voices or revealing a binary digital signal in a noisy environment. In these cases, the gain level of the ICA components is not so important as they can easily amplify the resulted component by multiplying it with any number they want. Furthermore, as the mixing and unmixing matrices are compatible with the unmixed signals, a full transform and reverse transform of the signals result into the original signals as they are. That's why people hadn't noticed this bug and maybe it will have no effect on their work...
In my work, however, I had to perform a task that needed to modify the signal based on its amplitude. which needs the signal to be as is.
So, in my opinion, we should not be worried about backward compatibility and should fix this bug.
The important note is to consider that the mixing and un-mixing matrices  must also be modified to be compatible with the corrected signals.

### Comment 5 ([user]):

By maintaining backwards compatibility we mean, for example:
* adding a setting whiten='unit-variance'.
* adding a warning when whiten=True saying "From version 0.23,
whiten='unit-variance' by default, and whiten=True will behave like
whiten='unit-variance'."

### Comment 6 ([user]):

Hi! I fixed this one. It would be great if [user] can help me with more test cases.

I created test cases in `decomposition.tests.test_fastica` but when I run them using pytest I can not see the warning message:

`pytest test_fastica`

Any ideas? Do you suggest me that let Travis run the tests instead?

### Comment 7 ([user]):

show us by submitting a PR

### Comment 8 ([user]):

I was refining the code to do the PR and when I ran all the tests some of them failed. For example, in this [line](https://github.com/scikit-learn/scikit-learn/blob/18bac2edc2a18a96ae0bdbfb9241efd2d70b67ee/sklearn/decomposition/tests/test_fastica.py#L97), `np.var(s_)` is not almost 1.0 (in fact, it is something like `9.99E-4`). 


        # Check that the mixing model described in the docstring holds:
        if whiten:
            assert_almost_equal(s_, np.dot(np.dot(mixing_, k_), m))
            # np.var(s_) is not almost 1.0

The test I did checking that the variance in the example of [user] is 1.0 works, but breaks other tests. My question is if the other tests are wrong or in my change I am break something.

PD: I'll do the PR but the tests will not pass, so I don't know if you can see my code.

### Comment 9 ([user]):

Yes, submit a PR and we can take a look at the code and the source of
failure. But perhaps you are just scaling S and also need to scale W to
correspond. I've not looked in detail, but I think the key will be showing
that pre-whitened data gets the same outputs.

### Comment 10 ([user]):

Removing the milestone. Please re-tag if this needs to be reprioritized.

## PR Review Comments

**[user]** on `sklearn/decomposition/_fastica.py`:

```suggestion
            From version 1.3, `whiten='unit-variance'` will be used by default.
```

**[user]** on `sklearn/decomposition/_fastica.py`:

```suggestion
    whiten : str or bool, default="warn"
```

**[user]** on `sklearn/decomposition/_fastica.py`:

```suggestion
        If 'arbitrary-variance' (default), a whitening with variance arbitrary is used.
```

**[user]** on `sklearn/decomposition/_fastica.py`:

```suggestion
```

**[user]** on `sklearn/decomposition/_fastica.py`:

Same changes as above

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
