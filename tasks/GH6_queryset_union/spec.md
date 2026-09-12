# GH6: QuerySet Filtering After Set Operations — Full Specification

## Issue

`qs1.union(qs2).exclude(status="deleted")` returns results that **include deleted
items**. The `.exclude()` call is silently dropped and has no effect on the
final result. The same bug affects `.filter()` after `.union()`,
`.intersection()`, and `.difference()`.

Reported upstream: https://code.djangoproject.com/ticket/28293
Related: https://code.djangoproject.com/ticket/29694

## Root Cause

In `QuerySet._filter_or_exclude()`, there is a guard clause that fires when
the queryset was produced by a set operation (union / intersection /
difference). At that point `self.query.combinator` is set to a non-empty
string ("UNION", "INTERSECT", or "EXCEPT").

The guard reads:

```python
def _filter_or_exclude(self, negate, **kwargs):
    # Guard: combinators cannot be filtered directly
    if self.query.combinator:
        return self._clone()   # ← silently returns unchanged clone
    ...
```

The original rationale was that SQL combinators wrap their operands in a
subquery, so a naive WHERE clause appended to the inner query would be
syntactically invalid. The author assumed filtering was simply impossible and
made the guard a no-op.

**The assumption is wrong.** The filter *can* be applied — it just must target
the *outer* wrapping query, not the inner combinator query. The correct fix is
to promote the combinator result to a subquery and apply the filter to a new
outer queryset that selects from it.

## The Fix

In `_filter_or_exclude()`, when `self.query.combinator` is set:

1. Treat `self` as a subquery source.
2. Create a new `Query` whose `subquery` field holds the current query.
3. Apply the filter / exclude condition to that new outer query.
4. Return a `QuerySet` wrapping the outer query.

The generated SQL should look like:

```sql
-- Before fix (broken — exclude is silently dropped):
SELECT * FROM users WHERE id = 1
UNION
SELECT * FROM users WHERE id = 2

-- After fix (correct — exclude wraps the union):
SELECT * FROM (
    SELECT * FROM users WHERE id = 1
    UNION
    SELECT * FROM users WHERE id = 2
) AS subq WHERE NOT (status = 'deleted')
```

## Constraints

- `union()`, `intersection()`, and `difference()` themselves are **CORRECT**
  and must not be modified.
- SQL generation for basic queries (no combinators) must be **unchanged**.
- `.filter()` after set operations must also be fixed (same code path).
- The fix lives entirely in `_filter_or_exclude()`; no other public methods
  need to change.

## Expected Behaviour After Fix

```python
db = Database()
db.create_table("users", [
    {"id": 1, "name": "Alice", "status": "active"},
    {"id": 2, "name": "Bob",   "status": "deleted"},
    {"id": 3, "name": "Carol", "status": "active"},
])

qs1 = QuerySet("users").filter(id=1)
qs2 = QuerySet("users").filter(id__in=[2, 3])

# Bug: before fix this returns all three rows
result = qs1.union(qs2).exclude(status="deleted")._execute(db)
assert len(result) == 2                          # Bob must be excluded
assert all(r["status"] != "deleted" for r in result)

# filter() must work the same way
result2 = qs1.union(qs2).filter(status="active")._execute(db)
assert len(result2) == 2
```
