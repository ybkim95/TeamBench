# GH1018_scikit_learn_25432: FIX Support readonly sparse datasets for `manhattan_distances`  — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/7981
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

From https://github.com/scikit-learn/scikit-learn/issues/5481#issuecomment-264770593.

#### Description
ValueError buffer source array is read-only when computing manahattan_distances of a CSR matrix inside Parallel

#### Steps/Code to Reproduce

```py
import numpy as np

from scipy.sparse import csr_matrix

from sklearn.externals.joblib import Parallel, delayed
from sklearn.metrics.pairwise import manhattan_distances

matrices1 = [csr_matrix(np.ones((5, 5)))]
matrices2 = [csr_matrix(np.ones((5, 5)))]

Parallel(n_jobs=-1, max_nbytes=0)(
    delayed(manhattan_distances)(m1, m2)
    for m1, m2 in zip(matrices1, matrices2))
```

Full traceback:
<details>

```
---------------------------------------------------------------------------
RemoteTraceback                           Traceback (most recent call last)
RemoteTraceback: 
"""
Traceback (most recent call last):
  File "/home/le243287/dev/scikit-learn/sklearn/externals/joblib/_parallel_backends.py", line 344, in __call__
    return self.func(*args, **kwargs)
  File "/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py", line 131, in __call__
    return [func(*args, **kwargs) for func, args, kwargs in self.items]
  File "/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py", line 131, in <listcomp>
    return [func(*args, **kwargs) for func, args, kwargs in self.items]
  File "/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise.py", line 533, in manhattan_distances
    X.shape[1], D)
  File "sklearn/metrics/pairwise_fast.pyx", line 53, in sklearn.metrics.pairwise_fast._sparse_manhattan (sklearn/metrics/pairwise_fast.c:4688)
    def _sparse_manhattan(floating1d X_data, int[:] X_indices, int[:] X_indptr,
  File "stringsource", line 644, in View.MemoryView.memoryview_cwrapper (sklearn/metrics/pairwise_fast.c:13277)
  File "stringsource", line 345, in View.MemoryView.memoryview.__cinit__ (sklearn/metrics/pairwise_fast.c:9512)
ValueError: buffer source array is read-only

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/volatile/le243287/miniconda3/lib/python3.5/multiprocessing/pool.py", line 119, in worker
    result = (True, func(*args, **kwds))
  File "/home/le243287/dev/scikit-learn/sklearn/externals/joblib/_parallel_backends.py", line 353, in __call__
    raise TransportableException(text, e_type)
sklearn.externals.joblib.my_exceptions.TransportableException: TransportableException
___________________________________________________________________________
ValueError                                         Mon Dec  5 13:19:44 2016
PID: 25869           Python 3.5.2: /volatile/le243287/miniconda3/bin/python
...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in __call__(self=<sklearn.externals.joblib.parallel.BatchedCalls object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        self.items = [(<function manhattan_distances>, (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>), {})]
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in <listcomp>(.0=<list_iterator object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        func = <function manhattan_distances>
        args = (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>)
        kwargs = {}
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise.py in manhattan_distances(X=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, Y=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, sum_over_features=True, size_threshold=500000000.0)
    528         X = csr_matrix(X, copy=False)
    529         Y = csr_matrix(Y, copy=False)
    530         D = np.zeros((X.shape[0], Y.shape[0]))
    531         _sparse_manhattan(X.data, X.indices, X.indptr,
    532                           Y.data, Y.indices, Y.indptr,
--> 533                           X.shape[1], D)
        X.shape = (5, 5)
        D = array([[ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  ...0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.]])
    534         return D
    535 
    536     if sum_over_features:
    537         return distance.cdist(X, Y, 'cityblock')

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in sklearn.metrics.pairwise_fast._sparse_manhattan (sklearn/metrics/pairwise_fast.c:4688)()
     48                     if nom != 0:
     49                         res  += denom * denom / nom
     50                 result[i, j] = -res
     51 
     52 
---> 53 def _sparse_manhattan(floating1d X_data, int[:] X_indices, int[:] X_indptr,
     54                       floating1d Y_data, int[:] Y_indices, int[:] Y_indptr,
     55                       np.npy_intp n_features, double[:, ::1] D):
     56     """Pairwise L1 distances for CSR matrices.
     57 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview_cwrapper (sklearn/metrics/pairwise_fast.c:13277)()
    639 
    640 
    641 
    642 
    643 
--> 644 
    645 
    646 
    647 
    648 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview.__cinit__ (sklearn/metrics/pairwise_fast.c:9512)()
    340 
    341 
    342 
    343 
    344 
--> 345 
    346 
    347 
    348 
    349 

ValueError: buffer source array is read-only
___________________________________________________________________________
"""

The above exception was the direct cause of the following exception:

TransportableException                    Traceback (most recent call last)
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in retrieve(self)
    681                 if 'timeout' in getfullargspec(job.get).args:
--> 682                     self._output.extend(job.get(timeout=self.timeout))
    683                 else:

/volatile/le243287/miniconda3/lib/python3.5/multiprocessing/pool.py in get(self, timeout)
    607         else:
--> 608             raise self._value
    609 

TransportableException: TransportableException
___________________________________________________________________________
ValueError                                         Mon Dec  5 13:19:44 2016
PID: 25869           Python 3.5.2: /volatile/le243287/miniconda3/bin/python
...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in __call__(self=<sklearn.externals.joblib.parallel.BatchedCalls object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        self.items = [(<function manhattan_distances>, (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>), {})]
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in <listcomp>(.0=<list_iterator object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        func = <function manhattan_distances>
        args = (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>)
        kwargs = {}
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise.py in manhattan_distances(X=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, Y=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, sum_over_features=True, size_threshold=500000000.0)
    528         X = csr_matrix(X, copy=False)
    529         Y = csr_matrix(Y, copy=False)
    530         D = np.zeros((X.shape[0], Y.shape[0]))
    531         _sparse_manhattan(X.data, X.indices, X.indptr,
    532                           Y.data, Y.indices, Y.indptr,
--> 533                           X.shape[1], D)
        X.shape = (5, 5)
        D = array([[ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  ...0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.]])
    534         return D
    535 
    536     if sum_over_features:
    537         return distance.cdist(X, Y, 'cityblock')

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in sklearn.metrics.pairwise_fast._sparse_manhattan (sklearn/metrics/pairwise_fast.c:4688)()
     48                     if nom != 0:
     49                         res  += denom * denom / nom
     50                 result[i, j] = -res
     51 
     52 
---> 53 def _sparse_manhattan(floating1d X_data, int[:] X_indices, int[:] X_indptr,
     54                       floating1d Y_data, int[:] Y_indices, int[:] Y_indptr,
     55                       np.npy_intp n_features, double[:, ::1] D):
     56     """Pairwise L1 distances for CSR matrices.
     57 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview_cwrapper (sklearn/metrics/pairwise_fast.c:13277)()
    639 
    640 
    641 
    642 
    643 
--> 644 
    645 
    646 
    647 
    648 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview.__cinit__ (sklearn/metrics/pairwise_fast.c:9512)()
    340 
    341 
    342 
    343 
    344 
--> 345 
    346 
    347 
    348 
    349 

ValueError: buffer source array is read-only
___________________________________________________________________________

During handling of the above exception, another exception occurred:

JoblibValueError                          Traceback (most recent call last)
/tmp/test_manhattan.py in <module>()
     11 Parallel(n_jobs=2, max_nbytes=0)(
     12     delayed(manhattan_distances)(m1, m2)
---> 13     for m1, m2 in zip(matrices1, matrices2))

/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in __call__(self, iterable)
    766                 # consumption.
    767                 self._iterating = False
--> 768             self.retrieve()
    769             # Make sure that we get a last message telling us we are done
    770             elapsed_time = time.time() - self._start_time

/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in retrieve(self)
    717                     ensure_ready = self._managed_backend
    718                     backend.abort_everything(ensure_ready=ensure_ready)
--> 719                 raise exception
    720 
    721     def __call__(self, iterable):

JoblibValueError: JoblibValueError
___________________________________________________________________________
Multiprocessing exception:
...........................................................................
/volatile/le243287/miniconda3/bin/ipython in <module>()
      1 #!/volatile/le243287/miniconda3/bin/python
      2 if __name__ == '__main__':
      3     import sys
      4     import IPython
      5 
----> 6     sys.exit(IPython.start_ipython())
      7 
      8 
      9 
     10 

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/__init__.py in start_ipython(argv=None, **kwargs={})
    114     kwargs : various, optional
    115         Any other kwargs will be passed to the Application constructor,
    116         such as `config`.
    117     """
    118     from IPython.terminal.ipapp import launch_new_instance
--> 119     return launch_new_instance(argv=argv, **kwargs)
        launch_new_instance = <bound method Application.launch_instance of <class 'IPython.terminal.ipapp.TerminalIPythonApp'>>
        argv = None
        kwargs = {}
    120 
    121 def start_kernel(argv=None, **kwargs):
    122     """Launch a normal IPython kernel instance (as opposed to embedded)
    123     

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/traitlets/config/application.py in launch_instance(cls=<class 'IPython.terminal.ipapp.TerminalIPythonApp'>, argv=None, **kwargs={})
    652         """Launch a global instance of this Application
    653 
    654         If a global instance already exists, this reinitializes and starts it
    655         """
    656         app = cls.instance(**kwargs)
--> 657         app.initialize(argv)
        app.initialize = <bound method TerminalIPythonApp.initialize of <IPython.terminal.ipapp.TerminalIPythonApp object>>
        argv = None
    658         app.start()
    659 
    660 #-----------------------------------------------------------------------------
    661 # utility functions, for convenience

...........................................................................
/home/le243287/dev/scikit-learn/<decorator-gen-109> in initialize(self=<IPython.terminal.ipapp.TerminalIPythonApp object>, argv=None)
      1 
----> 2 
      3 
      4 
      5 
      6 
      7 
      8 
      9 
     10 

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/traitlets/config/application.py in catch_config_error(method=<function TerminalIPythonApp.initialize>, app=<IPython.terminal.ipapp.TerminalIPythonApp object>, *args=(None,), **kwargs={})
     82     message, and exit the app.
     83 
     84     For use on init methods, to prevent invoking excepthook on invalid input.
     85     """
     86     try:
---> 87         return method(app, *args, **kwargs)
        method = <function TerminalIPythonApp.initialize>
        app = <IPython.terminal.ipapp.TerminalIPythonApp object>
        args = (None,)
        kwargs = {}
     88     except (TraitError, ArgumentError) as e:
     89         app.print_help()
     90         app.log.fatal("Bad config encountered during initialization:")
     91         app.log.fatal(str(e))

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/terminal/ipapp.py in initialize(self=<IPython.terminal.ipapp.TerminalIPythonApp object>, argv=None)
    310         # and draw the banner
    311         self.init_banner()
    312         # Now a variety of things that happen after the banner is printed.
    313         self.init_gui_pylab()
    314         self.init_extensions()
--> 315         self.init_code()
        self.init_code = <bound method InteractiveShellApp.init_code of <IPython.terminal.ipapp.TerminalIPythonApp object>>
    316 
    317     def init_shell(self):
    318         """initialize the InteractiveShell instance"""
    319         # Create an InteractiveShell instance.

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/core/shellapp.py in init_code(self=<IPython.terminal.ipapp.TerminalIPythonApp object>)
    268         if self.hide_initial_ns:
    269             self.shell.user_ns_hidden.update(self.shell.user_ns)
    270 
    271         # command-line execution (ipython -i script.py, ipython -m module)
    272         # should *not* be excluded from %whos
--> 273         self._run_cmd_line_code()
        self._run_cmd_line_code = <bound method InteractiveShellApp._run_cmd_line_...Python.terminal.ipapp.TerminalIPythonApp object>>
    274         self._run_module()
    275 
    276         # flush output, so itwon't be attached to the first cell
    277         sys.stdout.flush()

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/core/shellapp.py in _run_cmd_line_code(self=<IPython.terminal.ipapp.TerminalIPythonApp object>)
    389         elif self.file_to_run:
    390             fname = self.file_to_run
    391             if os.path.isdir(fname):
    392                 fname = os.path.join(fname, "__main__.py")
    393             try:
--> 394                 self._exec_file(fname, shell_futures=True)
        self._exec_file = <bound method InteractiveShellApp._exec_file of <IPython.terminal.ipapp.TerminalIPythonApp object>>
        fname = '/tmp/test_manhattan.py'
    395             except:
    396                 self.shell.showtraceback(tb_offset=4)
    397                 if not self.interact:
    398                     self.exit(1)

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/core/shellapp.py in _exec_file(self=<IPython.terminal.ipapp.TerminalIPythonApp object>, fname='/tmp/test_manhattan.py', shell_futures=True)
    323                     else:
    324                         # default to python, even without extension
    325                         self.shell.safe_execfile(full_filename,
    326                                                  self.shell.user_ns,
    327                                                  shell_futures=shell_futures,
--> 328                                                  raise_exceptions=True)
    329         finally:
    330             sys.argv = save_argv
    331 
    332     def _run_startup_files(self):

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/core/interactiveshell.py in safe_execfile(self=<IPython.terminal.interactiveshell.TerminalInteractiveShell object>, fname='/tmp/test_manhattan.py', *where=({'In': [''], 'Out': {}, 'Parallel': <class 'sklearn.externals.joblib.parallel.Parallel'>, '_': '', '__': '', '___': '', '__builtin__': <module 'builtins' (built-in)>, '__builtins__': <module 'builtins' (built-in)>, '__doc__': 'Automatically created module for IPython interactive environment', '__file__': '/tmp/test_manhattan.py', ...},), **kw={'exit_ignore': False, 'raise_exceptions': True, 'shell_futures': True})
   2476         with prepended_to_syspath(dname), self.builtin_trap:
   2477             try:
   2478                 glob, loc = (where + (None, ))[:2]
   2479                 py3compat.execfile(
   2480                     fname, glob, loc,
-> 2481                     self.compile if kw['shell_futures'] else None)
        self.compile = <IPython.core.compilerop.CachingCompiler object>
        kw = {'exit_ignore': False, 'raise_exceptions': True, 'shell_futures': True}
   2482             except SystemExit as status:
   2483                 # If the call was made with 0 or None exit status (sys.exit(0)
   2484                 # or sys.exit() ), don't bother showing a traceback, as both of
   2485                 # these are considered normal by the OS:

...........................................................................
/volatile/le243287/miniconda3/lib/python3.5/site-packages/IPython/utils/py3compat.py in execfile(fname='/tmp/test_manhattan.py', glob={'In': [''], 'Out': {}, 'Parallel': <class 'sklearn.externals.joblib.parallel.Parallel'>, '_': '', '__': '', '___': '', '__builtin__': <module 'builtins' (built-in)>, '__builtins__': <module 'builtins' (built-in)>, '__doc__': 'Automatically created module for IPython interactive environment', '__file__': '/tmp/test_manhattan.py', ...}, loc={'In': [''], 'Out': {}, 'Parallel': <class 'sklearn.externals.joblib.parallel.Parallel'>, '_': '', '__': '', '___': '', '__builtin__': <module 'builtins' (built-in)>, '__builtins__': <module 'builtins' (built-in)>, '__doc__': 'Automatically created module for IPython interactive environment', '__file__': '/tmp/test_manhattan.py', ...}, compiler=<IPython.core.compilerop.CachingCompiler object>)
    181 
    182     def execfile(fname, glob, loc=None, compiler=None):
    183         loc = loc if (loc is not None) else glob
    184         with open(fname, 'rb') as f:
    185             compiler = compiler or compile
--> 186             exec(compiler(f.read(), fname, 'exec'), glob, loc)
        compiler = <IPython.core.compilerop.CachingCompiler object>
        f.read = <built-in method read of _io.BufferedReader object>
        fname = '/tmp/test_manhattan.py'
        glob = {'In': [''], 'Out': {}, 'Parallel': <class 'sklearn.externals.joblib.parallel.Parallel'>, '_': '', '__': '', '___': '', '__builtin__': <module 'builtins' (built-in)>, '__builtins__': <module 'builtins' (built-in)>, '__doc__': 'Automatically created module for IPython interactive environment', '__file__': '/tmp/test_manhattan.py', ...}
        loc = {'In': [''], 'Out': {}, 'Parallel': <class 'sklearn.externals.joblib.parallel.Parallel'>, '_': '', '__': '', '___': '', '__builtin__': <module 'builtins' (built-in)>, '__builtins__': <module 'builtins' (built-in)>, '__doc__': 'Automatically created module for IPython interactive environment', '__file__': '/tmp/test_manhattan.py', ...}
    187     
    188     # Refactor print statements in doctests.
    189     _print_statement_re = re.compile(r"\bprint (?P<expr>.*)$", re.MULTILINE)
    190     def _print_statement_sub(match):

...........................................................................
/tmp/test_manhattan.py in <module>()
      8 matrices1 = [csr_matrix(np.ones((5, 5)))]
      9 matrices2 = [csr_matrix(np.ones((5, 5)))]
     10 
     11 Parallel(n_jobs=2, max_nbytes=0)(
     12     delayed(manhattan_distances)(m1, m2)
---> 13     for m1, m2 in zip(matrices1, matrices2))
     14 
     15 
     16 
     17 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in __call__(self=Parallel(n_jobs=2), iterable=<generator object <genexpr>>)
    763             if pre_dispatch == "all" or n_jobs == 1:
    764                 # The iterable was consumed all at once by the above for loop.
    765                 # No need to wait for async callbacks to trigger to
    766                 # consumption.
    767                 self._iterating = False
--> 768             self.retrieve()
        self.retrieve = <bound method Parallel.retrieve of Parallel(n_jobs=2)>
    769             # Make sure that we get a last message telling us we are done
    770             elapsed_time = time.time() - self._start_time
    771             self._print('Done %3i out of %3i | elapsed: %s finished',
    772                         (len(self._output), len(self._output),

---------------------------------------------------------------------------
Sub-process traceback:
---------------------------------------------------------------------------
ValueError                                         Mon Dec  5 13:19:44 2016
PID: 25869           Python 3.5.2: /volatile/le243287/miniconda3/bin/python
...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in __call__(self=<sklearn.externals.joblib.parallel.BatchedCalls object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        self.items = [(<function manhattan_distances>, (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>), {})]
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/externals/joblib/parallel.py in <listcomp>(.0=<list_iterator object>)
    126     def __init__(self, iterator_slice):
    127         self.items = list(iterator_slice)
    128         self._size = len(self.items)
    129 
    130     def __call__(self):
--> 131         return [func(*args, **kwargs) for func, args, kwargs in self.items]
        func = <function manhattan_distances>
        args = (<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, <5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>)
        kwargs = {}
    132 
    133     def __len__(self):
    134         return self._size
    135 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise.py in manhattan_distances(X=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, Y=<5x5 sparse matrix of type '<class 'numpy.float6... stored elements in Compressed Sparse Row format>, sum_over_features=True, size_threshold=500000000.0)
    528         X = csr_matrix(X, copy=False)
    529         Y = csr_matrix(Y, copy=False)
    530         D = np.zeros((X.shape[0], Y.shape[0]))
    531         _sparse_manhattan(X.data, X.indices, X.indptr,
    532                           Y.data, Y.indices, Y.indptr,
--> 533                           X.shape[1], D)
        X.shape = (5, 5)
        D = array([[ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  ...0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.]])
    534         return D
    535 
    536     if sum_over_features:
    537         return distance.cdist(X, Y, 'cityblock')

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in sklearn.metrics.pairwise_fast._sparse_manhattan (sklearn/metrics/pairwise_fast.c:4688)()
     48                     if nom != 0:
     49                         res  += denom * denom / nom
     50                 result[i, j] = -res
     51 
     52 
---> 53 def _sparse_manhattan(floating1d X_data, int[:] X_indices, int[:] X_indptr,
     54                       floating1d Y_data, int[:] Y_indices, int[:] Y_indptr,
     55                       np.npy_intp n_features, double[:, ::1] D):
     56     """Pairwise L1 distances for CSR matrices.
     57 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview_cwrapper (sklearn/metrics/pairwise_fast.c:13277)()
    639 
    640 
    641 
    642 
    643 
--> 644 
    645 
    646 
    647 
    648 

...........................................................................
/home/le243287/dev/scikit-learn/sklearn/metrics/pairwise_fast.cpython-35m-x86_64-linux-gnu.so in View.MemoryView.memoryview.__cinit__ (sklearn/metrics/pairwise_fast.c:9512)()
    340 
    341 
    342 
    343 
    344 
--> 345 
    346 
    347 
    348 
    349 

ValueError: buffer source array is read-only
___________________________________________________________________________

```

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Maybe similar to #4772.

