# GH988_spaCy_12817: 🐛 Escape annotated HTML tags in span renderer — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/explosion/spaCy/issues/12816
- Repo: https://github.com/explosion/spaCy

## Issue Description

## How to reproduce the behaviour

Here's a test that currently fails:
```python
def test_span_escaping(en_vocab) -> None:
    """Test that displaCy's span visualizer escapes annotated HTML tags correctly."""
    # Create a doc containing an annotated word and an unannotated HTML tag
    doc = Doc(en_vocab, words=["test", "<TEST>"])
    doc.spans["sc"] = [Span(doc, 0, 1, label="test")]

    # Verify that the HTML tag is escaped when unannotated
    html = displacy.render(doc, style="span")
    assert "&lt;TEST&gt;" in html

    # Annotate the HTML tag
    doc.spans["sc"].append(Span(doc, 1, 2, label="test"))

    # Verify that the HTML tag is still escaped
    html = displacy.render(doc, style="span")
    assert "&lt;TEST&gt;" in html
```

The test currently fails on the last line, since the annotated HTML tag is not escaped by the displaCy renderer. Adding a call to `escape_html` here fixes the issue:
https://github.com/explosion/spaCy/blob/ddffd096024004f27a0dee3701dc248c4647b3a7/spacy/displacy/render.py#L221

I ran into this issue when trying to visualize some annotated code documents with `<span>` in some of the documents. This resulted in the documents and span underlines rendering on top of each other at the beginning of the visualization. Adding `escape_html` as described above fixed the rendering issues.

~I have a PR ready to fix this that I'll post as soon as I update the test <-> issue links in the code!~ Posted! 😄 

## Your Environment

- **spaCy version:** 3.6.0
- **Platform:** macOS-13.4.1-arm64-arm-64bit
- **Python version:** 3.11.2

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

PR merged - thanks again!

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
