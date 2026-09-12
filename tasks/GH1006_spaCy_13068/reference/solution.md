# Reference solution — GH1006_spaCy_13068

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1006_spaCy_13068`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1006_spaCy_13068/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

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

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/displacy/render.py`
