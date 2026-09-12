# GH1006_spaCy_13068: Fix displacy span stacking — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/explosion/spaCy/issues/13056
- Repo: https://github.com/explosion/spaCy

## Issue Description

<!-- NOTE: For questions or install related issues, please open a Discussion instead. -->

Hello,

I'm trying to display spans with displacy render where I built the span manually. 

Several spans can be overlapped.

Sometimes when there are more than 3 spans overlapping, the rendering fails to render properly. 

In the following image spans on the second line have 1 token in common so the render should have done 3 lines, instead it overlapped them.
![image](https://github.com/explosion/spaCy/assets/74212431/4856e75c-d6ef-46ff-aeb3-7578eb166186)


## How to reproduce the behaviour
<!-- Include a code example or the steps that led to the problem. Please try to be as specific as possible. -->
```code
doc_rendering = {
    "text": "Welcome to the Bank of China.",
    "spans": [
        {"start_token": 2, "end_token": 5, "label": "SkillNC"},
        {"start_token": 0, "end_token": 2, "label": "Skill"},
        {"start_token": 1, "end_token": 3, "label": "Skill"},
    ],
    "tokens": ["Welcome", "to", "the", "Bank", "of", "China", "."],
}
```

```code
from spacy import displacy

html = displacy.render(
        doc_rendering,
        style="span",
        manual=True,
        options={"colors": {"Skill": "#56B4E9", "SkillNC": "#FF5733"}},
    )
```

## Your Environment
<!-- Include details of your environment. You can also type `python -m spacy info --markdown` and copy-paste the result here.-->
* Operating System: linux
* Python Version Used: 3.10
* spaCy Version Used: 3.6.1
* Environment Information: conda  23.5.2

Thanks for your help :)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], thanks for reporting this! This looks like a bug - we'll look into it and update this thread.

### Comment 2 ([user]):

This thread has been automatically locked since there has not been any recent activity after it was closed. Please open a new issue for related bugs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
