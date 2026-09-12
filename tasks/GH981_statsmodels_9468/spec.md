# GH981_statsmodels_9468: BUG: svar, A,B dtype, one parameter score shape, closes #9302 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9302
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

I am trying to estimate a two equation SVAR model using statsmodels but I am facing an issue. For reference, I am using the following code where 'subset' is just a pandas dataframe with two columns (the two series for the variables of the system) and a time series index in datetime format. 

```
lags = 20
   
A = np.array([[1, 'E'], [0, 1]])  
   
A_guess = np.asarray([0.0002])

model = SVAR(subset, svar_type='A', A=A)

results = model.fit(A_guess = A_guess, maxlags=20, maxiter = 10000000, maxfun=1000000, solver='bfgs', trend="n")
```

Running the code I get the following error

```
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
File /Users/test/Desktop/anders_project/code/sql_server_retrieval.py:27
     24     model = SVAR(subset, svar_type='A', A=A)
     26     # Fit the model
---> 27     results = model.fit(maxlags=20, maxiter = 10000000, maxfun=1000000, solver='bfgs', trend="n")
     28     var_results[ticker] = results
     31 # # %% (C)(R) VAR model estimation -> apparently I cannot estimate without intercept so need to find an alternative; also, there seem to be data issues so i need to clean data/remove outliers first
     32
     33 # from statsmodels.tsa.vector_ar.var_model import VAR
   (...)
     66 #     print(f"Results for {ticker}:")
     67 #     result.summary()

File /Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/statsmodels/tsa/vector_ar/svar_model.py:180, in SVAR.fit(self, A_guess, B_guess, maxlags, method, ic, trend, verbose, s_method, solver, override, maxiter, maxfun)
    177 # initialize starting parameters
    178 start_params = self._get_init_params(A_guess, B_guess)
--> 180 return self._estimate_svar(start_params, lags, trend=trend,
    181                            solver=solver, override=override,
    182                            maxiter=maxiter, maxfun=maxfun)

File /Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/statsmodels/tsa/vector_ar/svar_model.py:248, in SVAR._estimate_svar(self, start_params, lags, maxiter, maxfun, trend, solver, override)
    245 omega = sse / df_resid
    246 self.sigma_u = omega
--> 248 A, B = self._solve_AB(start_params, override=override,
...
--> 279     A[A_mask] = params[:A_len]
    280 if B is not None:
    281     B[B_mask] = params[A_len:A_len+B_len]

TypeError: NumPy boolean array indexing assignment requires a 0 or 1-dimensional input, input has 2 dimensions
```

I talked to josefpktd in the Google group and he had a quick look at the issue. He found that this most likely is a bug as numpy got more strict with shape mismatch in masked assignments which seems to cause the issue. He told me to report the issue here which I am doing with this report. He is a link [link](https://groups.google.com/g/pystatsmodels/c/uRzZMF-OLP8) to what he said exactly for reference.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

see also another example in #9436 that breaks because no parameters are to be estimated in A, B

### Comment 2 ([user]):

I managed to get it to work

mask work fine with numpy if dtype of A and B is "U"

however, params is 3dim, and I have not figured out why
fixing the symptoms instead of source:

add this to several methods
```
        if params.ndim > 1:
            params = params.ravel()
```


result for similar example
summary requires patching k_exog_user

However, it looks like we don't have A, B parameters in summary and no inference, cov_params for them

```
results.A, results.B
(array([[1.        , 0.03613134],
        [0.        , 1.        ]]),
 array([[1., 0.],
        [0., 1.]]))
```


```
k=2
model = SVAR(y[:, :k], svar_type="AB", A=A, B=B)
model.k_exog_user = 0
results = model.fit(maxlags=lags)
results.k_exog_user = 0
results.summary()
  Summary of Regression Results   
==================================
Model:                        SVAR
Method:                        OLS
Date:           Sun, 24, Nov, 2024
Time:                     14:24:18
--------------------------------------------------------------------
No. of Equations:         2.00000    BIC:                  0.0998087
Nobs:                     198.000    HQIC:               0.000955839
Log likelihood:          -545.339    FPE:                   0.935903
AIC:                   -0.0662654    Det(Omega_mle):        0.890367
--------------------------------------------------------------------
Results for equation y1
========================================================================
           coefficient       std. error           t-stat            prob
------------------------------------------------------------------------
const        -0.049756         0.070477           -0.706           0.480
L1.y1         0.355000         0.071535            4.963           0.000
L1.y2         0.076060         0.064452            1.180           0.238
L2.y1        -0.081373         0.071915           -1.132           0.258
L2.y2        -0.068970         0.064102           -1.076           0.282
========================================================================

Results for equation y2
========================================================================
           coefficient       std. error           t-stat            prob
------------------------------------------------------------------------
const        -0.223188         0.074249           -3.006           0.003
L1.y1         0.156949         0.075363            2.083           0.037
L1.y2         0.575030         0.067901            8.469           0.000
L2.y1        -0.086858         0.075764           -1.146           0.252
L2.y2        -0.332960         0.067532           -4.930           0.000
========================================================================

Correlation matrix of residuals
            y1        y2
y1    1.000000 -0.038065
y2   -0.038065  1.000000
```

### Comment 3 ([user]):

What are the params in SVARResults?

skimming the code it looks like those are just the var parameters
default svar_ma_rep  uses p = Ainv * B

i.e. I guess reduced form lag representation should pre-multiply var system by Ainv.

### Comment 4 ([user]):

There is something wrong with "bfgs".

Digging in with pdb, it looks like extra dimension to `params` are added during bfgs optimization.
I have no idea yet why and where (statsmodels or scipy?)
"newton" also fails. So there could be a problem in `score` or `hessian`, which both use numdiff.
(But, AFAIR, both bfgs and lbfgs use score only.)

"nm" and "lbfgs" seems to work fine  (I only partially removed my workaround `ravel`.)


**update**
SVAR,score return 2dim gradient.
If I ravel it to return 1dim gradient, then bfgs works. "newdon" also works now with 1dim score.
So, it could be that "bfgs" gets messed up by 2dim gradient, while "lbfgs" does not.

Maybe something changed in numdiff approx_fprime in this case.
IIRC, I added vectorization if there is only one param.

possible change in #8780

comments for problem and change with 1 param starts around here
(withheld: the upstream fix is not part of the task)#issuecomment-1505709618

### Comment 5 ([user]):

conclusion:

it looks like only two changes are needed:

- force dtype of A and B to be "U" (to force elementwise comparison in numpy)
- change score to return 1dim

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
