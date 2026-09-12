# GH1033_ray_23187: `map` and `map_unordered` cancel previous tasks before submitting new ones — Full Specification (Planner Only)

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

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
