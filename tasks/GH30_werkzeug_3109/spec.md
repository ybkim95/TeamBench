# GH30_werkzeug_3109: consider methods for duplicate rule check — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3105
- Repo: https://github.com/pallets/werkzeug

## Issue Description

The duplicate rule check added in #3038 isn't exact enough. It doesn't account for methods. It can't check equality `self.methods == other.methods`, it needs to check intersection `self.method & other.methods` since _any_ shared method would result in a duplicate. I don't think that's appropriate for `__eq__` though, as it's not exactly equality and `==` is used elsewhere. Also not sure if `strict_slashes` and `merge_slashes` is being accounted for. [user] 

While looking at `Rule.methods` I noticed that it can be `None` instead of a set of values. Why is this? Checks for that are throughout the code, and I also can't find logic saying the default is `GET` in that case. What's going on with that?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I disabled the duplicate check in order to do some more investigation on matching.

`merge_slashes` isn't relevant. The transformation is applied when defining the rule and so `_parts` will already be different. Matching will try the URL both with then without duplicate slashes, but the parts that do the matching remain the same.

`strict_slashes` is weird. For two static rules, it doesn't seem to make a difference to matching when there are explicit rules with and without a slash. It only matters if there's a single rule, in order to perform a redirect.

```python
from werkzeug.routing import Map, Rule

url_map = Map(
    [
        Rule('/a', endpoint="leaf", strict_slashes=True),
        Rule('/a/', endpoint="branch", strict_slashes=True),
    ],
)
urls = url_map.bind("localhost")
print("/a", urls.match("/a")[0])
print("/a/", urls.match("/a/")[0])
```

No matter what order I put the leaf and branch rules in, or what combination of `strict_slashes` I use for each, this always outputs "leaf" then "branch". It's only when I remove the leaf rule that both URLs are matched by branch or raise a redirect.

However, if I use a variable in the branch rule, things get weird.

```python
from werkzeug.routing import Map, Rule

url_map = Map(
    [
        Rule('/a', endpoint="leaf", strict_slashes=False),
        Rule('/<x>/', endpoint="branch", strict_slashes=True),
    ],
)
urls = url_map.bind("localhost")
print("/a", urls.match("/a")[0])
print("/a/", urls.match("/a/")[0])
print("/b/", urls.match("/b/")[0])
```

The order of the rules still doesn't matter. But if the leaf rule has `strict_slashes=False`, then it will match `/a` and `/a/`, even though that's not what happened with the two static rules earlier. `strict_slashes` on the branch rule only affects whether it raises a redirect. But the two rules aren't duplicates, even though they overlap, because the branch rule can match any string.

So I think the answer is that `strict_slashes` shouldn't affect the duplicate check.

### Comment 2 ([user]):

Argh, Flask adds `OPTIONS` to every rule's `methods`, meaning `self.methods & other.methods` is always true in Flask.

### Comment 3 ([user]):

Should probably change how Flask `provide_automatic_options` works, to register a separate rule and endpoint, rather than applying it to everything then overriding it during dispatch.

I guess a heuristic that only considers `OPTIONS` if it's the only method for a rule might work for now.

### Comment 4 ([user]):

This is sort of also a problem with `HEAD`, as `Rule` always adds it if `GET` is in the methods. It looks like this sort of came up in Flask before https://github.com/pallets/flask/issues/4395, and I agree with what I said there. `HEAD` only makes sense when paired with `GET`, and you can test `request.method == "HEAD"` if for some reason a view needs special handling.

I think the following three conditions are enough:

- `a.methods == b.methods`
- `a.methods is None or b.methods is None`
- `(a.methods & b.methods) - {"HEAD", "OPTIONS"}`

That last one will ignore rules that overlap only with `HEAD` and `OPTIONS`, but catch any other overlaps. The first rule, exact match, should catch most cases of deliberate head and options rules.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