### Comment 2 ([user]):

I just ran into this using latest version of numpy from pip.

### Comment 3 ([user]):

There is a limitation of cython that typed memoryviews does not work with read-only data. ~~Maybe we can fix this in scikit-learn, PR more than welcome in this case.~~ **Edit**: quickly looking at the stacktrace, probably not.

### Comment 4 ([user]):

huh what solution are you proposing [user]?

### Comment 5 ([user]):

If you are controlling the Parallel object as in my snippet above, you can use max_nbytes=None to prevent the auto-memmapping. If you are not in control of the Parallel object, then tough luck, maybe we could fix it in scikit-learn by not using cython type memoryviews in `_sparse_manhattan`.

### Comment 6 ([user]):

Encountered this today with the `apply` function of Random Forest Classifier. Happens only for comparatively big datasets like mnist, not digits or iris.

### Comment 7 ([user]):

I just tested this issue with the master version of Cython using const fused memoryviews and the issue was resolved.

### Comment 8 ([user]):

Using sklearn 0.21.3, i run into this error when using DictionaryLearning when n_job>1 and a very large dataset. e.g.

```
dl = sklearn.decomposition.DictionaryLearning(int(1e2), n_jobs=1, alpha=1e-4, fit_algorithm='cd', verbose=2)
dl.fit(patches)
```

