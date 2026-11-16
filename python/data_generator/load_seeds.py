"""Load the reference (dictionary) tables from ``seeds/reference_data.py``.

The loader is idempotent: running it again never creates duplicates and never touches
transactional tables. Where the schema has a UNIQUE constraint the insert uses
``ON CONFLICT DO NOTHING``. ``salespersons`` has no natural unique key in the schema (and the
schema must not be changed), so the loader inserts a manager only if no row with the same
first name, last name and region exists yet.

Dependent tables are loaded after their parents: regions -> cities, categories ->
subcategories. A reference to an unknown parent is an error, not a silent skip.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parent))

from common import GenerationError  # noqa: E402
from db import fetch_name_map, get_connection  # noqa: E402
from seeds.reference_data import (  # noqa: E402
    BRANDS,
    CATEGORIES,
    CITIES,
    CUSTOMER_TYPES,
    ORDER_STATUSES,
    PRODUCT_STATUSES,
    REGIONS,
    RETURN_REASONS,
    SALES_CHANNELS,
    SALESPERSONS,
    SUBCATEGORIES,
    SUPPLIERS,
)

# Simple dictionaries: (table, seed rows, seed key, column)
_SIMPLE_TABLES = (
    ("regions", REGIONS, "region_name", "region_name"),
    ("customer_types", CUSTOMER_TYPES, "customer_type_name", "type_name"),
    ("categories", CATEGORIES, "category_name", "category_name"),
    ("brands", BRANDS, "brand_name", "brand_name"),
    ("product_statuses", PRODUCT_STATUSES, "status_name", "status_name"),
    ("sales_channels", SALES_CHANNELS, "channel_name", "channel_name"),
    ("order_statuses", ORDER_STATUSES, "status_name", "status_name"),
)


def _lookup(mapping: dict[str, int], key: str, parent: str, child: str) -> int:
    """Resolve a parent id or fail with a clear message."""
    try:
        return mapping[key]
    except KeyError:
        raise GenerationError(f"Seed '{child}' references unknown {parent} '{key}'.") from None


def _salesperson_contacts(seed: dict[str, Any]) -> tuple[str, str]:
    """Deterministic e-mail and phone for a seeded manager (synthetic, reserved domain)."""
    email = f"{seed['first_name']}.{seed['last_name']}@autoparts-distribution.example".lower()
    digits = "".join(ch for ch in seed.get("employee_code", "0") if ch.isdigit()) or "0"
    return email, f"+38050{int(digits):07d}"


def load_reference_data(conn: Any | None = None) -> dict[str, int]:
    """Insert all reference data and return the number of rows per table afterwards.

    If ``conn`` is given the caller owns the transaction; otherwise a connection is opened
    and committed here.
    """
    if conn is None:
        with get_connection() as own_conn:
            return load_reference_data(own_conn)

    print("Loading reference data ...")
    with conn.cursor() as cur:
        for table, rows, key, column in _SIMPLE_TABLES:
            cur.executemany(
                f"INSERT INTO {table} ({column}) VALUES (%s) ON CONFLICT ({column}) DO NOTHING",
                [(row[key],) for row in rows],
            )

        regions = fetch_name_map(cur, "regions", "region_id", "region_name")
        cur.executemany(
            "INSERT INTO cities (city_name, region_id) VALUES (%s, %s) "
            "ON CONFLICT (region_id, city_name) DO NOTHING",
            [(row["city_name"], _lookup(regions, row["region_name"], "region", row["city_name"]))
             for row in CITIES],
        )

        categories = fetch_name_map(cur, "categories", "category_id", "category_name")
        cur.executemany(
            "INSERT INTO subcategories (subcategory_name, category_id) VALUES (%s, %s) "
            "ON CONFLICT (category_id, subcategory_name) DO NOTHING",
            [(row["subcategory_name"],
              _lookup(categories, row["category_name"], "category", row["subcategory_name"]))
             for row in SUBCATEGORIES],
        )

        cur.executemany(
            "INSERT INTO suppliers (supplier_name, country, is_active) VALUES (%s, %s, %s) "
            "ON CONFLICT (supplier_name) DO NOTHING",
            [(row["supplier_name"], row["country"], row.get("status", "Active") == "Active")
             for row in SUPPLIERS],
        )

        cur.executemany(
            "INSERT INTO return_reasons (reason_name, is_active) VALUES (%s, TRUE) "
            "ON CONFLICT (reason_name) DO NOTHING",
            [(row["reason_name"],) for row in RETURN_REASONS],
        )

        # salespersons: no UNIQUE in the schema -> guard with NOT EXISTS (idempotent).
        for row in SALESPERSONS:
            region_id = _lookup(regions, row["region_name"], "region", row["last_name"])
            email, phone = _salesperson_contacts(row)
            cur.execute(
                """
                INSERT INTO salespersons (first_name, last_name, region_id, email, phone, hire_date, is_active)
                SELECT %(first)s::varchar, %(last)s::varchar, %(region)s::int, %(email)s::varchar, %(phone)s::varchar,
                       %(hired)s::date, %(active)s::boolean
                WHERE NOT EXISTS (
                    SELECT 1 FROM salespersons
                    WHERE first_name = %(first)s::varchar AND last_name = %(last)s::varchar
                      AND region_id = %(region)s::int
                )
                """,
                {
                    "first": row["first_name"], "last": row["last_name"], "region": region_id,
                    "email": email, "phone": phone,
                    "hired": date.fromisoformat(row["hire_date"]),
                    "active": row.get("status", "Active") == "Active",
                },
            )

        counts: dict[str, int] = {}
        for table in ("regions", "cities", "customer_types", "salespersons", "categories",
                      "subcategories", "brands", "suppliers", "product_statuses",
                      "sales_channels", "order_statuses", "return_reasons"):
            cur.execute(f"SELECT count(*) FROM {table}")
            counts[table] = int(cur.fetchone()[0])

    print("Reference data loaded: " + ", ".join(f"{t}={n}" for t, n in counts.items()))
    return counts


if __name__ == "__main__":
    load_reference_data()
