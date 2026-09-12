# GH891_statsmodels_9487: BUG/ENH: Tukeyhsd, fix unused variance, add Games-Howell  — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9175
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

- [x] tests added / passed. 
- [x] code/documentation is well formatted.  
- [x] properly formatted commit message. See 
      [NumPy's guide](https://docs.scipy.org/doc/numpy-1.15.1/dev/gitwash/development_workflow.html#writing-the-commit-message). 

<details>

like tests in try_tukey_hsd.py
With the first dataset, results should be the same, as below.

![image](https://github.com/statsmodels/statsmodels/assets/56634448/9b070938-dac8-4e8a-ac5e-eef711c00477)


</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Great, thanks for finding this mistake.

Do you have an example that uses this code path?
I don't remember now where this is used, and it does not have unit test coverage

### Comment 2 ([user]):

Hello [user]! Thanks for updating this PR. We checked the lines you've touched for [PEP 8](https://www.python.org/dev/peps/pep-0008) issues, and found:







There are currently no PEP 8 issues detected in this Pull Request. Cheers! :beers: 

##### Comment last updated at 2024-04-07 02:49:39 UTC

### Comment 3 ([user]):

> Great, thanks for finding this mistake.
> 
> Do you have an example that uses this code path? I don't remember now where this is used, and it does not have unit test coverage

add a unit test in examples/try_tukey_hsd.py, is it ok?

### Comment 4 ([user]):

No, unit tests need to go into a module that starts with tests

The most appropriate test file for Games-Howell unit test is `"statsmodels\statsmodels\stats\tests\test_pairwise.py"`

Also, the unit test need to go into a function with name starting with "test", see the other cases

The example files like `examples/try_tukey_hsd.py` were experimental and illustrative script files before the use of notebooks. We do not add those anymore.
Full examples go into docs notebooks.

If Games-Howell test verifies now against R, then we can add it to the official docs. I will look at that at the end of this PR.

If I understand correctly, then related PR and issue are #7332 and #8396

### Comment 5 ([user]):

> No, unit tests need to go into a module that starts with tests
> 
> The most appropriate test file for Games-Howell unit test is `"statsmodels\statsmodels\stats\tests\test_pairwise.py"`
> 
> Also, the unit test need to go into a function with name starting with "test", see the other cases
> 
> The example files like `examples/try_tukey_hsd.py` were experimental and illustrative script files before the use of notebooks. We do not add those anymore. Full examples go into docs notebooks.
> 
> If Games-Howell test verifies now against R, then we can add it to the official docs. I will look at that at the end of this PR.
> 
> If I understand correctly, then related PR and issue are #7332 and #8396

thanks a lot, added the unit test in test_pairwise.py

### Comment 6 ([user]):

[user] Could you please review it? All checks have passed

### Comment 7 ([user]):

Thanks

Looks good to me, but I want to go over some details in the related code.
I'm taking a break from `robust` and will go over it within a few days.

### Comment 8 ([user]):

many packages seems to have games-howell, tamhane t2 and dunnet t3 as options for unequal nobs/variance.

need future proof keywords when we add the other two.

Also, we eventually need an option to use standard p-value correction method, instead of hardcoded tukey hsd p-value distribution.

### Comment 9 ([user]):

PMCMRplus gives the same results for p-values but with more digits

```
> res = gamesHowellTest(d[4:29,]$StressReduction, as.factor(d[4:29,]$Treatment))
> summary(res)

        Pairwise comparisons using Games-Howell test

data: d[4:29, ]$StressReduction and as.factor(d[4:29, ]$Treatment)
alternative hypothesis: two.sided
P value adjustment method: none
H0
                        q value         Pr(>|q|)    
mental - medical == 0     7.859 0.00019641028219 ***
physical - medical == 0   2.536 0.20585647592932    
physical - mental == 0   -2.979 0.12691156834160    
---
Signif. codes: 0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1
```

### Comment 10 ([user]):

[user] Thanks again for the PR

merged in #9487
The main addition was to fix the plot_simultaneous method in the unequal var case

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
