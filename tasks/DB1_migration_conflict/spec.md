# DB1_migration_conflict: Migration Conflict Resolution — Full Specification (Planner Only)

            ## Overview

            Two feature branches (`feature/payments` and `feature/analytics`) were developed in
            parallel for the `ShopApp` ecommerce application. Both branches
            produced SQL migrations that conflict with each other. The executor must
            resolve the conflicts so the migrations can be applied cleanly to produce
            the correct final schema.

            There are **4 conflicts** to resolve. The executor only receives
            the brief; this spec provides the full analysis.

            ## File Structure

            ```
            migrations/
              0001_baseline.sql                              ← correct, do not modify
              0006_branch_a_rename_col.sql          ← from feature/payments (wins on conflict)
              0006_branch_b_add_analytics.sql       ← CONFLICT: same seq# as branch A
              0007_branch_b_add_analytics.sql   ← resolved version (already present)
              0008_branch_a_add_index.sql            ← branch A index (keep)
              0008_branch_b_add_index.sql            ← CONFLICT: duplicate index (delete)
            migration_policy.md                             ← authoritative conflict resolution rules
            apply_migrations.py                             ← helper to apply migrations to SQLite
            verify_schema.py                                ← schema verification script
            ```

            ## Migration Policy

            - **Branch priority:** `feature/payments` > `feature/analytics`
            - **Merge order:** baseline → `feature/payments` migrations → `feature/analytics` migrations
            - **On sequence collision:** the lower-priority branch's file is renumbered
            - **On column reference conflict:** update to use the name from the higher-priority branch
            - **On index name collision:** keep the higher-priority branch's index; delete the other

            ## Conflict Analysis

            | # | Type | Problem | Resolution |
            |---|------|---------|------------|
            | C1 | sequence_collision | Both branches use `0006_*.sql` | Rename `feature/analytics`'s file to `0007_branch_b_add_analytics.sql` |
| C2 | column_rename_conflict | `feature/analytics` references `customer_name` after `feature/payments` renames it | Update `order_metrics` DDL to use `full_name` |
| C3 | foreign_key_dep | Analytics table FK would reference stale column name | Apply `feature/payments` rename before `feature/analytics` analytics table |
| C4 | index_name_collision | Both branches create index `idx_orders_customer` | Delete `feature/analytics`'s index file; keep `feature/payments`'s |

            ### Conflict Details

### Conflict C1 — Sequence Number Collision

**Files:** `0006_branch_a_rename_col.sql` and
`0006_branch_b_add_analytics.sql`

**Root cause:** Both branches were cut from the same baseline and
independently chose sequence number `0006`. Applying both
in the same database will fail because the migration runner processes
them in lexicographic order and can't determine which is authoritative.

**Resolution:** Per policy, `feature/payments` wins. The `feature/analytics` file
`0006_branch_b_add_analytics.sql` must be **renamed** to
`0007_branch_b_add_analytics.sql`.

The corrected file is already present as
`0007_branch_b_add_analytics.sql` — delete the conflicting
`0006_branch_b_add_analytics.sql`.

### Conflict C2 — Column Rename Reference Conflict

**Files:** `0006_branch_a_rename_col.sql` renames `customer_name` → `full_name`.
`0006_branch_b_add_analytics.sql` creates `order_metrics` with
a column called `customer_name` (the stale name).

**Root cause:** Branch B was developed against the old schema and still
references `customer_name`. After branch A's rename is applied, `customer_name`
no longer exists as a column in the secondary table. Branch B's analytics
table uses the old name inconsistently.

**Resolution:** The corrected file (`0007_branch_b_add_analytics.sql`)
already uses `full_name`. Delete the conflicting original.

### Conflict C3 — Foreign Key Dependency Order

**Issue:** The analytics table must be created **after** the column rename
is complete. If `feature/analytics`'s migration runs before `feature/payments`'s rename,
the FK reference will point to a non-existent column name.

**Resolution:** Ensure `feature/payments` migrations are fully applied before
`feature/analytics` migrations. This is already satisfied by the sequence numbering
after resolving C1 — `0006` (branch A) runs before `0007` (branch B).

### Conflict C4 — Index Name Collision

**Files:** `0008_branch_a_add_index.sql` and
`0008_branch_b_add_index.sql` both create an index
named `idx_orders_customer`.

**Root cause:** Both branches independently chose the same index name.
Applying both would fail with "index already exists".

**Resolution:** Per policy, `feature/payments` wins. Delete
`0008_branch_b_add_index.sql`.
Keep `0008_branch_a_add_index.sql`.

## Expected Final Schema

After applying all resolved migrations, the database must have:

### `customers` table
- Column `full_name` (renamed from `customer_name`) — **not** `customer_name`
- All other baseline columns unchanged

### `orders` table
- All baseline columns present
- New column `region` (added by `feature/payments`)

### `order_metrics` table
- Column `full_name` (not `customer_name`)
- FK reference to `orders`

### Indexes
- `idx_orders_customer` exists (from `feature/payments`)

## Acceptance Criteria

1. No two migration files have the same sequence number prefix
2. `python apply_migrations.py schema.db` completes without errors
3. `python verify_schema.py schema.db` reports all checks passed
4. `customers.full_name` exists; `customers.customer_name` does not
5. `orders.region` exists
6. `order_metrics` table references `full_name` not `customer_name`
