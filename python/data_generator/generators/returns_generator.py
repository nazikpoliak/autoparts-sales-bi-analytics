"""Returns generator (initial population, executed once).

Rules
-----
* Returns exist only for ``Completed`` orders; one order has at most one ``returns`` row.
* A return may contain several order lines; each selected line is returned in full
  (``return_items.quantity`` equals the sold quantity, so it can never exceed it).
* The return date is at least one day after the order date and strictly before the end of
  the generation period (never in the future).
* ``refund_unit_price`` is the refund **per one unit** and includes the original discount::

      refund_unit_price = floor_to_cent((unit_sale_price * quantity - discount_amount) / quantity)

  so ``quantity * refund_unit_price`` never exceeds what the customer actually paid for the line.
  (``discount_amount`` of an order line is a discount for the whole line, not per unit.)
* No ``ON CONFLICT``: the schema has no UNIQUE on ``returns.order_id`` and must not be changed.
  The "one return per order" rule is guaranteed by sampling distinct orders, and a repeated run
  is refused by the empty-table guard.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common import GenerationError, clamp, floor_money, make_rng  # noqa: E402
from config import GenerationConfig  # noqa: E402
from db import copy_rows, ensure_empty, get_connection, reserve_ids  # noqa: E402

RETURN_COLUMNS = ("return_id", "order_id", "customer_id", "return_reason_id", "return_date", "notes")
RETURN_ITEM_COLUMNS = ("return_id", "order_item_id", "product_id", "quantity", "refund_unit_price")
ID_CHUNK = 5_000

# Reason -> (relative frequency, notes that fit the reason)
REASON_PROFILES: dict[str, tuple[int, tuple[str, ...]]] = {
    "Defective Product": (22, ("Defective item reported by customer", "Failed after installation")),
    "Incorrect Item Supplied": (12, ("Wrong item shipped from warehouse", "Part number mismatch on delivery")),
    "Incorrect Item Ordered": (16, ("Wrong item ordered by mistake", "Customer ordered a wrong part number")),
    "Damaged During Delivery": (10, ("Damaged packaging during delivery", "Item damaged in transit")),
    "Customer Changed Mind": (12, ("Customer changed mind", "Repair cancelled by end customer")),
    "Warranty Claim": (12, ("Warranty claim registered", "Premature wear reported")),
    "Compatibility Issue": (12, ("Part does not fit the vehicle", "Compatibility issue found during fitting")),
    "Duplicate Order": (4, ("Item was ordered twice",)),
}


@dataclass(frozen=True)
class CompletedOrder:
    order_id: int
    customer_id: int
    order_date: datetime


@dataclass(frozen=True)
class SoldLine:
    order_item_id: int
    order_id: int
    product_id: int
    quantity: Decimal
    unit_sale_price: Decimal
    discount_amount: Decimal


def refund_unit_price(unit_sale_price: Decimal, quantity: Decimal, discount_amount: Decimal) -> Decimal:
    """Refund per one unit including the original line discount, rounded *down* to cents."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return floor_money((unit_sale_price * quantity - discount_amount) / quantity)


def pick_return_date(rng: random.Random, order_date: datetime, end_ts: datetime, max_lag_days: int) -> datetime:
    """Return date 1..``max_lag_days`` days after the order, never at or after ``end_ts``."""
    lag_days = int(clamp(1 + rng.expovariate(1 / 9), 1, max_lag_days))
    candidate = (order_date + timedelta(days=lag_days)).replace(
        hour=rng.randint(9, 17), minute=rng.randint(0, 59), second=rng.randint(0, 59))
    lowest = order_date + timedelta(days=1)
    highest = end_ts - timedelta(minutes=1)
    return min(max(candidate, lowest), highest)


