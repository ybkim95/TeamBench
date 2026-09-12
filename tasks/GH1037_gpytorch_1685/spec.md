# GH1037_gpytorch_1685: Kernel batch size recurses through module lists. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1672
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug: Possible error with multitask learning with additive kernel structure

<!-- A clear and concise description of what the bug is. -->
When I define in the class MultitaskGPModel the multitask kernel

            self.covar_module = (gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.PeriodicKernel(batch_shape=torch.Size([num_latents])) * 
                     gpytorch.kernels.RQKernel(batch_shape=torch.Size([num_latents])),
                                               batch_shape=torch.Size([num_latents])
                                                             )  + 
                                gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.MaternKernel(nu=0.5, batch_shape=torch.Size([num_latents])), 
                                               batch_shape=torch.Size([num_latents])
                                                             )
                                )

which uses the additive kernel as its outermost layer, and I apply the class on data as

  w_l = 50
  num_latents = 24
  Xc_t_npa = np.arange(0,w_l,1,dtype=np.float32).reshape(-1, 1)
  Xc_t = torch.from_numpy(Xc_t_npa).type(torch.Tensor)
  model_mul(Xc_t)

I get 
'RuntimeError: The expected shape of the kernel was torch.Size([100, 100]), but got torch.Size([24, 100, 100]). This is likely a bug in GPyTorch'.
This behavior seems not to change when changing the number of tasks or the number of latent gps.

If I use the same kernel in a non-batch setting, it works smoothly.

I wrote the batched problem with another kernel which is mathematically the same but which doesn't use the outer additive kernel, and it works smoothly. Unfortunatly the role of the subkernel parameters in the new form is not the same as that of the malfunctioning kernel, and I have to re-run a lot of past non-batch fits in the new form to make them comparable with the new setting.


## To reproduce

** Code snippet to reproduce **
```python
# Your code goes here
# Please make sure it does not require any external dependencies (other than PyTorch!)
# (We much prefer small snippets rather than links to existing libraries!)
```
    Zc_intra_np = np.arange(0, 24, 1).reshape(-1, 1)
    Zc_intra = torch.tensor(Zc_intra_np, dtype=torch.float)
 
    w_l = 50
    num_latents = 24
    num_tasks = 12
    Xc_t_npa = np.arange(0,w_l,1,dtype=np.float32).reshape(-1, 1)
    Xc_t = torch.from_numpy(Xc_t_npa).type(torch.Tensor)

    model_mul = MultitaskGPModel()
    likelihood_mul = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)
    model_mul(Xc_t)


    class MultitaskGPModel(gpytorch.models.ApproximateGP):
        
        def __init__(self):
            

            inducing_points = Zc_intra
        
            variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(
                inducing_points.size(-2), batch_shape=torch.Size([num_latents])
            )

            variational_strategy = gpytorch.variational.LMCVariationalStrategy(
                gpytorch.variational.VariationalStrategy(
                    self, inducing_points, variational_distribution, learn_inducing_locations=True
                ),
                num_tasks=num_tasks,
                num_latents=num_latents,
                # could be 0
                latent_dim=-1
            )

            super().__init__(variational_strategy)

            self.mean_module = gpytorch.means.ConstantMean(batch_shape=torch.Size([num_latents]))
        
            self.covar_module = gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.PeriodicKernel(batch_shape=torch.Size([num_latents])) * 
                     gpytorch.kernels.RQKernel(batch_shape=torch.Size([num_latents]))  + 
                     gpytorch.kernels.ScaleKernel(
                         gpytorch.kernels.MaternKernel(nu=0.5, batch_shape=torch.Size([num_latents])), 
                                                 batch_shape=torch.Size([num_latents])),                 
                             batch_shape=torch.Size([num_latents])  
                                                             )


        def forward(self, x):
            mean_x = self.mean_module(x)
            covar_x = self.covar_module(x)
            return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)






