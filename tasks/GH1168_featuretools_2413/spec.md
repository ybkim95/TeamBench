# GH1168_featuretools_2413: Fix backtracking in NumberOfWordsInQuotes primitive — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2411
- Repo: https://github.com/alteryx/featuretools

## Issue Description

NumberOfWordsInQuotes completely freezes up on this dataset 
[twitter_training.csv](https://github.com/alteryx/featuretools/files/10252617/twitter_training.csv)

```python
import featuretools as ft
from featuretools.primitives import NumberOfWordsInQuotes
df = pd.read_csv("./twitter_training.csv")
es = ft.EntitySet()
es.add_dataframe(
    dataframe=df,
    dataframe_name="df",
    index="id",
    make_index=True,
)

prim_instance = NumberOfWordsInQuotes()
get_fun = prim_instance.get_function()
answer = get_fun(es["df"]["text"])
```

## PR Review Comments

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py`:

Can we add this string to other NaturalLauguage primitive tests?

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py`:

We could, but I am concerned that what made this string an edge case for this primitive, may not make it an edge case for others. I think one possible longterm solution would be to have a single corpus (something like the twitter dataset), that we run all our applicable NLP primitives on. This would be a test not for correctness (which the individual test files could check) but that the primitives avoid failure. Basically programmatically doing what [user] did when he ran the tests for recommended primitives. We can exclude the tests from our regular test suite if efficiency is a concern.

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py`:

How about making a test that imports all NatLang primitives and runs them on a fixture of strings we think the primitives could possibly hang or fail on (like all whitespace, or this string)? Anytime we encounter an edge-case string that triggers an error, we could add it to the fixture. This would give us the confidence that the primitives won't hang, and would also give us a living history of strings that have caused failures before. It would also be a line of defense in the future, in case we implement a primitive and forget to check a particular edge case.


[user] [user]

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py`:

Sorry if this is kind of confusing, I can put up a POC in a different PR

**[user]** on `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py`:

That sounds like a good idea and what I had in mind.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
