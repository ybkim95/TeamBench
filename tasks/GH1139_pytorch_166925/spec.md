# GH1139_pytorch_166925: [dynamo] fix error_on_graph_break bug where non-empty checkpoint results in unwanted graph break resumption — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/166589
- Repo: https://github.com/pytorch/pytorch

## Issue Description

This test fails since compilation succeeds when it should not, thus hiding a graph break.
```python
    def test_error_on_graph_break_nonempty_checkpoint(self):
        cnts = torch._dynamo.testing.CompileCounter()

        @torch.compile(backend=cnts)
        def fn(x):
            x = x + 1
            x = x + 1
            x = x + 1
            with torch._dynamo.error_on_graph_break(True):
                torch._dynamo.graph_break()
            return x + 1

        with self.assertRaises(Unsupported):
            fn(torch.ones(3))

        self.assertEqual(cnts.frame_count, 0)
```

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