** Stack trace/error message **
```
Traceback (most recent call last):

  File "<ipython-input-398-5fc832e3a3f0>", line 1, in <module>
    model_mul(Xc_t)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\models\approximate_gp.py", line 81, in __call__
    return self.variational_strategy(inputs, prior=prior, **kwargs)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\variational\lmc_variational_strategy.py", line 124, in __call__
    function_dist = self.base_variational_strategy(x, prior=prior, **kwargs)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\variational\variational_strategy.py", line 168, in __call__
    return super().__call__(x, prior=prior, **kwargs)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\variational\_variational_strategy.py", line 129, in __call__
    **kwargs,

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\module.py", line 28, in __call__
    outputs = self.forward(*inputs, **kwargs)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\variational\variational_strategy.py", line 96, in forward
    induc_induc_covar = full_covar[..., :num_induc, :num_induc].add_jitter()

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\lazy\lazy_evaluated_kernel_tensor.py", line 237, in add_jitter
    return self.evaluate_kernel().add_jitter(jitter_val)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\utils\memoize.py", line 59, in g
    return _add_to_cache(self, cache_name, method(self, *args, **kwargs), *args, kwargs_pkl=kwargs_pkl)

  File "C:\Users\lucheron\Anaconda3\envs\pyro16_py37\lib\site-packages\gpytorch\lazy\lazy_evaluated_kernel_tensor.py", line 291, in evaluate_kernel
    f"The expected shape of the kernel was {self.shape}, but got {res.shape}. "

RuntimeError: The expected shape of the kernel was torch.Size([100, 100]), but got torch.Size([24, 100, 100]). This is likely a bug in GPyTorch.
```

## Expected Behavior

<!-- A clear and concise description of what you expected to happen. --> Run with no errors

## System information

