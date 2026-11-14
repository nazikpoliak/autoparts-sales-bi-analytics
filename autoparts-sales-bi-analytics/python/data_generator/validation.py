"""Read-only quality validation of a generated database.

Every check is a single ``SELECT`` returning one number. The whole run happens inside a
``READ ONLY`` transaction that is rolled back, so it cannot modify data. Use it right after
the generation (``python main.py validate``) or at any time later.

Severities
----------
* ``ERROR`` - the data is wrong (broken rule, ERD mismatch); the command exits with code 1;
* ``WARN``  - the data is valid but looks unrealistic or misses a project target;
* ``INFO``  - a metric for the analyst, never fails.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

sys.path.append(str(Path(__file__).resolve().parent))

from config import TARGET_MINIMUMS, GenerationConfig  # noqa: E402

# Columns of the 18 tables exactly as in database/schema/01_schema.sql (the ERD).
EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "regions": ("region_id", "region_name"),
    "cities": ("city_id", "region_id", "city_name"),
    "customer_types": ("customer_type_id", "type_name"),
    "customers": ("customer_id", "customer_type_id", "city_id", "customer_name", "tax_id", "phone", "email", "address", "registration_date", "is_active"),
    "salespersons": ("salesperson_id", "region_id", "first_name", "last_name", "email", "phone", "hire_date", "is_active"),
    "sales_channels": ("sales_channel_id", "channel_name"),
    "order_statuses": ("order_status_id", "status_name"),
    "brands": ("brand_id", "brand_name"),
    "categories": ("category_id", "category_name"),
    "subcategories": ("subcategory_id", "category_id", "subcategory_name"),
    "suppliers": ("supplier_id", "supplier_name", "contact_name", "phone", "email", "country", "is_active"),
    "product_statuses": ("product_status_id", "status_name"),
    "products": ("product_id", "subcategory_id", "brand_id", "supplier_id", "product_status_id", "sku", "product_name", "description", "unit_of_measure", "purchase_price", "standard_sale_price", "weight_kg", "created_at"),
    "orders": ("order_id", "customer_id", "salesperson_id", "sales_channel_id", "order_status_id", "order_date", "customer_reference", "notes"),
    "order_items": ("order_item_id", "order_id", "product_id", "quantity", "unit_sale_price", "unit_cost", "discount_amount"),
    "return_reasons": ("return_reason_id", "reason_name", "description", "is_active"),
    "returns": ("return_id", "order_id", "customer_id", "return_reason_id", "return_date", "notes"),
    "return_items": ("return_item_id", "return_id", "order_item_id", "product_id", "quantity", "refund_unit_price"),
}


@dataclass(frozen=True)
class Check:
    """One SQL check. ``expect`` is ``("zero",)``, ``("range", low, high)`` or ``("info",)``."""

    code: str
    name: str
    severity: str
    sql: str
    expect: tuple = ("zero",)


@dataclass(frozen=True)
class CheckResult:
    code: str
    name: str
    severity: str
    value: Any
    expected: str
    passed: bool


_LINE_NET = "(oi.quantity * oi.unit_sale_price - oi.discount_amount)"

# Parameters: %(end)s = end of the generation period (timestamp)
SQL_CHECKS: tuple[Check, ...] = (
    # ---- referential logic that foreign keys alone cannot enforce
    Check("INT01", "Return customer differs from order customer", "ERROR",
          "SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id WHERE r.customer_id <> o.customer_id"),
    Check("INT02", "Return item product differs from order item product", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id "
          "WHERE ri.product_id <> oi.product_id"),
    Check("INT03", "Return item belongs to another order than its return", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN returns r ON r.return_id = ri.return_id "
          "JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE oi.order_id <> r.order_id"),
    Check("INT04", "Orders without lines", "ERROR",
          "SELECT count(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id)"),
    Check("INT05", "Returns without lines", "ERROR",
          "SELECT count(*) FROM returns r WHERE NOT EXISTS (SELECT 1 FROM return_items ri WHERE ri.return_id = r.return_id)"),
    # ---- duplicates
    Check("DUP01", "Duplicate customer names", "ERROR",
          "SELECT count(*) FROM (SELECT customer_name FROM customers GROUP BY 1 HAVING count(*) > 1) t"),
    Check("DUP02", "Duplicate customer e-mails or phones", "ERROR",
          "SELECT (SELECT count(*) FROM (SELECT email FROM customers GROUP BY 1 HAVING count(*) > 1) a) "
          "+ (SELECT count(*) FROM (SELECT phone FROM customers GROUP BY 1 HAVING count(*) > 1) b)"),
    Check("DUP03", "Duplicate product names", "ERROR",
          "SELECT count(*) FROM (SELECT product_name FROM products GROUP BY 1 HAVING count(*) > 1) t"),
    Check("DUP04", "Duplicate salespersons (name + region)", "ERROR",
          "SELECT count(*) FROM (SELECT first_name, last_name, region_id FROM salespersons GROUP BY 1, 2, 3 HAVING count(*) > 1) t"),
    Check("DUP05", "Same product twice in one order", "ERROR",
          "SELECT count(*) FROM (SELECT order_id, product_id FROM order_items GROUP BY 1, 2 HAVING count(*) > 1) t"),
    Check("DUP06", "More than one return per order", "ERROR",
          "SELECT count(*) FROM (SELECT order_id FROM returns GROUP BY 1 HAVING count(*) > 1) t"),
    # ---- dates
    Check("DAT01", "Orders dated before customer registration", "ERROR",
          "SELECT count(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_date::date < c.registration_date"),
    Check("DAT02", "Orders dated in the future (after the period end)", "ERROR",
          "SELECT count(*) FROM orders WHERE order_date >= %(end)s"),
    Check("DAT03", "Orders dated before the salesperson was hired", "ERROR",
          "SELECT count(*) FROM orders o JOIN salespersons s ON s.salesperson_id = o.salesperson_id WHERE o.order_date::date < s.hire_date"),
    Check("DAT04", "Products sold before they were created", "ERROR",
          "SELECT count(*) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id "
          "JOIN products p ON p.product_id = oi.product_id WHERE o.order_date < p.created_at"),
    Check("DAT05", "Returns not later than the order", "ERROR",
          "SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id WHERE r.return_date <= o.order_date"),
    Check("DAT06", "Returns dated in the future (after the period end)", "ERROR",
          "SELECT count(*) FROM returns WHERE return_date >= %(end)s"),
    Check("DAT07", "Registration dates in the future", "ERROR",
          "SELECT count(*) FROM customers WHERE registration_date >= (%(end)s)::date"),
    Check("DAT08", "Churned (inactive) customers ordering in the last 60 days", "ERROR",
          "SELECT count(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id "
          "WHERE NOT c.is_active AND o.order_date >= (%(end)s)::timestamp - interval '60 days'"),
    # ---- prices, discounts, totals
    Check("PRC01", "Non-positive sale price or cost, or non-positive quantity", "ERROR",
          "SELECT count(*) FROM order_items WHERE unit_sale_price <= 0 OR unit_cost <= 0 OR quantity <= 0"),
    Check("PRC02", "Fractional quantities (units are whole pieces)", "ERROR",
          "SELECT count(*) FROM order_items WHERE quantity <> trunc(quantity)"),
    Check("PRC03", "Discount above the line amount or negative", "ERROR",
          "SELECT count(*) FROM order_items WHERE discount_amount < 0 OR discount_amount > quantity * unit_sale_price"),
    Check("PRC04", "Lines sold below cost after discount", "ERROR",
          "SELECT count(*) FROM order_items WHERE quantity * unit_sale_price - discount_amount < quantity * unit_cost"),
    Check("PRC05", "Standard sale price below purchase price", "ERROR",
          "SELECT count(*) FROM products WHERE standard_sale_price < purchase_price"),
    Check("PRC06", "Orders with non-positive total (lines minus discounts)", "ERROR",
          "SELECT count(*) FROM (SELECT order_id FROM order_items GROUP BY 1 HAVING sum(quantity * unit_sale_price - discount_amount) <= 0) t"),
    Check("PRC07", "Discount above 25% of the line", "WARN",
          "SELECT count(*) FROM order_items WHERE discount_amount > 0.25 * quantity * unit_sale_price"),
    # ---- returns
    Check("RET01", "Returned quantity above the sold quantity", "ERROR",
          "SELECT count(*) FROM (SELECT oi.order_item_id FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id "
          "GROUP BY oi.order_item_id, oi.quantity HAVING sum(ri.quantity) > oi.quantity) t"),
    Check("RET02", "Order line returned more than once", "ERROR",
          "SELECT count(*) FROM (SELECT order_item_id FROM return_items GROUP BY 1 HAVING count(*) > 1) t"),
    Check("RET03", "Return line quantity differs from the sold quantity (full-return rule)", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.quantity <> oi.quantity"),
    Check("RET04", "Refund above what the customer paid for the line", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id "
          "WHERE ri.quantity * ri.refund_unit_price > " + _LINE_NET),
    Check("RET05", "Refund unit price above the sale unit price", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id "
          "WHERE ri.refund_unit_price > oi.unit_sale_price"),
    Check("RET06", "Refund ignores the discount (more than 1 cent per unit off the net unit price)", "ERROR",
          "SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id "
          "WHERE (" + _LINE_NET + " / oi.quantity) - ri.refund_unit_price > 0.01 OR ri.refund_unit_price < 0"),
    Check("RET07", "Returns for orders that are not Completed", "ERROR",
          "SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id "
          "JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name <> 'Completed'"),
    # ---- statuses and relationships
    Check("STA01", "Unfinished orders older than 60 days", "ERROR",
          "SELECT count(*) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id "
          "WHERE s.status_name NOT IN ('Completed', 'Cancelled') AND o.order_date < (%(end)s)::timestamp - interval '60 days'"),
    Check("STA02", "Active-status products never sold", "INFO",
          "SELECT count(*) FROM products p JOIN product_statuses s ON s.product_status_id = p.product_status_id "
          "WHERE s.status_name = 'Active' AND NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id)",
          ("info",)),
    # ---- realism (distribution) metrics
    Check("REAL01", "Share of Completed orders, %", "WARN",
          "SELECT round(100.0 * count(*) FILTER (WHERE s.status_name = 'Completed') / nullif(count(*), 0), 1) "
          "FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id", ("range", 85, 95)),
    Check("REAL02", "Orders handled by a manager of the customer's region, %", "WARN",
          "SELECT round(100.0 * count(*) FILTER (WHERE sp.region_id = ci.region_id) / nullif(count(*), 0), 1) "
          "FROM orders o JOIN salespersons sp ON sp.salesperson_id = o.salesperson_id "
          "JOIN customers c ON c.customer_id = o.customer_id JOIN cities ci ON ci.city_id = c.city_id", ("range", 70, 100)),
    Check("REAL03", "Share of products that make 80% of revenue, %", "WARN",
          "WITH p AS (SELECT oi.product_id, sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) AS rev "
          "FROM order_items oi JOIN orders o ON o.order_id = oi.order_id "
          "JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed' GROUP BY 1), "
          "r AS (SELECT product_id, rev, sum(rev) OVER (ORDER BY rev DESC, product_id) AS cum, sum(rev) OVER () AS tot, "
          "count(*) OVER () AS n FROM p) "
          "SELECT round(100.0 * count(*) FILTER (WHERE cum - rev < 0.8 * tot) / max(n), 1) FROM r", ("range", 8, 40)),
    Check("REAL04", "Share of customers placing 80% of orders, %", "WARN",
          "WITH c AS (SELECT customer_id, count(*) AS n FROM orders GROUP BY 1), "
          "r AS (SELECT n, sum(n) OVER (ORDER BY n DESC, customer_id) AS cum, sum(n) OVER () AS tot, count(*) OVER () AS cnt FROM c) "
          "SELECT round(100.0 * count(*) FILTER (WHERE cum - n < 0.8 * tot) / max(cnt), 1) FROM r", ("range", 15, 55)),
    Check("REAL05", "Gross margin on Completed orders, %", "WARN",
          "SELECT round(100.0 * sum(oi.quantity * (oi.unit_sale_price - oi.unit_cost) - oi.discount_amount) "
          "/ nullif(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 0), 1) "
          "FROM order_items oi JOIN orders o ON o.order_id = oi.order_id "
          "JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed'", ("range", 12, 40)),
    Check("REAL06", "Average lines per order", "INFO",
          "SELECT round(count(*)::numeric / nullif((SELECT count(*) FROM orders), 0), 2) FROM order_items", ("info",)),
    Check("REAL07", "Months between first and last order", "WARN",
          "SELECT round((max(order_date)::date - min(order_date)::date) / 30.4375, 1) FROM orders", ("range", 24, 36)),
)


def _plain(value: Any) -> Any:
    """Decimal -> int/float so values compare and print naturally."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _check_expectation(expect: tuple, value: Any) -> tuple[bool, str]:
    if value is None:
        return False, "a value"
    if expect[0] == "zero":
        return value == 0, "0"
    if expect[0] == "range":
        return expect[1] <= value <= expect[2], f"{expect[1]}..{expect[2]}"
    return True, "-"


