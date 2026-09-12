# GH1128_FLAML_1475: Fix: Preserve FLAML_sample_size in best_config_per_estimator — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1318
- Repo: https://github.com/microsoft/FLAML

## Issue Description

in automl.py
 from flaml import AutoML
        automl = AutoML()
        X_train, y_train = Mydata
        automl.fit(X_train, y_train)
        starting_points = automl.best_config_per_estimator

        new_automl = AutoML()
        new_automl.fit(X_train, y_train, starting_points=starting_points)
Using this snippet, I get the same answer using my starting_points with my optimized params , that is it uses the internal default and starts retraining from scratch . My optimizized params are not being used. Looking at automl.py I cannot find any code that would incorporate  starting_points  params into the estimater

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi,
Check whether you are using the latest FLAML version and verify that `starting_points` is correctly formatted and supported; if issues persist, it may be something worth fixing.

### Comment 2 ([user]):

It is formatted as described  in the python file I mentioned. It is the
version of FLAML on github.The problem is the program does not reset the
starting hyperparams to those in the starting_points file. It just uses the
default in DATA.

On Sat, Jul 20, 2024 at 10:30 AM Ranuga ***@***.***> wrote:

> Hi,
> Check whether you are using the latest FLAML version and verify that
> starting_points is correctly formatted and supported; if issues persist,
> it may be something worth fixing.
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/microsoft/FLAML/issues/1318#issuecomment-2241169388>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/BDFVJGBG3XLGQYXC3QHFWW3ZNJYBVAVCNFSM6AAAAABK7TCEVSVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDENBRGE3DSMZYHA>
> .
> You are receiving this because you authored the thread.Message ID:
> ***@***.***>
>

### Comment 3 ([user]):

Hi [user] , thank you very much for your feedback. Could you please provide a complete code snippet for reproducing the issue?

### Comment 4 ([user]):

from automi.py
 starting_points: A dictionary or a str to specify the starting
hyperparameter
                config for the estimators | default="static".
                If str:
                    - if "data", use data-dependent defaults;
                    - if "data:path" use data-dependent defaults which are
stored at path;
                    - if "static", use data-independent defaults.
                If dict, keys are the name of the estimators, and values
are the starting
                hyperparameter configurations for the corresponding
estimators.
                The value can be a single hyperparameter configuration dict
or a list
                of hyperparameter configuration dicts.
                In the following code example, we get starting_points from
the
                `automl` object and use them in the `new_automl` object.
                e.g.,

        ```python
        from flaml import AutoML
        automl = AutoML()
        X_train, y_train = load_iris(return_X_y=True)
        automl.fit(X_train, y_train)
        starting_points = automl.best_config_per_estimator

        new_automl = AutoML()
        new_automl.fit(X_train, y_train,
starting_points=starting_points)This fails it does not use staring points
        ```

On Tue, Aug 6, 2024 at 10:43 PM Li Jiang ***@***.***> wrote:

> Hi [user] <https://github.com/[user]> , thank you very much for your
> feedback. Could you please provide a complete code snippet for reproducing
> the issue?
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/microsoft/FLAML/issues/1318#issuecomment-2272511045>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/BDFVJGHFA2WD5NHZJVTTLE3ZQGCW7AVCNFSM6AAAAABK7TCEVSVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDENZSGUYTCMBUGU>
> .
> You are receiving this because you were mentioned.Message ID:
> ***@***.***>
>

### Comment 5 ([user]):

