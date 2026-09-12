# GH985_ray_22113: Fixed MRO for `DerivedActorClass` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ray-project/ray/issues/1234
- Repo: https://github.com/ray-project/ray

## Issue Description

<!--
General questions should be asked on the mailing list [email redacted].

Before submitting an issue, please fill out the following form.
-->

### System information
- **Ray installed from (source or binary)**: pip
- **Ray version**: 0.2.2
- **Python version**: 3.6.2

<!--
You can obtain the Ray version with

python -c "import ray; print(ray.__version__)"
-->

### Describe the problem

Ray fails to serialize self-reference objects (for example, Graph objects in networkx).

I think it is because ray always tries to use pyarrow first and does not catch `pyarrow.lib.ArrowNotImplementedError`, see

https://github.com/ray-project/ray/blob/e0360eb4298371e308cd266dd512befaa457ce24/python/ray/worker.py#L285-L289

After catching `pyarrow.lib.ArrowNotImplementedError`, we **should not** use `use_dict=True` as a workaround, because it will cause endless loop. A correct approach may be:

```python
            except (pyarrow.SerializationCallbackError, pyarrow.lib.ArrowNotImplementedError) as e:
                try:
                    if isinstance(e, pyarrow.lib.ArrowNotImplementedError):
                        e.example_object = value
                        raise e  # redirect to use cloudpickle
```

### Source code / logs
<!-- Include any logs or source code that would be helpful to diagnose the problem. If including tracebacks, please include the full traceback. Large logs and files should be attached. Try to provide a reproducible test case that is the bare minimum necessary to generate the problem. -->

```python
class Graph:
    def __init__(self):
        self.g = self

G = Graph()
ray.put(G)  # --> pyarrow.lib.ArrowNotImplementedError: This object exceeds the maximum recursion depth. It may contain itself recursively.

# another example

import networkx as nx
G = nx.Graph()
    
G.add_edges_from([(1, 2), (1, 3)])
G.add_node(1)
G.add_edge(1, 2)
G.add_node("spam")  # adds node "spam"
G.add_nodes_from("spam")  # adds 4 nodes: 's', 'p', 'a', 'm'
G.add_edge(3, 'm')
ray.put(G)  # --> pyarrow.lib.ArrowNotImplementedError: This object exceeds the maximum recursion depth. It may contain itself recursively.
```

[user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Can you try `ray.register_custom_serializer`? The following works for me.

```python
import ray
ray.init()

class Graph:
    def __init__(self):
        self.g = self

ray.register_custom_serializer(Graph, use_pickle=True)

G = Graph()
ray.put(G)
```

This is closely related to #319 and https://issues.apache.org/jira/browse/ARROW-1382.

A side comment. The original code worked for me in Python 2 because in Python 2 `Graph` is an old-style class and so we automatically fall back to Pickle anyway I think.

### Comment 2 ([user]):

Hm, so ideally we would like to serialize networkx graphs. Because they can be quite large, I am not sure if pickling is a good approach.

### Comment 3 ([user]):

Custom serializers/deserializers can be registered with the same approach. Not sure what the right one would be in this case, but just as a simple example, you could do something like

```python
import numpy as np
import ray

ray.init()

class Graph:
    def __init__(self, big_array):
        self.g = self
        self.big_array = big_array

def custom_graph_serializer(obj):
    return obj.big_array

def custom_graph_deserializer(serialized_obj):
    return Graph(serialized_obj)

ray.register_custom_serializer(Graph,
                               serializer=custom_graph_serializer,
                               deserializer=custom_graph_deserializer)

G = Graph(np.ones(100))
ray.put(G)
```

### Comment 4 ([user]):

Stale - please open new issue if still relevant

## PR Review Comments

**[user]** on `python/ray/actor.py`:

**Problem** - We cannot always delegate call to `cls.__init__` or `modified_cls.__init__`. Because if always delegate call to `cls.__init__` from here, then user defined class's `__init__` method will be ignore leading to issues like, #21868. If we always delegate call to `modified_cls.__init__` then it will allow inheriting from actor classes leading to failure of `test_actor_inheritance`. So, I have added this `if-else` check to figure out which `__init__` method should be called. If `"__module__"`, `"__qualname__"` and `"__init__"` are present in `args[-1]` then it would mean an actor class is being inherited so `cls.__init__` should be called. However, if no such signal is received in `args` then user defined class's `__init__` i.e., `modified_class.__init__` should be called.
cc: [user]

**[user]** on `python/ray/actor.py`:

The fix is not clear to me. Can you clarify what args is in this context? Also, why is an actor class being inherited if "__module__", "__qualname__" and "__init__" are in args[-1]?

Can you replace the test with one that is clearer?

**[user]** on `python/ray/actor.py`:

> Also, why is an actor class being inherited if "**module**", "**qualname**" and "**init**" are in args[-1]?

This is a pattern that I noticed. When I inherited an actor class, then there were 3 arguments, ("DerivedClassName", "ModuleOfTheDerivedClass",  "<A dict having module, qualname and init>"). If you notice the signature of `ActorClass.__init__`, then it matches with these 3 arguments. However, when you simply call `cls(<arguments>)` (as done in #21868), then the above pattern is not observed which means the `ActorClass` is not inherited. I know this is somewhat hackish, but let me know if Python has any other technique to figure if some class is inherited or not.

The other approaches I tried included, checking `DerivedActorClass.__subclasses__` but that doesn't work. I am not sure if there is any other way to figure out if the user is inheriting an actor class or simply calling the `__init__` method from a `classmethod`.

**[user]** on `python/ray/actor.py`:

So I noted that `ActorClass.__init__` will anyway raise a `TypeError` whenever it will be inherited. To exactly figure out whether the exception is due to inheritance of `ActorClass`, I created a new class `ActorClassInheritanceException(TypeError)`. Now, whenever this will be raised, then `DerivedActorClass` will get a clear signal about inheritance of `ActorClass`. In other cases, it will be safe to conclude (AFAICT) that user called `__init__` method of their class and we will proceed normally. IMHO, this is a better and more robust solution which just depends on a simple signal i.e., raising a particular exception in a specific event. It doesn't matter how inheritance is prevented as in the end we just need to raise `ActorClassInheritanceException` and all other code will be able to detect that easily.

[user] Does this look good?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
