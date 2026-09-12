# GH909_pymc_7501: Fix latex rendering of variables with underscore in name — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/6508
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

_I apologize if this was an intended feature implemented to reflect the demand of the PyMC community. But when I migrate my codebase from PyMC3 to PyMC5, this seems more like a bug to me; it didn't raise an error in PyMC 3.8._

## Issue
When trying to display (not print) a PyMC model on Jupyter Notebook, I received a "KaTeX parse error". Apparently, this is due to the underscore character, `_`, in the name.

### Reproduceable code example:

```python
import pymc as pm
with pm.Model() as model:
    new_a = pm.Normal('new_a')
display(model) # on jupyter notebook
```


### Error message:

```shell
ParseError: KaTeX parse error: Expected 'EOF', got '_' at position 53: … \text{new_̲a} &\sim & \ope…
```


### PyMC version information:

`pip install pymc==5.0.2`

### Context for the issue:

Right now, I could bypass this error by adding a slash, `\_`, e.g. `new\_a` instead of `new_a`. But this is less desirable. For instance, I often have many variables that I would like to define. To do that, I would loop over some dictionary, and declare the variable one by one, while automatically assign them names that match the keys in the dictionary. However, with this "bug", I would either have to avoid using underscores at all or pre-process the names by replacing `_` with `\_`.

### More
Because of this parse error, I thought maybe I could write LaTeX syntax in my name field, or use raw string? But I don't think it works. Below are the things that I have tried:
- `pm.Normal(r'new_a')` - I though raw string would "protect" the underscore from getting parse error, but it still raises the same error.
- `pm.Normal('\alpha')` - Nope.
- `pm.Normal('\\alpha')` - Nope.
- `pm.Normal('$\alpha$')` - Nope.
- `pm.Normal('$\\alpha$')` - Nope.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Curious -- what IDE or environment are you using to work in jupyter notebooks?

I've noticed this problem as well, for a while, in VSCode. While Jupyter's environments (notebook and lab) for use MathJax for parsing equations, VSCode uses KaTeX. Turns out there's a difference in how the two backends parse stuff in  `\text{...}`.

See https://github.com/KaTeX/KaTeX/issues/1676 and https://github.com/mathjax/MathJax/issues/1770, both closed issues since each backend does it one way by design.

Also annoying:
```latex
$$
\begin{array}{rcl}
\text{new\_a} &\sim & \operatorname{N}(0,~1)
\end{array}
$$
```
Is a functioning workaround in KaTeX,
![image](https://user-images.githubusercontent.com/1542825/217992500-c317046c-b391-4f59-bdbe-5dfe6ec7e1a4.png)

But not in MathJax,
![image](https://user-images.githubusercontent.com/1542825/217992611-06bf5588-aaf4-4cf2-9dbb-c58259b78b9b.png)

What *does* seem to work for both backends in this case is to replace the `_` in `\text{...}` with `}\_\text{`.

### Comment 2 ([user]):

[user] Thanks for your reply. You are right, I was using Visual Studio Code.

Then it seems like PyMC5 is developed assuming a MathJax backend then.

Is there anything we, the PyMC side, could do about this? For example, detecting if it's KaTeX or MathJax.

### Comment 3 ([user]):

I believe we should be in the clear if we do a replacement as mentioned above--

If we encounter `_` within a \text command, end the \text command, drop in an escaped `_` outside of the \text, then start a new \text with the remaining string.

I'll give this a go soon. To be comprehensive it seems like we'll want to update a couple other cases too -- e.g. latex strings from potential/determinstics and Model names also

### Comment 4 ([user]):

Hey [user], are you still working on this issue? If not, I would like to give it a go if you don't mind.

### Comment 5 ([user]):

Thanks for asking! Sorry I haven't been around. Feel free to take this up, as I won't be able to prioritize it soon.

### Comment 6 ([user]):

For our example above, consider document `Hermione` with feature vector 
$$[1,0,0,1,1,0,1]$$ (the first column above).

Consider the *permutation* of the **feature indices** given by 
$$[3,1,0,6,2,5,4].$$

This says that feature 3 will be numbered 0, feature 1 still numbered 1, feature 0 numbered 2 and so on. Hence, the permutation will **reorder** document `Hermione` as
$$[\underline{1},0,1,1,0,0,1]$$
e.g. the underlined 1 at the new index **0**, corresponds to the original feature number 3. 

If we apply the permutation across all characters (columns), we get:


I GET THE FOLLOWING ERROR WHEN I RUN THE ABOVE CODE IN VSCODE IPNB VERSION 3.12.4 PYTHON

```
ParseError: KaTeX parse error: Can't use function "$' in math mode at position 16: 1,0,0,1,1,0,1]S$ (the first co...
```

## PR Review Comments

**[user]** on `pymc/printing.py`:

Does this work equivalently?
```
import re

def _format_underscore(variable: str) -> str:
    """
    Escapes all unescaped underscores in the variable name for LaTeX representation.
    """
    return re.sub(r'(?<!\\)_', r'\\_', variable)
```

**[user]** on `pymc/printing.py`:

Oh, that looks a lot better. Let me test it out.

**[user]** on `tests/test_printing.py`:

Instead of iterating through matches, directly assert that the LaTeX string contains only escaped underscores:
```
assert "\\_" in model_str
assert "_" not in model_str.replace("\\_", "")
```

**[user]** on `pymc/printing.py`:

Yup, that seems to work equivalently! I will replace the long function with this.

**[user]** on `tests/test_printing.py`:

Yes, I agree. That is a much cleaner way of doing it. I will make the change now.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