**Please complete the following information:**
- <!-- GPyTorch Version (run `print(gpytorch.__version__)` --> 1.4.1
- <!-- PyTorch Version (run `print(torch.__version__)` --> 1.8.1
- <!-- Computer OS --> Win10 pro 19042.1052

## Additional context
Add any other context about the problem here.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I cannot reproduce your error based on the code example you provide. I had to fix the code example to get it to run:

```python
import gpytorch
import numpy as np
import torch


class MultitaskGPModel(gpytorch.models.ApproximateGP):
    
    def __init__(self):
        

        inducing_points = Zc_intra
    
        variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(
            inducing_points.size(-2), batch_shape=torch.Size([num_latents])
        )

        variational_strategy = gpytorch.variational.LMCVariationalStrategy(
            gpytorch.variational.VariationalStrategy(
                self, inducing_points, variational_distribution, learn_inducing_locations=True
            ),
            num_tasks=num_tasks,
            num_latents=num_latents,
            # could be 0
            latent_dim=-1
        )

        super().__init__(variational_strategy)

        self.mean_module = gpytorch.means.ConstantMean(batch_shape=torch.Size([num_latents]))
    
        self.covar_module = gpytorch.kernels.ScaleKernel(
                 gpytorch.kernels.PeriodicKernel(batch_shape=torch.Size([num_latents])) * 
                 gpytorch.kernels.RQKernel(batch_shape=torch.Size([num_latents]))  + 
                 gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.MaternKernel(nu=0.5, batch_shape=torch.Size([num_latents])), 
                                             batch_shape=torch.Size([num_latents])),                 
                         batch_shape=torch.Size([num_latents])  
                                                         )


    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
    
    

Zc_intra_np = np.arange(0, 24, 1).reshape(-1, 1)
Zc_intra = torch.tensor(Zc_intra_np, dtype=torch.float)

w_l = 50
num_latents = 24
num_tasks = 12
Xc_t_npa = np.arange(0,w_l,1,dtype=np.float32).reshape(-1, 1)
Xc_t = torch.from_numpy(Xc_t_npa).type(torch.Tensor)

model_mul = MultitaskGPModel()
likelihood_mul = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)
model_mul(Xc_t).covariance_matrix
```

### Comment 2 ([user]):

My mistake. I posted the fixed up version of the kernel - the one in which I eliminated the external additive layer. 

I gather hereafter a more elaborated, self-contained extract of the program which gives me the error.

One can run it with the 'fixed_kernel = False' flag (inside the MultitaskGPModel class) and get the error, or with the 'fixed_kernel = True' flag, not getting the error.

Thank you for the quick answer, and in perspective for your patience :)

```
import gpytorch
import numpy as np
import torch

class MultitaskGPModel(gpytorch.models.ApproximateGP):
    
    def __init__(self):
        
        inducing_points = Zc_intra
    
        variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(
            inducing_points.size(-2), batch_shape=torch.Size([num_latents])
        )

        variational_strategy = gpytorch.variational.LMCVariationalStrategy(
            gpytorch.variational.VariationalStrategy(
                self, inducing_points, variational_distribution, learn_inducing_locations=True
            ),
            num_tasks=num_tasks,
            num_latents=num_latents,
            latent_dim=-1
        )

        super().__init__(variational_strategy)

        self.mean_module = gpytorch.means.ConstantMean(batch_shape=torch.Size([num_latents]))
 
        
        fixed_kernel = False
    
        if fixed_kernel:            
            # fixed kernel - works
            self.covar_module = gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.PeriodicKernel(batch_shape=torch.Size([num_latents])) * 
                     gpytorch.kernels.RQKernel(batch_shape=torch.Size([num_latents]))  + 
                     gpytorch.kernels.ScaleKernel(
                         gpytorch.kernels.MaternKernel(nu=0.5, batch_shape=torch.Size([num_latents])), 
                                                 batch_shape=torch.Size([num_latents])),                 
                             batch_shape=torch.Size([num_latents])  
                                                             )
                        
        else:
            # original kernel - gives problem
            self.covar_module = gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.PeriodicKernel(batch_shape=torch.Size([num_latents])) * 
                     gpytorch.kernels.RQKernel(batch_shape=torch.Size([num_latents])),
                                               batch_shape=torch.Size([num_latents])
                                                             )  + \
                            gpytorch.kernels.ScaleKernel(
                     gpytorch.kernels.MaternKernel(nu=0.5, batch_shape=torch.Size([num_latents])), 
                                               batch_shape=torch.Size([num_latents])
                                                             )
        
                                    
    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
        
Zc_intra_np = np.arange(0, 24, 1).reshape(-1, 1)
Zc_intra = torch.tensor(Zc_intra_np, dtype=torch.float)

w_l = 50
num_latents = 24
num_tasks = 12
Xc_t_npa = np.arange(0,w_l,1,dtype=np.float32).reshape(-1, 1)
Xc_t = torch.from_numpy(Xc_t_npa).type(torch.Tensor)

model_mul = MultitaskGPModel()
likelihood_mul = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)

model_mul(Xc_t).covariance_matrix

Yc_t = torch.rand((50,12))
    
Yc_t = torch.tensor(Yc_t,dtype=torch.float
                    ).flatten().reshape(Yc_t.shape[0],Yc_t.shape[1])

training_iter = 5

model_mul.train()
likelihood_mul.train()

optimizer_mul = torch.optim.Adam([
    {'params': model_mul.parameters()},
    {'params': likelihood_mul.parameters()},
], lr=0.1)

mll_mul = gpytorch.mlls.VariationalELBO(likelihood_mul, model_mul, num_data=Yc_t.size(0))

for i in range(training_iter):    
        optimizer_mul.zero_grad()
        output = model_mul(Xc_t)
        loss = -mll_mul(output, Yc_t)
        loss.backward()
        optimizer_mul.step()
```

The error is now
```
RuntimeError: The expected shape of the kernel was torch.Size([24, 24]), but got torch.Size([24, 24, 24]). This is likely a bug in GPyTorch.
```
and can be obtained by just running
```
model_mul(Xc_t)
```
after the model is instantiated.

One extra piece of information, which I don't know if it can be useful. In my environment I first installed pyro-ppl 1.6.0, then gpytorch 1.4.1.

### Comment 3 ([user]):

Further information.
I built from scratch a new Python/Spyder environment with GPyTorch 1.4.1 without previous Pyro installation. 
Running the program with the 'fixed_kernel = False' returns again the 'This is likely a bug in GPyTorch.' message. 
Program runs smoothly wiith  'fixed_kernel = True'.

### Comment 4 ([user]):

Gotcha. This looks like a bug on our end. I'll put up a PR to fix it.

### Comment 5 ([user]):

Thanks. I guess that if it is a bug, it is located in the
variational_strategy module
I've rewritten my program as an exact multitask GP, and I'm getting no
problem with the addition of kernels.

Carlo

On Mon, Jul 5, 2021 at 5:35 PM Geoff Pleiss ***@***.***>
wrote:

> Gotcha. This looks like a bug on our end. I'll put up a PR to fix it.
>
> —
> You are receiving this because you authored the thread.
> Reply to this email directly, view it on GitHub
> <https://github.com/cornellius-gp/gpytorch/issues/1672#issuecomment-874197843>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AOMFUN4NG4F6IAGHOUKJJFTTWHGMFANCNFSM47HHVUJA>
> .
>
>
>

-- 
Carlo Lucheroni
School of Sciences and Technologies
Universita' di Camerino
via Madonna delle Carceri 9
62032 Camerino (MC)
Italy
Office phone: 39-0737402552


--
Ask me for  my Mathematical Finance and
Stochastic Dynamic Optimization courseware:
'Take the Chance!'

View and download my papers on Finance and Physics from ResearchGate:
https://www.researchgate.net/profile/Carlo_Lucheroni/publications

View and download my research on power markets on my SSRN Author page:
http://ssrn.com/author=1390778

You can also check IDEAS/RePEc for my name:
https://ideas.repec.org/f/plu234.html <https://ideas.repec.org/>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
