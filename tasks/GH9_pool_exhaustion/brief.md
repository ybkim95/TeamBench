# GH9: Fix Connection Pool Exhaustion on Query Errors

The database connection pool becomes exhausted after repeated query failures.
Users report that after several failed queries, the application hangs
indefinitely on new database operations.

Fix the connection management in `db_pool.py`.