def _structure_results(cur: Any) -> list[CheckResult]:
    """Tables and columns of the database must equal the ERD / SQL schema."""
    cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'")
    actual: dict[str, set[str]] = {}
    for table, column in cur.fetchall():
        actual.setdefault(table, set()).add(column)
    missing_tables = sorted(set(EXPECTED_COLUMNS) - set(actual))
    diffs = [f"{t}: -{sorted(set(c) - actual[t])} +{sorted(actual[t] - set(c))}"
             for t, c in EXPECTED_COLUMNS.items() if t in actual and set(c) != actual[t]]
    return [
        CheckResult("STR01", "Tables missing compared with the ERD", "ERROR", len(missing_tables), "0",
                    not missing_tables),
        CheckResult("STR02", "Tables whose columns differ from the ERD", "ERROR", len(diffs), "0", not diffs),
    ]


def _count_results(cur: Any, cfg: GenerationConfig | None) -> list[CheckResult]:
    """Row counts versus generation parameters (ERROR) and project minimums (WARN)."""
    tables = ("customers", "products", "orders", "order_items", "returns", "return_items", "brands",
              "categories", "subcategories", "salespersons")
    counts: dict[str, int] = {}
    for table in tables:
        cur.execute(f"SELECT count(*) FROM {table}")
        counts[table] = int(cur.fetchone()[0])
    results: list[CheckResult] = []
    if cfg is not None:
        for table, wanted in (("customers", cfg.customers), ("products", cfg.products), ("orders", cfg.orders)):
            results.append(CheckResult(f"VOL-{table}", f"{table} count equals the generation parameter", "ERROR",
                                       counts[table], str(wanted), counts[table] == wanted))
        cur.execute("SELECT count(*) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id "
                    "WHERE s.status_name = 'Completed'")
        completed = int(cur.fetchone()[0])
        expected_returns = round(cfg.return_rate * completed)
        low, high = int(expected_returns * 0.85), int(expected_returns * 1.15) + 1
        results.append(CheckResult("VOL-returns", "returns count follows return_rate of Completed orders", "ERROR",
                                   counts["returns"], f"{low}..{high}", low <= counts["returns"] <= high))
    for table, minimum in TARGET_MINIMUMS.items():
        results.append(CheckResult(f"TGT-{table}", f"{table} >= project target", "WARN", counts[table],
                                   f">= {minimum}", counts[table] >= minimum))
    return results


