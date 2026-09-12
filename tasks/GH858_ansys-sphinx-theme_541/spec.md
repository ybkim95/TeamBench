# GH858_ansys-sphinx-theme_541: fix: add more components to the search indexing — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ansys/ansys-sphinx-theme/issues/540
- Repo: https://github.com/ansys/ansys-sphinx-theme

## Issue Description

Currently the static search is not working that great whenever our API reference is based on autoapi.

See example: 

![image](https://github.com/user-attachments/assets/42e90acf-ee0f-41c3-9228-de8127134ac0)

I know for a fact that there is a method called "create_design", that is available at https://geometry.docs.pyansys.com/version/stable/api/ansys/geometry/core/modeler/Modeler.html#Modeler.create_design

However, the static search is not indexing properly subsections inside my API page - only summary, description and some other elements are being indexed, making the search completely broken. We should fix this because currently the static search is not usable for our API reference.

Pinging [user]/pyansys-core for visibility

## PR Review Comments

**[user]** on `src/ansys_sphinx_theme/search/fuse_search.py`:

We need to find a better solution for this. I think projects should be able to index on a page-basis. 

By default, all types of nodes are indexed. However, users could use a glob pattern to match certain files for which desired nodes are indexed.

```
index_patterns = {
    "api/*": ALL_NODES,
    "examples/*": PARAGRAPH,
    ...
}
```

**[user]** on `src/ansys_sphinx_theme/search/fuse_search.py`:

yeah sure, we can try to get this, pinging [user]/pyansys-core for insights

**[user]** on `src/ansys_sphinx_theme/search/fuse_search.py`:

works for me

**[user]** on `doc/source/conf.py`:

These shouldn't be strings but aliases implemented in our `__init__.py` file.

```python
PARAGRAPHS = [docutils.nodes.paragraph]
```

Thus, when users use them, we just get a long list of docutils nodes:

```python
TILES + PARAGRAPHS
```

**[user]** on `src/ansys_sphinx_theme/__init__.py`:

We should use the `__all__` to avoid ignoring these warnings.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
