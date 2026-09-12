# GH61_werkzeug_3097: rewrite build docstring — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3094
- Repo: https://github.com/pallets/werkzeug

## Issue Description

As an application developer, my expectation is that a URL returned by `app.url_for('endpoint', **params)` will resolve to `endpoint`. However, depending on the params, this is not always the case. It’s possible that the param values don’t match the routing converters, and yet Flask will put them into the URL, resulting in a 404 response; and it’s possible that the param values will actually select a different endpoint altogether.

Consider the following example application (which is not a great application, but that’s not the point):
```python
import flask

app = flask.Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:5000'

@app.route('/user/<id>')
def user_by_id(id):
    return f'user_by_id({id=})'

@app.route('/user/current')
def current_user():
    return 'current_user()'

@app.route('/user/<id>/delete')
def delete_user_by_id(id):
    return f'delete_user_by_id({id=})'

@app.route('/user_int/<int:id>')
def user_by_numeric_id(id: int):
    return f'user_by_numeric_id({id=})'

print(f'{app.url_for('user_by_id', id='123')=}')
print(f'{app.url_for('user_by_id', id='current')=}')
print(f'{app.url_for('user_by_id', id='123/delete')=}')
print(f'{app.url_for('user_by_numeric_id', id=123)=}')
print(f'{app.url_for('user_by_numeric_id', id='123')=}')
print(f'{app.url_for('user_by_numeric_id', id='123/delete')=}')
```

Output:
```
app.url_for('user_by_id', id='123')='http://localhost:5000/user/123'
app.url_for('user_by_id', id='current')='http://localhost:5000/user/current'
app.url_for('user_by_id', id='123/delete')='http://localhost:5000/user/123/delete'
app.url_for('user_by_numeric_id', id=123)='http://localhost:5000/user_int/123'
app.url_for('user_by_numeric_id', id='123')='http://localhost:5000/user_int/123'
Traceback (most recent call last):
[snip]
ValueError: invalid literal for int() with base 10: '123/delete'
```

