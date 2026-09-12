"""
Circular FK loader for customers and orders with circular FK.
BUG: Enables FK constraints before loading data, so the first table loaded
always fails (it references the not-yet-loaded second table).

Fix: Load all data with PRAGMA foreign_keys = OFF, then enable FK checks
and run a manual integrity verification query to catch violations.
"""
import pandas as pd
import json
import sqlite3

df_a = pd.read_csv("data/customers.csv")
df_b = pd.read_csv("data/orders.csv")

conn = sqlite3.connect("output.db")

# BUG: FK constraints enabled BEFORE loading — causes failure on circular refs
conn.execute("PRAGMA foreign_keys = ON")  # BUG: should be OFF during load

conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        name TEXT,
        amount REAL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        first_order_id INTEGER,
        name TEXT,
        value REAL,
        FOREIGN KEY (first_order_id) REFERENCES orders(order_id)
    )
""")

load_errors = 0
for _, row in df_b.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?)",
            (int(row["order_id"]), int(row["customer_id"]), row["name"], float(row["amount"]))
        )
    except Exception:
        load_errors += 1

for _, row in df_a.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO customers VALUES (?, ?, ?, ?)",
            (int(row["customer_id"]), int(row["first_order_id"]), row["name"], float(row["value"]))
        )
    except Exception:
        load_errors += 1

conn.commit()

count_a = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
count_b = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
conn.close()

results = {
    "customers_rows_loaded": count_a,
    "orders_rows_loaded": count_b,
    "load_errors": load_errors,
    "deferred_fk_used": False,  # BUG: should be True
    "fk_violations_detected": 0,  # BUG: should detect violations after load
    "load_succeeded": count_a == 22 and count_b == 28,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Loaded: customers={count_a}, orders={count_b}, errors={load_errors}")
