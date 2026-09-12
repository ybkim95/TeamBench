# GH5: Fix Recursive Model Validation

The data validation library fails to validate self-referential models
beyond depth 2. Nested structures like tree nodes lose their children
at deeper levels.

Fix the schema resolution in `validator.py`.