### Comment 9 ([user]):

This has bitten us within a GridSearchCV. 

The workaround suggested by [user] did a great job; we ended up having to subclass `joblib.LokyBackend`, hack its `configure` method to set `max_nbytes=None`, and then use the `joblib` facilities for setting the backend directly. Kind of a disaster, but it works.

## PR Review Comments

**[user]** on `sklearn/metrics/tests/test_pairwise.py`:

We need to use `sklearn.utils.parallel.Parallel` once the latest PR of 1.2.1 is in.

**[user]** on `sklearn/metrics/tests/test_pairwise.py`:

`delayed` should come from `parallel` and not `fixes` as well.

**[user]** on `sklearn/metrics/tests/test_pairwise.py`:

```suggestion
    # The following call was reporting as failing in #7981, but this must pass.
```

**[user]** on `sklearn/metrics/tests/test_pairwise.py`:

```suggestion
    # Joblib memory maps datasets which makes them read-only.
```

**[user]** on `sklearn/metrics/tests/test_pairwise.py`:

Let's not use `n_jobs=-1` in tests because running that test on a machine with 64 cores will start 64 Python interpreters that will import concurrently sklearn, numpy, scipy from disk which might slow down the machine for nothing (and make the test very slow to run).

```suggestion
    Parallel(n_jobs=2, max_nbytes=0)(
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