The first URL is fine. The second will actually resolve to the `current_user` endpoint, not to `user_by_id`; the third URL will resolve to `delete_user_by_id()`, even though `123/delete` is not a valid value for `id` to begin with (the default `string` converter “accepts any text without a slash”, see [URL Route Registrations](https://flask.palletsprojects.com/en/stable/api/#url-route-registrations)). The fourth and fifth URLs are fine again; the sixth call demonstrates that the `int` converter apparently *does* check whether the given value is valid or not, raising an error instead of returning an invalid URL (yet the `string` converter doesn’t?).

<details><summary>full traceback of the last call</summary>

```
Traceback (most recent call last):
  File "/tmp/app.py", line 27, in <module>
    print(f'{app.url_for('user_by_numeric_id', id='123/delete')=}')
             ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/venv/lib/python3.14/site-packages/flask/app.py", line 1110, in url_for
    rv = url_adapter.build(  # type: ignore[union-attr]
        endpoint,
    ...<3 lines>...
        force_external=_external,
    )
  File "/tmp/venv/lib/python3.14/site-packages/werkzeug/routing/map.py", line 922, in build
    rv = self._partial_build(endpoint, values, method, append_unknown)
  File "/tmp/venv/lib/python3.14/site-packages/werkzeug/routing/map.py", line 801, in _partial_build
    rv = self._partial_build(
        endpoint, values, self.default_method, append_unknown
    )
  File "/tmp/venv/lib/python3.14/site-packages/werkzeug/routing/map.py", line 814, in _partial_build
    build_rv = rule.build(values, append_unknown)
  File "/tmp/venv/lib/python3.14/site-packages/werkzeug/routing/rules.py", line 850, in build
    return self._build_unknown(**values)
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "<werkzeug routing>", line 1, in <builder:'/user_int/<int:id>'>
  File "/tmp/venv/lib/python3.14/site-packages/werkzeug/routing/converters.py", line 163, in to_url
    value_str = str(self.num_convert(value))
                    ~~~~~~~~~~~~~~~~^^^^^^^
ValueError: invalid literal for int() with base 10: '123/delete'
```

</details>

IMHO `url_for()` should raise an error if the returned URL isn’t going to be routed to the specified endpoint. In the example above, `url_for('user_by_id', id='current')` can’t return anything sensible, so it would be better to raise an error; `url_for('user_by_id', id='123/delete')` should error because `123/delete` doesn’t match the `string` converter.

(I was wondering if I should report this as a security vulnerability, but I don’t think it can cause issues on its own. However, in an already-vulnerable application – e.g. the sample application above where the “delete” endpoint doesn’t require POST and isn’t protected against CSRF etc. – I think this issue could increase the “blast radius” of a vulnerability, if you can trick the application into generating these inconsistent URLs.)

Environment:

- Python version: Python 3.14.2
- Flask version: Flask 3.1.2
- Werkzeug version: Werkzeug 3.1.5

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I don't know the original design choices for the URL building system. But my guess is that it was intended to do as little work as possible to get the right result in normal cases, since every view is likely to call `url_for`/`MapAdapter.build` many times, such as for a lot of CSS, JS, and image links in a template. The performance of building URLs actually came up years ago, and the result was assembling, with `ast` and `compile`, specific optimized functions for each rule.

This isn't a security issue, since I don't think `url_for` is intended to be passed untrusted/unfiltered user input. But if that's not the case for your project, and you need more validation, it's possible to do that by modifying `Map.converter`. You can remove converters you don't use, replace them with subclasses that do more in `to_url`, etc.

I'd guess that the `int` (and `float`) converter is calling `int` in order to support any type that implements `__int__` method, not necessarily to validate the value. The fact that it also results in validation when passing a string seems incidental.

The `any` converter also checks its value, but that's a simple `in set` test. It also appears to be subtly wrong, it should probably do `str(value) in self.values` rather than `value in self.values`.

All other converters only do the minimum to get the value to be a string. Many converters, including `int`, also take more arguments such as min length/value, but none are validating that.

Considering these points, especially performance, I'm not sure adding comprehensive validation is the right thing to do.

### Comment 2 ([user]):

The `app.url_for('user_by_id', id='123/delete')='http://localhost:5000/user/123/delete'` example is a result of how values are percent-encoded. `/` is a safe value in paths _in general_, so it's allowed by the base converter, which `UnicodeConverter` (`str`) inherits and doesn't override. It should probably be quoted in the base, and overridden by the `path` converter.

However, this is also another example where applying more processing _could_ be done, but isn't presumably for performance. `int`, `any`, `uuid`, etc. do not percent encode the string value they produce, since any valid value wouldn't need to be quoted. This seems like more evidence that the converters are not meant to do type checking and validation during building.

### Comment 3 ([user]):

> This isn't a security issue, since I don't think `url_for` is intended to be passed user input.

That’s surprising, I definitely do that sometimes (more or less indirectly and with more or less processing in between)… even the [Uploading Files](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/) example includes a call to `url_for('download_file', name=filename)`; `filename` has been made safe _as a file name_ via `secure_filename()`, but AFAICT there’s no suggestion that one might have to watch out for how it might interact with any other routes of the app.

### Comment 4 ([user]):

Another way to word what you're asking for, instead of validating values, is validating that `match(build(endpoint)) == endpoint`. Ultimately, you would _have_ to call match after build, because however much validation of the individual values you do, you could still end up with overlapping URLs. Your `path` converter for downloads is a good demonstration, because more specific  routes take higher matching priority. So if you want special handling for a certain file, you'd get unhelpful behavior from validation:

```python
url_map = Map([
    Rule("/static/<path:name>", endpoint="static"),
    Rule("/static/a/b/c", endpoint="static-abc"),
])
urls = url_map.bind("localhost")
print(urls.match("/static/d/e/f"))  # static, name=d/e/f
print(urls.match("/static/a/b/c"))  # static-abc
print(urls.match("/static/a/b/c/d"))  # static, name=a/b/c/d
```

### Comment 5 ([user]):

I'm fine with adding some more to the docs, if you're saying that the docs just didn't make it clear:

> Matching URLs validates the variable parts to be able to return a 404 for invalid URLs. On the other hand, building is mainly concerned with filling in the variable parts with whatever values you pass. Depending on the rules in your app, and what values you pass, the URL that's built may be be matched by a different rule or not match at all.
>
> For example... path example, int with min value example, etc

### Comment 6 ([user]):

> Another way to word what you're asking for, instead of validating values, is validating that `match(build(endpoint)) == endpoint`.

Yes, I think that’s what I expected. I guess the point about `/` not being valid in string params ended up being mostly a distraction from that.

If performance is a concern, I wonder if a separate function which includes this check would be an option… though I don’t like how this sounds usability-wise.

### Comment 7 ([user]):

I think this is too niche, and the solution too heavy, to include here. If you need that level of guarantee in your app, you can override the `Flask.url_for` method to do so, or use some other helper in cases where you need it:

```python
# when using Flask you could use req_ctx.url_adapter instead of passing an argument
def strict_url_for(urls: MapAdapter, endpoint: str, **values: Any) -> str:
    out = url_for(endpoint, **values)

    if urls.match(out)[0] != endpoint:
        raise ValueError("build didn't match the same endpoint")

    return out
```

You can also override converters to do more strict checks:

```python
url_map.converters["int"] = MyIntConverter
```

I'll update the docs to be more clear about URL building.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
