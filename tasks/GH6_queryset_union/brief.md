# GH6: Fix QuerySet Filtering After Set Operations

The ORM's QuerySet has a bug where filtering operations (exclude, filter)
applied after set operations (union, intersection) are silently ignored.
Users report that `.exclude()` calls after `.union()` have no effect.

Fix the query builder in `queryset.py`.
