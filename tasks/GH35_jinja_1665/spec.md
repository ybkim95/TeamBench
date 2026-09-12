# GH35_jinja_1665: Fix bug involving calling set on a template parameter within all branches of an if block — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/jinja/issues/1253
- Repo: https://github.com/pallets/jinja

## Issue Description

I have the following **Jinja** template:

```jinja
{% if new_data_set_created is defined %}
    {% if new_data_set_created == True %}
        The new image data set <strong>{{ form_data["data_set_name"] }}</strong> has been created.
        {% set form_data = {"data_set_name": "", "client": "", "project": ""} %}
    {% else %}
        The new image data set <strong>{{ form_data["data_set_name"] }}</strong> could not be created.<br />
    {% endif %}
{% elif deleted_data_set is defined %}
    The image data set <strong>{{ deleted_data_set }}</strong> has been deleted from DB and from disk.
    {% set form_data = {"data_set_name": "", "client": "", "project": ""} %}
{% else %}
    {% set form_data = {"data_set_name": "", "client": "", "project": ""} %}
{% endif %}
```

However, when rendering this template via **Flask** I get the error message that `form_data` in line 3 of this code section is undefined (which is not the case, I double-checked that):

    jinja2.exceptions.UndefinedError: 'form_data' is undefined

Now when I remove the `elif` block from that code section above (i.e. lines 8-10) then the very same template does work again and line 3 does not lead to an error any more.

I am calling this template like so:

```python
return render_template(
    "image-data-sets.html",
    new_data_set_created=True,
    form_data=request.form,
    data_sets=ImageDataSet.query.all(),
    clients=clients,
)
```

I double-checked that `request.form` (and thus `form_data` within the template) is not `None`. And as said, I don't make any changes to this call, I just remove those lines from the template and then it's working.

So my question: Why does removing the `elif` block fix this issue, and why is this error raised in the first place? What's wrong with my `if-elif-else-endif` block? Is this a bug or am I missing something?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I was able to reproduce the issue as it is described. I did some research on this, however, wasn't able to find the cause.

### Comment 2 ([user]):

The use of `set` here is unnecessary if not incorrect, but I'm not sure if that's causing the issue. Would need to dump the compiled code to see what's being generated and see if that reveals anything. Otherwise step through the frames to see what's defined at that point in the execution.

### Comment 3 ([user]):

> The use of `set` here is unnecessary if not incorrect, but I'm not sure if that's causing the issue. Would need to dump the compiled code to see what's being generated and see if that reveals anything. Otherwise step through the frames to see what's defined at that point in the execution.

`set` is, indeed, causing the issue I think. When I commented out the first `set` on line 4, everything works fine. However, when I executed the `elif` block and printed out `data_form["data_set_name"]`, the `set` within `elif` didn't cause any issues.  

UPDATE: Just traced through the code, trying to update the `data_form` dict is what is causing the issue on line 4. When `set` command is executed, this is what I got in my debugger: `form_data: missing`. If I am not mistaken, that's why it is giving the `Undefined` error.

### Comment 4 ([user]):

An initial guess it that setting a name that's passed in to the render context is not intended to be supported, and there's something going on with that in the runtime. So we need to identify the code that's handling that and then decide whether to change it or raise a better error.

## PR Review Comments

**[user]** on `src/jinja2/idtracking.py`:

I _think_ I understand what's happening here, but could you add some comments explaining it? I think it's doing "combine the definitions across branches, then remove any that are defined in this scope already", is that right? I'm also not sure why combining them all instead of counting them works, what was wrong about the previous code?

**[user]** on `tests/test_regression.py`:

This should probably output `{{ a }}` after the `{% endif %}` and test that both the before and after are what we expect.

**[user]** on `src/jinja2/idtracking.py`:

The previous code had a special case (the `if branch_count` that was removed below) that basically said "if this symbol is stored (using `{ %set %}`) in all branches, then don't load it into this context" which was a bad assumption because that symbol being set is not always local to the context. Since we don't make use of reference counting anywhere else, I removed the reference counting code (which is why we don't need a dictionary mapping symbols to their usage).

**[user]** on `src/jinja2/idtracking.py`:

The change from checking `if target in self.stores: continue` to using `difference_update` on two sets performs roughly the same goal: Making sure we don't override the loading behaviour of a symbol already defined in this context.

**[user]** on `src/jinja2/idtracking.py`:

We no longer need the `type: ignore` here because `name` can be properly inferred as a `str` instead of as a key type within the dictionary.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