def run_validation(conn: Any, cfg: GenerationConfig | None = None) -> list[CheckResult]:
    """Run every check in a read-only transaction and return the results."""
    end = (cfg.end_date if cfg else None)
    results: list[CheckResult] = []
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        if end is None:  # no config: the period ends after the last order/return
            cur.execute("SELECT (greatest(max(order_date), (SELECT coalesce(max(return_date), '-infinity') FROM returns)))::date + 1 FROM orders")
            end = cur.fetchone()[0]
        results.extend(_structure_results(cur))
        results.extend(_count_results(cur, cfg))
        for check in SQL_CHECKS:
            cur.execute(check.sql, {"end": end})
            value = _plain(cur.fetchone()[0])
            passed, expected = _check_expectation(check.expect, value)
            results.append(CheckResult(check.code, check.name, check.severity, value, expected,
                                       True if check.expect[0] == "info" else passed))
    conn.rollback()
    return results


def format_report(results: Sequence[CheckResult]) -> str:
    """Plain-text table of the results."""
    lines = [f"{'Code':<18}{'Sev':<6}{'Result':<8}{'Value':>10}  {'Expected':<11} Check"]
    for r in results:
        status = "OK" if r.passed else ("FAIL" if r.severity == "ERROR" else "WARN")
        if r.severity == "INFO":
            status = "info"
        lines.append(f"{r.code:<18}{r.severity:<6}{status:<8}{str(r.value):>10}  {r.expected:<11} {r.name}")
    errors = sum(1 for r in results if r.severity == "ERROR" and not r.passed)
    warnings = sum(1 for r in results if r.severity == "WARN" and not r.passed)
    lines.append(f"\nErrors: {errors}, warnings: {warnings}, checks: {len(results)}")
    return "\n".join(lines)


def has_errors(results: Sequence[CheckResult]) -> bool:
    """True if any ERROR-level check failed."""
    return any(r.severity == "ERROR" and not r.passed for r in results)


def run_on_database(cfg: GenerationConfig | None = None) -> list[CheckResult]:
    """Open a connection, validate, print the report and return the results."""
    from db import get_connection

    with get_connection() as conn:
        results = run_validation(conn, cfg)
    print(format_report(results))
    return results