> from automi.py starting_points: A dictionary or a str to specify the starting hyperparameter config for the estimators | default="static". If str: - if "data", use data-dependent defaults; - if "data:path" use data-dependent defaults which are stored at path; - if "static", use data-independent defaults. If dict, keys are the name of the estimators, and values are the starting hyperparameter configurations for the corresponding estimators. The value can be a single hyperparameter configuration dict or a list of hyperparameter configuration dicts. In the following code example, we get starting_points from the `automl` object and use them in the `new_automl` object. e.g., ```python from flaml import AutoML automl = AutoML() X_train, y_train = load_iris(return_X_y=True) automl.fit(X_train, y_train) starting_points = automl.best_config_per_estimator new_automl = AutoML() new_automl.fit(X_train, y_train, starting_points=starting_points)This fails it does not use staring points ```
> […](#)
> On Tue, Aug 6, 2024 at 10:43 PM Li Jiang ***@***.***> wrote: Hi [user] <https://github.com/[user]> , thank you very much for your feedback. Could you please provide a complete code snippet for reproducing the issue? — Reply to this email directly, view it on GitHub <[#1318 (comment)](https://github.com/microsoft/FLAML/issues/1318#issuecomment-2272511045)>, or unsubscribe <https://github.com/notifications/unsubscribe-auth/BDFVJGHFA2WD5NHZJVTTLE3ZQGCW7AVCNFSM6AAAAABK7TCEVSVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDENZSGUYTCMBUGU> . You are receiving this because you were mentioned.Message ID: ***@***.***>


Hi [user] , check this:

```python
from flaml import AutoML
from sklearn.datasets import load_iris
import numpy as np

def test_fit_w_starting_point(as_frame=True, n_concurrent_trials=1):
    automl = AutoML()
    settings = {
        "max_iter": 3,
        "metric": "accuracy",
        "task": "classification",
        "log_training_metric": True,
        "n_jobs": 1,
        "model_history": True,
    }
    X_train, y_train = load_iris(return_X_y=True, as_frame=as_frame)
    if as_frame:
        # test drop column
        X_train.columns = range(X_train.shape[1])
        X_train[X_train.shape[1]] = np.zeros(len(y_train))
    automl.fit(X_train=X_train, y_train=y_train, n_concurrent_trials=n_concurrent_trials, **settings)
    automl_val_accuracy = 1.0 - automl.best_loss
    print("Best ML leaner:", automl.best_estimator)
    print("Best hyperparmeter config:", automl.best_config)
    print("Best accuracy on validation data: {0:.4g}".format(automl_val_accuracy))
    print("Training duration of best run: {0:.4g} s".format(automl.best_config_train_time))

    starting_points = automl.best_config_per_estimator
    print("starting_points", starting_points)
    print("loss of the starting_points", automl.best_loss_per_estimator)
    settings_resume = {
        "max_iter": 3,
        "metric": "accuracy",
        "task": "classification",
        "log_training_metric": True,
        "n_jobs": 1,
        "model_history": True,
        "log_type": "all",
        "starting_points": starting_points,
        "verbose": 5,
    }
    new_automl = AutoML()
    new_automl.fit(X_train=X_train, y_train=y_train, **settings_resume)

    new_automl_val_accuracy = 1.0 - new_automl.best_loss
    print("Best ML leaner:", new_automl.best_estimator)
    print("Best hyperparmeter config:", new_automl.best_config)
    print("Best accuracy on validation data: {0:.4g}".format(new_automl_val_accuracy))
    print("Training duration of best run: {0:.4g} s".format(new_automl.best_config_train_time))

test_fit_w_starting_point()
```

And the outputs:
```
[flaml.automl.logger: 08-09 02:30:10] {1751} INFO - task = classification
[flaml.automl.logger: 08-09 02:30:10] {1762} INFO - Evaluation method: cv
[flaml.automl.logger: 08-09 02:30:10] {1865} INFO - Minimizing error metric: 1-accuracy
[flaml.automl.logger: 08-09 02:30:10] {1982} INFO - List of ML learners in AutoML Run: ['lgbm', 'rf', 'xgboost', 'extra_tree', 'xgb_limitdepth', 'sgd', 'catboost', 'lrl1']
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 0, current learner lgbm
[flaml.automl.logger: 08-09 02:30:10] {2427} INFO - Estimated sufficient time budget=10000s. Estimated necessary time budget=10s.
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.0s,	estimator lgbm's best error=0.0733,	best estimator lgbm's best error=0.0733
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 1, current learner lgbm
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.1s,	estimator lgbm's best error=0.0733,	best estimator lgbm's best error=0.0733
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 2, current learner lgbm
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.1s,	estimator lgbm's best error=0.0533,	best estimator lgbm's best error=0.0533
[flaml.automl.logger: 08-09 02:30:10] {2719} INFO - retrain lgbm for 0.0s
[flaml.automl.logger: 08-09 02:30:10] {2722} INFO - retrained model: LGBMClassifier(learning_rate=0.26770501231052046, max_bin=127,
               min_child_samples=12, n_estimators=1, n_jobs=1, num_leaves=4,
               reg_alpha=0.001348364934537134, reg_lambda=1.4442580148221913,
               verbose=-1)
[flaml.automl.logger: 08-09 02:30:10] {2018} INFO - fit succeeded
[flaml.automl.logger: 08-09 02:30:10] {2019} INFO - Time taken to find the best model: 0.0877523422241211
Best ML leaner: lgbm
Best hyperparmeter config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 12, 'learning_rate': 0.26770501231052046, 'log_max_bin': 7, 'colsample_bytree': 1.0, 'reg_alpha': 0.001348364934537134, 'reg_lambda': 1.4442580148221913}
Best accuracy on validation data: 0.9467
Training duration of best run: 0.002497 s
starting_points {'lgbm': {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 12, 'learning_rate': 0.26770501231052046, 'log_max_bin': 7, 'colsample_bytree': 1.0, 'reg_alpha': 0.001348364934537134, 'reg_lambda': 1.4442580148221913}, 'rf': None, 'xgboost': None, 'extra_tree': None, 'xgb_limitdepth': None, 'sgd': None, 'catboost': None, 'lrl1': None}
loss of the starting_points {'lgbm': 0.05333333333333332, 'rf': inf, 'xgboost': inf, 'extra_tree': inf, 'xgb_limitdepth': inf, 'sgd': inf, 'catboost': inf, 'lrl1': inf}
[flaml.automl.logger: 08-09 02:30:10] {1751} INFO - task = classification
[flaml.automl.logger: 08-09 02:30:10] {1762} INFO - Evaluation method: cv
[flaml.automl.logger: 08-09 02:30:10] {1865} INFO - Minimizing error metric: 1-accuracy
[flaml.automl.logger: 08-09 02:30:10] {1982} INFO - List of ML learners in AutoML Run: ['lgbm', 'rf', 'xgboost', 'extra_tree', 'xgb_limitdepth', 'sgd', 'catboost', 'lrl1']
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 0, current learner lgbm
[flaml.tune.tune: 08-09 02:30:10] {905} INFO - trial 1 config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 12, 'learning_rate': 0.2677050123105203, 'log_max_bin': 7, 'colsample_bytree': 1.0, 'reg_alpha': 0.001348364934537134, 'reg_lambda': 1.4442580148221913}
[flaml.automl.logger: 08-09 02:30:10] {2427} INFO - Estimated sufficient time budget=10000s. Estimated necessary time budget=10s.
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.0s,	estimator lgbm's best error=0.0533,	best estimator lgbm's best error=0.0533
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 1, current learner lgbm
[flaml.tune.tune: 08-09 02:30:10] {905} INFO - trial 1 config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 20, 'learning_rate': 0.09999999999999987, 'log_max_bin': 8, 'colsample_bytree': 0.8085131463835397, 'reg_alpha': 0.0009765625, 'reg_lambda': 0.9999999999999992}
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.1s,	estimator lgbm's best error=0.0533,	best estimator lgbm's best error=0.0533
[flaml.automl.logger: 08-09 02:30:10] {2292} INFO - iteration 2, current learner lgbm
[flaml.tune.tune: 08-09 02:30:10] {905} INFO - trial 1 config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 7, 'learning_rate': 0.716659736161759, 'log_max_bin': 6, 'colsample_bytree': 1.0, 'reg_alpha': 0.0018617221086098734, 'reg_lambda': 2.0858812133781366}
[flaml.automl.logger: 08-09 02:30:10] {2476} INFO -  at 0.1s,	estimator lgbm's best error=0.0400,	best estimator lgbm's best error=0.0400
[flaml.automl.logger: 08-09 02:30:10] {2719} INFO - retrain lgbm for 0.0s
[flaml.automl.logger: 08-09 02:30:10] {2722} INFO - retrained model: LGBMClassifier(learning_rate=0.716659736161759, max_bin=63, min_child_samples=7,
               n_estimators=1, n_jobs=1, num_leaves=4,
               reg_alpha=0.0018617221086098734, reg_lambda=2.0858812133781366,
               verbose=-1)
[flaml.automl.logger: 08-09 02:30:10] {2018} INFO - fit succeeded
[flaml.automl.logger: 08-09 02:30:10] {2019} INFO - Time taken to find the best model: 0.08789968490600586
Best ML leaner: lgbm
Best hyperparmeter config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 7, 'learning_rate': 0.716659736161759, 'log_max_bin': 6, 'colsample_bytree': 1.0, 'reg_alpha': 0.0018617221086098734, 'reg_lambda': 2.0858812133781366}
Best accuracy on validation data: 0.96
Training duration of best run: 0.002469 s
```

The trial 1 config `trial 1 config: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 12, 'learning_rate': 0.2677050123105203, 'log_max_bin': 7, 'colsample_bytree': 1.0, 'reg_alpha': 0.001348364934537134, 'reg_lambda': 1.4442580148221913}` is exactly the same as the starting_points `starting_points {'lgbm': {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 12, 'learning_rate': 0.26770501231052046, 'log_max_bin': 7, 'colsample_bytree': 1.0, 'reg_alpha': 0.001348364934537134, 'reg_lambda': 1.4442580148221913}, 'rf': None, 'xgboost': None, 'extra_tree': None, 'xgb_limitdepth': None, 'sgd': None, 'catboost': None, 'lrl1': None}
loss of the starting_points {'lgbm': 0.05333333333333332, 'rf': inf, 'xgboost': inf, 'extra_tree': inf, 'xgb_limitdepth': inf, 'sgd': inf, 'catboost': inf, 'lrl1': inf}
`

### Comment 6 ([user]):

A simpler code that recreate this issue -

```
import numpy as np
from flaml import AutoML
from sklearn.datasets import load_iris

N = 10000
X_train, y_train = load_iris(return_X_y=True)
X_train = np.concatenate([X_train+0.1*i for i in range(N)], axis=0)
y_train = np.concatenate([y_train]*N, axis=0)

am1 = AutoML()
am1.fit(X_train, y_train, estimator_list=['lgbm'], time_budget=60, seed=11)

am2 = AutoML()
am2.fit(X_train, y_train, estimator_list=['lgbm'], time_budget=30, seed=11, starting_points=am1.best_config_per_estimator)

print(f"am1.best_loss: {am1.best_loss:.4f}")
print(f"am2.best_loss: {am2.best_loss:.4f}")
```

Note that on smaller N (say 10) this is not reproduced.

### Comment 7 ([user]):

Hi [user] , check this:

```python
import numpy as np
from flaml import AutoML
from sklearn.datasets import load_iris

N = 10
X_train, y_train = load_iris(return_X_y=True)
X_train = np.concatenate([X_train+0.1*i for i in range(N)], axis=0)
y_train = np.concatenate([y_train]*N, axis=0)

am1 = AutoML()
am1.fit(X_train, y_train, estimator_list=['lgbm'], time_budget=3, seed=11)

am2 = AutoML()
am2.fit(X_train, y_train, estimator_list=['lgbm'], time_budget=3, seed=11, starting_points=am1.best_config_per_estimator, verbose=5)

print(f"am1.best_loss: {am1.best_loss:.4f}")
print(f"am2.best_loss: {am2.best_loss:.4f}")
```

The output:
```
[flaml.automl.logger: 08-23 00:39:37] {1728} INFO - task = classification
[flaml.automl.logger: 08-23 00:39:37] {1739} INFO - Evaluation method: cv
[flaml.automl.logger: 08-23 00:39:37] {1838} INFO - Minimizing error metric: log_loss
[flaml.automl.logger: 08-23 00:39:37] {1955} INFO - List of ML learners in AutoML Run: ['lgbm']
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 0, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2393} INFO - Estimated sufficient time budget=574s. Estimated necessary time budget=1s.
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.1s,	estimator lgbm's best error=0.6502,	best estimator lgbm's best error=0.6502
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 1, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.1s,	estimator lgbm's best error=0.6502,	best estimator lgbm's best error=0.6502
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 2, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.2s,	estimator lgbm's best error=0.2277,	best estimator lgbm's best error=0.2277
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 3, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.3s,	estimator lgbm's best error=0.1464,	best estimator lgbm's best error=0.1464
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 4, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.4s,	estimator lgbm's best error=0.1464,	best estimator lgbm's best error=0.1464
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 5, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.5s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 6, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.5s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 7, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.6s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 8, current learner lgbm
[flaml.automl.logger: 08-23 00:39:37] {2442} INFO -  at 0.8s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:37] {2258} INFO - iteration 9, current learner lgbm
[flaml.automl.logger: 08-23 00:39:38] {2442} INFO -  at 0.9s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:38] {2258} INFO - iteration 10, current learner lgbm
[flaml.automl.logger: 08-23 00:39:38] {2442} INFO -  at 1.0s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:38] {2258} INFO - iteration 11, current learner lgbm
[flaml.automl.logger: 08-23 00:39:38] {2442} INFO -  at 1.0s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:38] {2258} INFO - iteration 12, current learner lgbm
[flaml.automl.logger: 08-23 00:39:38] {2442} INFO -  at 1.3s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:38] {2258} INFO - iteration 13, current learner lgbm
[flaml.automl.logger: 08-23 00:39:38] {2442} INFO -  at 1.5s,	estimator lgbm's best error=0.0995,	best estimator lgbm's best error=0.0995
[flaml.automl.logger: 08-23 00:39:38] {2258} INFO - iteration 14, current learner lgbm
[flaml.automl.logger: 08-23 00:39:39] {2442} INFO -  at 2.0s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:39] {2258} INFO - iteration 15, current learner lgbm
[flaml.automl.logger: 08-23 00:39:39] {2442} INFO -  at 2.2s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:39] {2258} INFO - iteration 16, current learner lgbm
[flaml.automl.logger: 08-23 00:39:40] {2442} INFO -  at 2.9s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:40] {2685} INFO - retrain lgbm for 0.0s
[flaml.automl.logger: 08-23 00:39:40] {2688} INFO - retrained model: LGBMClassifier(colsample_bytree=0.7854369023412479,
               learning_rate=0.6681452089267123, max_bin=1023,
               min_child_samples=8, n_estimators=1, n_jobs=-1, num_leaves=9,
               reg_alpha=0.0046680380940597324, reg_lambda=2.7127484555926396,
               verbose=-1)
[flaml.automl.logger: 08-23 00:39:40] {1985} INFO - fit succeeded
[flaml.automl.logger: 08-23 00:39:40] {1986} INFO - Time taken to find the best model: 1.9591500759124756
[flaml.automl.logger: 08-23 00:39:40] {1728} INFO - task = classification
[flaml.automl.logger: 08-23 00:39:40] {1739} INFO - Evaluation method: cv
[flaml.automl.logger: 08-23 00:39:40] {1838} INFO - Minimizing error metric: log_loss
[flaml.automl.logger: 08-23 00:39:40] {1955} INFO - List of ML learners in AutoML Run: ['lgbm']
[flaml.automl.logger: 08-23 00:39:40] {2258} INFO - iteration 0, current learner lgbm
[flaml.tune.tune: 08-23 00:39:40] {874} INFO - trial 1 config: {'n_estimators': 28, 'num_leaves': 9, 'min_child_samples': 8, 'learning_rate': 0.6681452089267123, 'log_max_bin': 10, 'colsample_bytree': 0.7854369023412479, 'reg_alpha': 0.0046680380940597324, 'reg_lambda': 2.7127484555926396}
[flaml.automl.logger: 08-23 00:39:40] {2393} INFO - Estimated sufficient time budget=2966s. Estimated necessary time budget=3s.
[flaml.automl.logger: 08-23 00:39:40] {2442} INFO -  at 0.3s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:40] {2258} INFO - iteration 1, current learner lgbm
[flaml.tune.tune: 08-23 00:39:40] {874} INFO - trial 1 config: {'n_estimators': 38, 'num_leaves': 6, 'min_child_samples': 9, 'learning_rate': 0.1820529479425827, 'log_max_bin': 10, 'colsample_bytree': 0.6178595690062099, 'reg_alpha': 0.004704775942800625, 'reg_lambda': 2.2572219466809567}
[flaml.automl.logger: 08-23 00:39:40] {2442} INFO -  at 0.5s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:40] {2258} INFO - iteration 2, current learner lgbm
[flaml.tune.tune: 08-23 00:39:40] {874} INFO - trial 1 config: {'n_estimators': 21, 'num_leaves': 14, 'min_child_samples': 7, 'learning_rate': 1.0, 'log_max_bin': 9, 'colsample_bytree': 0.953014235676286, 'reg_alpha': 0.004631587117541134, 'reg_lambda': 3.2602040725950805}
[flaml.automl.logger: 08-23 00:39:41] {2442} INFO -  at 1.1s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:41] {2258} INFO - iteration 3, current learner lgbm
[flaml.tune.tune: 08-23 00:39:41] {874} INFO - trial 1 config: {'n_estimators': 19, 'num_leaves': 33, 'min_child_samples': 7, 'learning_rate': 0.8560177007610394, 'log_max_bin': 10, 'colsample_bytree': 0.6944120472750334, 'reg_alpha': 0.01908241965223944, 'reg_lambda': 2.3865208114810255}
[flaml.automl.logger: 08-23 00:39:42] {2442} INFO -  at 1.9s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:42] {2258} INFO - iteration 4, current learner lgbm
[flaml.tune.tune: 08-23 00:39:42] {874} INFO - trial 1 config: {'n_estimators': 40, 'num_leaves': 4, 'min_child_samples': 10, 'learning_rate': 0.5215055948198659, 'log_max_bin': 9, 'colsample_bytree': 0.8764617574074625, 'reg_alpha': 0.0011419191090389612, 'reg_lambda': 3.0835700857573514}
[flaml.automl.logger: 08-23 00:39:42] {2442} INFO -  at 2.4s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:42] {2258} INFO - iteration 5, current learner lgbm
[flaml.tune.tune: 08-23 00:39:42] {874} INFO - trial 1 config: {'n_estimators': 58, 'num_leaves': 5, 'min_child_samples': 5, 'learning_rate': 1.0, 'log_max_bin': 10, 'colsample_bytree': 0.8022556389143802, 'reg_alpha': 0.013840574983227511, 'reg_lambda': 6.63546949023169}
[flaml.automl.logger: 08-23 00:39:43] {2442} INFO -  at 3.0s,	estimator lgbm's best error=0.0986,	best estimator lgbm's best error=0.0986
[flaml.automl.logger: 08-23 00:39:43] {2685} INFO - retrain lgbm for 0.2s
[flaml.automl.logger: 08-23 00:39:43] {2688} INFO - retrained model: LGBMClassifier(colsample_bytree=0.7854369023412479,
               learning_rate=0.6681452089267123, max_bin=1023,
               min_child_samples=8, n_estimators=1, n_jobs=-1, num_leaves=9,
               reg_alpha=0.0046680380940597324, reg_lambda=2.7127484555926396,
               verbose=-1)
[flaml.automl.logger: 08-23 00:39:43] {1985} INFO - fit succeeded
[flaml.automl.logger: 08-23 00:39:43] {1986} INFO - Time taken to find the best model: 0.30064892768859863
am1.best_loss: 0.0986
am2.best_loss: 0.0986

```

```
[flaml.automl.logger: 08-23 00:39:40] {2688} INFO - retrained model: LGBMClassifier(colsample_bytree=0.7854369023412479,
               learning_rate=0.6681452089267123, max_bin=1023,
               min_child_samples=8, n_estimators=1, n_jobs=-1, num_leaves=9,
               reg_alpha=0.0046680380940597324, reg_lambda=2.7127484555926396,
               verbose=-1)

...

[flaml.tune.tune: 08-23 00:39:40] {874} INFO - trial 1 config: {'n_estimators': 28, 'num_leaves': 9, 'min_child_samples': 8, 'learning_rate': 0.6681452089267123, 'log_max_bin': 10, 'colsample_bytree': 0.7854369023412479, 'reg_alpha': 0.0046680380940597324, 'reg_lambda': 2.7127484555926396}
```
The `starting_points` is correctly used.

### Comment 8 ([user]):

You decreased the time_budget. Here is my log (when running with 60/30 time_budget) -

```
[flaml.automl.logger: 08-23 07:25:37] {1680} INFO - task = classification
[flaml.automl.logger: 08-23 07:25:37] {1691} INFO - Evaluation method: holdout
[flaml.automl.logger: 08-23 07:25:38] {1789} INFO - Minimizing error metric: log_loss
[flaml.automl.logger: 08-23 07:25:38] {1901} INFO - List of ML learners in AutoML Run: ['lgbm']
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 0, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2345} INFO - Estimated sufficient time budget=97022s. Estimated necessary time budget=97s.
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 0.7s,   estimator lgbm's best error=1.0978,     best estimator lgbm's best error=1.0978
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 1, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 0.7s,   estimator lgbm's best error=1.0978,     best estimator lgbm's best error=1.0978
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 2, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 0.8s,   estimator lgbm's best error=1.0949,     best estimator lgbm's best error=1.0949
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 3, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 0.9s,   estimator lgbm's best error=1.0341,     best estimator lgbm's best error=1.0341
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 4, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 1.0s,   estimator lgbm's best error=1.0341,     best estimator lgbm's best error=1.0341
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 5, current learner lgbm
[flaml.automl.logger: 08-23 07:25:38] {2392} INFO -  at 1.1s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:38] {2219} INFO - iteration 6, current learner lgbm
[flaml.automl.logger: 08-23 07:25:39] {2392} INFO -  at 1.3s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:39] {2219} INFO - iteration 7, current learner lgbm
[flaml.automl.logger: 08-23 07:25:39] {2392} INFO -  at 1.4s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:39] {2219} INFO - iteration 8, current learner lgbm
[flaml.automl.logger: 08-23 07:25:39] {2392} INFO -  at 1.8s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:39] {2219} INFO - iteration 9, current learner lgbm
[flaml.automl.logger: 08-23 07:25:40] {2392} INFO -  at 2.7s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:40] {2219} INFO - iteration 10, current learner lgbm
[flaml.automl.logger: 08-23 07:25:41] {2392} INFO -  at 3.2s,   estimator lgbm's best error=0.9739,     best estimator lgbm's best error=0.9739
[flaml.automl.logger: 08-23 07:25:41] {2219} INFO - iteration 11, current learner lgbm
[flaml.automl.logger: 08-23 07:25:41] {2392} INFO -  at 3.5s,   estimator lgbm's best error=0.9440,     best estimator lgbm's best error=0.9440
[flaml.automl.logger: 08-23 07:25:41] {2219} INFO - iteration 12, current learner lgbm
[flaml.automl.logger: 08-23 07:25:42] {2392} INFO -  at 4.5s,   estimator lgbm's best error=0.9440,     best estimator lgbm's best error=0.9440
[flaml.automl.logger: 08-23 07:25:42] {2219} INFO - iteration 13, current learner lgbm
[flaml.automl.logger: 08-23 07:25:43] {2392} INFO -  at 5.4s,   estimator lgbm's best error=0.8874,     best estimator lgbm's best error=0.8874
[flaml.automl.logger: 08-23 07:25:43] {2219} INFO - iteration 14, current learner lgbm
[flaml.automl.logger: 08-23 07:25:43] {2392} INFO -  at 5.6s,   estimator lgbm's best error=0.8874,     best estimator lgbm's best error=0.8874
[flaml.automl.logger: 08-23 07:25:43] {2219} INFO - iteration 15, current learner lgbm
[flaml.automl.logger: 08-23 07:25:45] {2392} INFO -  at 7.5s,   estimator lgbm's best error=0.7059,     best estimator lgbm's best error=0.7059
[flaml.automl.logger: 08-23 07:25:45] {2219} INFO - iteration 16, current learner lgbm
[flaml.automl.logger: 08-23 07:25:47] {2392} INFO -  at 9.3s,   estimator lgbm's best error=0.7059,     best estimator lgbm's best error=0.7059
[flaml.automl.logger: 08-23 07:25:47] {2219} INFO - iteration 17, current learner lgbm
[flaml.automl.logger: 08-23 07:25:50] {2392} INFO -  at 12.4s,  estimator lgbm's best error=0.7059,     best estimator lgbm's best error=0.7059
[flaml.automl.logger: 08-23 07:25:50] {2219} INFO - iteration 18, current learner lgbm
[flaml.automl.logger: 08-23 07:25:51] {2392} INFO -  at 13.5s,  estimator lgbm's best error=0.5011,     best estimator lgbm's best error=0.5011
[flaml.automl.logger: 08-23 07:25:51] {2219} INFO - iteration 19, current learner lgbm
[flaml.automl.logger: 08-23 07:25:51] {2392} INFO -  at 14.1s,  estimator lgbm's best error=0.5011,     best estimator lgbm's best error=0.5011
[flaml.automl.logger: 08-23 07:25:51] {2219} INFO - iteration 20, current learner lgbm
[flaml.automl.logger: 08-23 07:25:54] {2392} INFO -  at 17.2s,  estimator lgbm's best error=0.5011,     best estimator lgbm's best error=0.5011
[flaml.automl.logger: 08-23 07:25:54] {2219} INFO - iteration 21, current learner lgbm
[flaml.automl.logger: 08-23 07:25:57] {2392} INFO -  at 19.8s,  estimator lgbm's best error=0.5011,     best estimator lgbm's best error=0.5011
[flaml.automl.logger: 08-23 07:25:57] {2219} INFO - iteration 22, current learner lgbm
[flaml.automl.logger: 08-23 07:26:03] {2392} INFO -  at 25.7s,  estimator lgbm's best error=0.4370,     best estimator lgbm's best error=0.4370
[flaml.automl.logger: 08-23 07:26:03] {2219} INFO - iteration 23, current learner lgbm
[flaml.automl.logger: 08-23 07:26:05] {2392} INFO -  at 27.4s,  estimator lgbm's best error=0.4370,     best estimator lgbm's best error=0.4370
[flaml.automl.logger: 08-23 07:26:05] {2219} INFO - iteration 24, current learner lgbm
[flaml.automl.logger: 08-23 07:26:24] {2392} INFO -  at 46.4s,  estimator lgbm's best error=0.4370,     best estimator lgbm's best error=0.4370
[flaml.automl.logger: 08-23 07:26:24] {2219} INFO - iteration 25, current learner lgbm
[flaml.automl.logger: 08-23 07:26:28] {2392} INFO -  at 50.3s,  estimator lgbm's best error=0.4370,     best estimator lgbm's best error=0.4370
[flaml.automl.logger: 08-23 07:26:28] {2219} INFO - iteration 26, current learner lgbm
[flaml.automl.logger: 08-23 07:26:37] {2392} INFO -  at 60.0s,  estimator lgbm's best error=0.4003,     best estimator lgbm's best error=0.4003
[flaml.automl.logger: 08-23 07:26:47] {2628} INFO - retrain lgbm for 9.5s
[flaml.automl.logger: 08-23 07:26:47] {2631} INFO - retrained model: LGBMClassifier(colsample_bytree=0.6385756292196149, learning_rate=1.0,
               max_bin=1023, min_child_samples=6, n_estimators=1, n_jobs=-1,
               num_leaves=23, reg_alpha=0.0021485314598267266,
               reg_lambda=226.20169683228747, verbose=-1)
[flaml.automl.logger: 08-23 07:26:47] {1931} INFO - fit succeeded
[flaml.automl.logger: 08-23 07:26:47] {1932} INFO - Time taken to find the best model: 60.02181434631348
[flaml.automl.logger: 08-23 07:26:47] {1680} INFO - task = classification
[flaml.automl.logger: 08-23 07:26:47] {1691} INFO - Evaluation method: holdout
[flaml.automl.logger: 08-23 07:26:47] {1789} INFO - Minimizing error metric: log_loss
[flaml.automl.logger: 08-23 07:26:47] {1901} INFO - List of ML learners in AutoML Run: ['lgbm']
[flaml.automl.logger: 08-23 07:26:47] {2219} INFO - iteration 0, current learner lgbm
[flaml.automl.logger: 08-23 07:26:48] {2345} INFO - Estimated sufficient time budget=227442s. Estimated necessary time budget=227s.
[flaml.automl.logger: 08-23 07:26:48] {2392} INFO -  at 0.6s,   estimator lgbm's best error=1.0791,     best estimator lgbm's best error=1.0791
[flaml.automl.logger: 08-23 07:26:48] {2219} INFO - iteration 1, current learner lgbm
[flaml.automl.logger: 08-23 07:26:48] {2392} INFO -  at 0.8s,   estimator lgbm's best error=1.0791,     best estimator lgbm's best error=1.0791
[flaml.automl.logger: 08-23 07:26:48] {2219} INFO - iteration 2, current learner lgbm
[flaml.automl.logger: 08-23 07:26:48] {2392} INFO -  at 1.0s,   estimator lgbm's best error=1.0791,     best estimator lgbm's best error=1.0791
[flaml.automl.logger: 08-23 07:26:48] {2219} INFO - iteration 3, current learner lgbm
[flaml.automl.logger: 08-23 07:26:48] {2392} INFO -  at 1.1s,   estimator lgbm's best error=1.0791,     best estimator lgbm's best error=1.0791
[flaml.automl.logger: 08-23 07:26:48] {2219} INFO - iteration 4, current learner lgbm
[flaml.automl.logger: 08-23 07:26:48] {2392} INFO -  at 1.3s,   estimator lgbm's best error=1.0791,     best estimator lgbm's best error=1.0791
[flaml.automl.logger: 08-23 07:26:48] {2219} INFO - iteration 5, current learner lgbm
[flaml.automl.logger: 08-23 07:26:49] {2392} INFO -  at 1.9s,   estimator lgbm's best error=0.9526,     best estimator lgbm's best error=0.9526
[flaml.automl.logger: 08-23 07:26:49] {2219} INFO - iteration 6, current learner lgbm
[flaml.automl.logger: 08-23 07:26:49] {2392} INFO -  at 2.4s,   estimator lgbm's best error=0.9526,     best estimator lgbm's best error=0.9526
[flaml.automl.logger: 08-23 07:26:49] {2219} INFO - iteration 7, current learner lgbm
[flaml.automl.logger: 08-23 07:26:50] {2392} INFO -  at 2.9s,   estimator lgbm's best error=0.9526,     best estimator lgbm's best error=0.9526
[flaml.automl.logger: 08-23 07:26:50] {2219} INFO - iteration 8, current learner lgbm
[flaml.automl.logger: 08-23 07:26:50] {2392} INFO -  at 3.2s,   estimator lgbm's best error=0.9526,     best estimator lgbm's best error=0.9526
[flaml.automl.logger: 08-23 07:26:50] {2219} INFO - iteration 9, current learner lgbm
[flaml.automl.logger: 08-23 07:26:51] {2392} INFO -  at 3.7s,   estimator lgbm's best error=0.9234,     best estimator lgbm's best error=0.9234
[flaml.automl.logger: 08-23 07:26:51] {2219} INFO - iteration 10, current learner lgbm
[flaml.automl.logger: 08-23 07:26:51] {2392} INFO -  at 4.3s,   estimator lgbm's best error=0.9234,     best estimator lgbm's best error=0.9234
[flaml.automl.logger: 08-23 07:26:51] {2219} INFO - iteration 11, current learner lgbm
[flaml.automl.logger: 08-23 07:26:52] {2392} INFO -  at 4.7s,   estimator lgbm's best error=0.9234,     best estimator lgbm's best error=0.9234
[flaml.automl.logger: 08-23 07:26:52] {2219} INFO - iteration 12, current learner lgbm
[flaml.automl.logger: 08-23 07:26:52] {2392} INFO -  at 5.3s,   estimator lgbm's best error=0.9234,     best estimator lgbm's best error=0.9234
[flaml.automl.logger: 08-23 07:26:52] {2219} INFO - iteration 13, current learner lgbm
[flaml.automl.logger: 08-23 07:26:53] {2392} INFO -  at 5.8s,   estimator lgbm's best error=0.5855,     best estimator lgbm's best error=0.5855
[flaml.automl.logger: 08-23 07:26:53] {2219} INFO - iteration 14, current learner lgbm
[flaml.automl.logger: 08-23 07:26:53] {2392} INFO -  at 6.3s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:53] {2219} INFO - iteration 15, current learner lgbm
[flaml.automl.logger: 08-23 07:26:53] {2392} INFO -  at 6.6s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:53] {2219} INFO - iteration 16, current learner lgbm
[flaml.automl.logger: 08-23 07:26:54] {2392} INFO -  at 7.1s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:54] {2219} INFO - iteration 17, current learner lgbm
[flaml.automl.logger: 08-23 07:26:54] {2392} INFO -  at 7.5s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:54] {2219} INFO - iteration 18, current learner lgbm
[flaml.automl.logger: 08-23 07:26:55] {2392} INFO -  at 8.0s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:55] {2219} INFO - iteration 19, current learner lgbm
[flaml.automl.logger: 08-23 07:26:55] {2392} INFO -  at 8.4s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:55] {2219} INFO - iteration 20, current learner lgbm
[flaml.automl.logger: 08-23 07:26:56] {2392} INFO -  at 8.8s,   estimator lgbm's best error=0.4760,     best estimator lgbm's best error=0.4760
[flaml.automl.logger: 08-23 07:26:56] {2219} INFO - iteration 21, current learner lgbm
[flaml.automl.logger: 08-23 07:26:57] {2392} INFO -  at 10.2s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:26:57] {2219} INFO - iteration 22, current learner lgbm
[flaml.automl.logger: 08-23 07:26:58] {2392} INFO -  at 10.8s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:26:58] {2219} INFO - iteration 23, current learner lgbm
[flaml.automl.logger: 08-23 07:26:59] {2392} INFO -  at 11.9s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:26:59] {2219} INFO - iteration 24, current learner lgbm
[flaml.automl.logger: 08-23 07:27:00] {2392} INFO -  at 13.1s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:27:00] {2219} INFO - iteration 25, current learner lgbm
[flaml.automl.logger: 08-23 07:27:01] {2392} INFO -  at 14.1s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:27:01] {2219} INFO - iteration 26, current learner lgbm
[flaml.automl.logger: 08-23 07:27:02] {2392} INFO -  at 15.4s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:27:02] {2219} INFO - iteration 27, current learner lgbm
[flaml.automl.logger: 08-23 07:27:03] {2392} INFO -  at 16.0s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:27:03] {2219} INFO - iteration 28, current learner lgbm
[flaml.automl.logger: 08-23 07:27:16] {2392} INFO -  at 29.2s,  estimator lgbm's best error=0.4135,     best estimator lgbm's best error=0.4135
[flaml.automl.logger: 08-23 07:27:34] {2628} INFO - retrain lgbm for 18.2s
[flaml.automl.logger: 08-23 07:27:34] {2631} INFO - retrained model: LGBMClassifier(colsample_bytree=0.8807916995792399, learning_rate=1.0,
               max_bin=511, min_child_samples=6, n_estimators=1, n_jobs=-1,
               num_leaves=133, reg_alpha=0.010458389890154931,
               reg_lambda=9.452290991116241, verbose=-1)
[flaml.automl.logger: 08-23 07:27:34] {1931} INFO - fit succeeded
[flaml.automl.logger: 08-23 07:27:34] {1932} INFO - Time taken to find the best model: 10.166210651397705
am1.best_loss: 0.4003
am2.best_loss: 0.4135
```

### Comment 9 ([user]):

And N=10000 (with N=10 the issue is not reproducible).

To my opinion the issue happens in large data-sets since FLAML_sample_size is not included in the best_config_per_estimator dict.

### Comment 10 ([user]):

> And N=10000 (with N=10 the issue is not reproducible).
> 
> To my opinion the issue happens in large data-sets since FLAML_sample_size is not included in the best_config_per_estimator dict.

Hi [user], the starting_point is used. I don't see any issue in your output. Do you want to see `am1.best_loss = am2.best_loss`?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
