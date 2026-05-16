# GH1006_spaCy_13068: Fix displacy span stacking — Full Specification (Planner Only)

## Source
- PR: https://github.com/explosion/spaCy/pull/13068
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

### Comment 1 (@rmitsch):

Hi @mchlsam, thanks for reporting this! This looks like a bug - we'll look into it and update this thread.

### Comment 2 (@github-actions[bot]):

This thread has been automatically locked since there has not been any recent activity after it was closed. Please open a new issue for related bugs.

## Files Changed in Fix

- `spacy/displacy/render.py` (modified, +30/-9)
- `spacy/tests/test_displacy.py` (modified, +21/-1)

## Diff Summary (What the Fix Changes)

### `spacy/displacy/render.py`
```diff
@@ -142,7 +142,25 @@ def render_spans(
         spans (list): Individual entity spans and their start, end, label, kb_id and kb_url.
         title (str / None): Document title set in Doc.user_data['title'].
         """
-        per_token_info = []
+        per_token_info = self._assemble_per_token_info(tokens, spans)
+        markup = self._render_markup(per_token_info)
+        markup = TPL_SPANS.format(content=markup, dir=self.direction)
+        if title:
+            markup = TPL_TITLE.format(title=title) + markup
+        return markup
+
+    @staticmethod
+    def _assemble_per_token_info(
+        tokens: List[str], spans: List[Dict[str, Any]]
+    ) -> List[Dict[str, List[Dict[str, Any]]]]:
+        """Assembles token info used to generate markup in render_spans().
+        tokens (List[str]): Tokens in text.
+        spans (List[Dict[str, Any]]): Spans in text.
+        RETURNS (List[Dict[str, List[Dict, str, Any]]]): Per token info needed to render HTML markup for given tokens
+            and spans.
+        """
+        per_token_info: List[Dict[str, List[Dict[str, Any]]]] = []
+
         # we must sort so that we can correctly describe when spans need to "stack"
         # which is determined by their start token, then span length (longer spans on top),
         # then break any remaining ties with the span label
@@ -154,29 +172,35 @@ def render_spans(
                 s["label"],
             ),
         )
+
         for s in spans:
             # this is the vertical 'slot' that the span will be rendered in
             # vertical_position = span_label_offset + (offset_step * (slot - 1))
             s["render_slot"] = 0
+
         for idx, token in enumerate(tokens):
             # Identify if a token belongs to a Span (and which) and if it's a
             # start token of said Span. We'll use this for the final HTML render
             token_markup: Dict[str, Any] = {}
             token_markup["text"] = token
-            concurrent_spans = 0
+ 
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
