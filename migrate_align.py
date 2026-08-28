"""Migración idempotente: alinea el esquema de Neon con core/models.py.

Añade las columnas que faltan en la BD (detectadas por comparación con los
modelos). Es seguro ejecutarlo varias veces: comprueba information_schema
antes de cada ALTER.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine

def column_exists(conn, table, column):
    row = conn.execute(
        text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).scalar()
    return row > 0

ALTERS = [
    ("products", "type", "ALTER TABLE products ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT 'termined'"),
    ("sale_orders", "payment_status", "ALTER TABLE sale_orders ADD COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'pending'"),
    ("purchase_orders", "payment_status", "ALTER TABLE purchase_orders ADD COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'pending'"),
    ("purchase_orders", "due_date", "ALTER TABLE purchase_orders ADD COLUMN due_date TIMESTAMPTZ"),
    ("production_orders", "produced_quantity", "ALTER TABLE production_orders ADD COLUMN produced_quantity INTEGER NOT NULL DEFAULT 0"),
    ("production_orders", "total_cost", "ALTER TABLE production_orders ADD COLUMN total_cost FLOAT NOT NULL DEFAULT 0.0"),
    ("production_orders", "machine_time_min", "ALTER TABLE production_orders ADD COLUMN machine_time_min FLOAT NOT NULL DEFAULT 0.0"),
]

applied, skipped = [], []

with engine.begin() as conn:
    for table, column, stmt in ALTERS:
        if column_exists(conn, table, column):
            skipped.append(f"{table}.{column}")
        else:
            conn.execute(text(stmt))
            applied.append(f"{table}.{column}")

print("APPLIED:", applied)
print("SKIPPED (ya existía):", skipped)