def plan_returns(
    cfg: GenerationConfig,
    rng: random.Random,
    completed: Sequence[CompletedOrder],
    reason_ids: dict[str, int],
) -> list[tuple[CompletedOrder, datetime, int, str | None]]:
    """Choose orders to be returned: ``(order, return_date, reason_id, notes)`` sorted by date."""
    unknown = set(reason_ids) - set(REASON_PROFILES)
    reasons = [name for name in REASON_PROFILES if name in reason_ids]
    if not reasons:
        raise GenerationError(f"No usable return reasons (database has {sorted(reason_ids)}).")
    if unknown:
        print(f"Note: return reasons without a profile are not used: {sorted(unknown)}")
    weights = [REASON_PROFILES[name][0] for name in reasons]

    end_ts = datetime.combine(cfg.end_date, time.min)
    latest_return = end_ts - timedelta(minutes=1)
    eligible = [o for o in completed if o.order_date + timedelta(days=1) <= latest_return]  # room for a return date
    wanted = min(round(cfg.return_rate * len(completed)), len(eligible))
    chosen = rng.sample(eligible, wanted)  # distinct orders -> at most one return per order

    plan = []
    for order in chosen:
        reason = rng.choices(reasons, weights=weights, k=1)[0]
        note_options = REASON_PROFILES[reason][1]
        notes = rng.choice(note_options) if rng.random() < 0.65 else None
        plan.append((order, pick_return_date(rng, order.order_date, end_ts, cfg.max_return_lag_days),
                     reason_ids[reason], notes))
    plan.sort(key=lambda row: (row[1], row[0].order_id))
    return plan


def plan_return_items(rng: random.Random, lines: Sequence[SoldLine]) -> list[SoldLine]:
    """Lines of an order to be returned: mostly one, sometimes two or three."""
    count = min(len(lines), rng.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0])
    return rng.sample(list(lines), count)


def generate_returns(cfg: GenerationConfig, conn: Any | None = None) -> dict[str, int]:
    """Insert returns and return items into empty tables; return row counts."""
    if conn is None:
        with get_connection() as own_conn:
            return generate_returns(cfg, own_conn)

    print("Generating returns ...")
    rng = make_rng(cfg.seed, "returns")
    with conn.cursor() as cur:
        ensure_empty(cur, ["returns", "return_items"], "returns")
        cur.execute(
            "SELECT o.order_id, o.customer_id, o.order_date FROM orders o "
            "JOIN order_statuses s ON s.order_status_id = o.order_status_id "
            "WHERE s.status_name = 'Completed' ORDER BY o.order_id"
        )
        completed = [CompletedOrder(int(i), int(c), d) for i, c, d in cur.fetchall()]
        if not completed:
            raise GenerationError("No completed orders found. Run `python main.py orders` first.")
        cur.execute("SELECT reason_name, return_reason_id FROM return_reasons ORDER BY return_reason_id")
        reason_ids = {name: int(i) for name, i in cur.fetchall()}

        plan = plan_returns(cfg, rng, completed, reason_ids)
        return_ids = reserve_ids(cur, "returns", "return_id", len(plan))
        returns_written = copy_rows(
            cur, "returns", RETURN_COLUMNS,
            ((rid, order.order_id, order.customer_id, reason_id, when, notes)
             for rid, (order, when, reason_id, notes) in zip(return_ids, plan)),
        )

        # Load sold lines of the returned orders (in chunks) and build return items.
        return_id_by_order = {order.order_id: rid for rid, (order, *_rest) in zip(return_ids, plan)}
        order_ids = list(return_id_by_order)
        item_rows: list[tuple[Any, ...]] = []
        for start in range(0, len(order_ids), ID_CHUNK):
            chunk = order_ids[start:start + ID_CHUNK]
            cur.execute(
                "SELECT order_item_id, order_id, product_id, quantity, unit_sale_price, discount_amount "
                "FROM order_items WHERE order_id = ANY(%s) ORDER BY order_id, order_item_id",
                (chunk,),
            )
            lines_by_order: dict[int, list[SoldLine]] = {}
            for item_id, order_id, product_id, qty, price, discount in cur.fetchall():
                lines_by_order.setdefault(int(order_id), []).append(
                    SoldLine(int(item_id), int(order_id), int(product_id), Decimal(qty), Decimal(price), Decimal(discount)))
            for order_id in chunk:
                lines = lines_by_order.get(order_id)
                if not lines:
                    raise GenerationError(f"Completed order {order_id} has no lines to return")
                for line in plan_return_items(rng, lines):
                    item_rows.append((
                        return_id_by_order[order_id], line.order_item_id, line.product_id, line.quantity,
                        refund_unit_price(line.unit_sale_price, line.quantity, line.discount_amount),
                    ))
        items_written = copy_rows(cur, "return_items", RETURN_ITEM_COLUMNS, item_rows)
    print(f"Returns inserted: {returns_written}, return items inserted: {items_written}")
    return {"returns": returns_written, "return_items": items_written}


if __name__ == "__main__":
    generate_returns(GenerationConfig.from_env())
