"""Orders and order items generator.

Planning is separated from loading: the ``plan_*`` / ``build_*`` functions are pure (they take
plain data and a seeded RNG, and need no database), so the business rules can be unit tested.
``generate_orders`` reads reference data, runs the plan and bulk-loads it with ``COPY``.

Business rules implemented here
-------------------------------
* An order is never dated before the customer's registration date, before the salesperson's
  hire date, or before a product existed. Customers marked inactive have *churned*: their
  orders stop at least 60 days before the end of the period.
* Demand has a weekly pattern, a yearly seasonality and a growth trend. Customers differ
  strongly in activity (log-normal), so a minority of customers produces most orders; a
  customer registered recently gets proportionally fewer orders.
* Product popularity follows a Pareto-like (Zipf) law. Only active products sell; discontinued
  or temporarily unavailable ones sell until a cut-off date; pre-order items do not sell.
* Order status depends on the order age: non-final statuses occur only in the last two weeks.
* Prices are negotiated per customer type; a line never sells below cost, also after discount.
  ``discount_amount`` is the discount of the whole line (not per unit), as in the schema.
* The manager normally belongs to the customer's region (``customers.city -> region``).
"""

from __future__ import annotations

import bisect
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator, Sequence

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common import GenerationError, clamp, cumulative, make_rng, money, require_names  # noqa: E402
from config import GenerationConfig  # noqa: E402
from db import copy_rows, ensure_empty, fetch_name_map, get_connection, reserve_ids  # noqa: E402
from profiles import (  # noqa: E402
    CUSTOMER_TYPE_PROFILES,
    MONTH_SEASONALITY,
    ORDER_HOUR_WEIGHTS,
    ORDER_HOURS,
    SUBCATEGORY_PROFILES,
    WEEKDAY_FACTOR,
    CustomerTypeProfile,
)

ORDER_COLUMNS = ("order_id", "customer_id", "salesperson_id", "sales_channel_id", "order_status_id",
                 "order_date", "customer_reference", "notes")
ITEM_COLUMNS = ("order_id", "product_id", "quantity", "unit_sale_price", "unit_cost", "discount_amount")
REQUIRED_STATUSES = ("Completed", "Cancelled", "Processing", "On Hold", "Partially Fulfilled")
CHURN_GAP_DAYS = 60          # inactive customers stop ordering this long before the end
MIN_MARGIN_OVER_COST = 1.03  # list price floor
MIN_NET_MARGIN = 1.01        # even after the discount a line is sold above cost


# ---------------------------------------------------------------------------
# Plain data containers (what the generator needs to know about DB rows)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CustomerRef:
    customer_id: int
    type_name: str
    region_id: int | None
    registration_date: date
    is_active: bool


@dataclass(frozen=True)
class SalespersonRef:
    salesperson_id: int
    region_id: int | None
    hire_date: date | None


@dataclass(frozen=True)
class ProductRef:
    product_id: int
    subcategory_name: str
    category_name: str
    purchase_price: Decimal
    standard_sale_price: Decimal
    status_name: str
    created_at: datetime


@dataclass
class OrderHeader:
    customer_id: int
    type_name: str
    salesperson_id: int | None
    channel_id: int
    status_id: int
    status_name: str
    order_date: datetime
    reference: str | None
    notes: str | None


# ---------------------------------------------------------------------------
# Calendar: seasonality, weekday pattern and growth trend
# ---------------------------------------------------------------------------
class Calendar:
    """Daily demand weights for ``[start_date, end_date)`` with cumulative sums for fast sampling."""

    def __init__(self, cfg: GenerationConfig) -> None:
        self.start = cfg.start_date
        self.days = cfg.period_days
        if self.days < 1:
            raise GenerationError("The generation period is empty")
        weights = []
        for index in range(self.days):
            day = self.start + timedelta(days=index)
            trend = 1.0 + cfg.trend_growth * index / max(self.days - 1, 1)
            weights.append(trend * MONTH_SEASONALITY[day.month] * WEEKDAY_FACTOR[day.weekday()])
        self.cum = [0.0] + cumulative(weights)

    def date_of(self, index: int) -> date:
        return self.start + timedelta(days=index)

    def mass(self, first: int, last: int) -> float:
        """Total demand weight of days ``first..last`` (inclusive)."""
        return self.cum[last + 1] - self.cum[first]

    def sample_day(self, rng: random.Random, first: int, last: int) -> int:
        """Random day index in ``first..last``, proportional to demand."""
        point = rng.uniform(self.cum[first], self.cum[last + 1])
        return int(clamp(bisect.bisect_right(self.cum, point) - 1, first, last))


def _random_time(rng: random.Random) -> time:
    hour = rng.choices(ORDER_HOURS, weights=ORDER_HOUR_WEIGHTS, k=1)[0]
    return time(hour, rng.randint(0, 59), rng.randint(0, 59))


# ---------------------------------------------------------------------------
# Headers: who orders, when, through which channel, with which status
# ---------------------------------------------------------------------------
def customer_windows(cfg: GenerationConfig, rng: random.Random,
                     customers: Sequence[CustomerRef]) -> list[tuple[int, int] | None]:
    """Day-index window ``(first, last)`` in which each customer can order, or ``None``."""
    last_day = cfg.period_days - 1
    windows: list[tuple[int, int] | None] = []
    for customer in customers:
        first = max(0, (customer.registration_date - cfg.start_date).days)
        last = last_day
        if first > last:
            windows.append(None)
            continue
        if not customer.is_active:                      # churned customer
            latest_stop = last_day - CHURN_GAP_DAYS
            if latest_stop < first:
                windows.append(None)                    # registered too late to have bought anything
                continue
            last = min(latest_stop, first + int(rng.uniform(0.15, 0.85) * (latest_stop - first)))
        windows.append((first, last))
    return windows


def choose_status(rng: random.Random, order_date: datetime, end_ts: datetime) -> str:
    """Order status from the order age: unfinished statuses exist only for fresh orders."""
    age_days = (end_ts - order_date).days
    if age_days <= 14:
        weights = {"Completed": 55, "Processing": 20, "Partially Fulfilled": 10, "On Hold": 5, "Cancelled": 10}
    elif age_days <= 45:
        weights = {"Completed": 93, "Cancelled": 6, "On Hold": 1}
    else:
        weights = {"Completed": 92, "Cancelled": 8}
    names = list(weights)
    return rng.choices(names, weights=[weights[n] for n in names], k=1)[0]


_NOTES = {
    "Completed": (0.08, ("Delivered by courier", "Pickup at warehouse", "Urgent delivery")),
    "Cancelled": (0.60, ("Cancelled by customer", "Out of stock - cancelled", "Duplicate order")),
    "On Hold": (0.80, ("Awaiting payment", "Awaiting stock")),
    "Partially Fulfilled": (0.80, ("Backorder for remaining items", "Partial shipment")),
    "Processing": (0.20, ("In picking",)),
}


def _pick_salesperson(rng: random.Random, customer: CustomerRef, primary: SalespersonRef,
                      by_region: dict[int | None, list[SalespersonRef]],
                      everyone: Sequence[SalespersonRef], when: date,
                      channel_name: str) -> int | None:
    """Account manager of the order: usually the customer's own, hired before the order date."""
    if channel_name == "E-commerce" and rng.random() < 0.85:
        return None  # self-service web order
    if channel_name == "B2B Portal" and rng.random() < 0.50:
        return None
    roll = rng.random()
    if roll < 0.88:
        pool: Sequence[SalespersonRef] = [primary]
    elif roll < 0.96:
        pool = by_region.get(customer.region_id) or everyone
    else:
        pool = everyone  # key-account request handled by another region
    eligible = [s for s in pool if s.hire_date is None or s.hire_date <= when]
    if not eligible:
        eligible = [s for s in everyone if s.hire_date is None or s.hire_date <= when]
    return rng.choice(eligible).salesperson_id if eligible else None


def plan_order_headers(
    cfg: GenerationConfig,
    rng: random.Random,
    calendar: Calendar,
    customers: Sequence[CustomerRef],
    salespersons: Sequence[SalespersonRef],
    channels: dict[str, int],
    statuses: dict[str, int],
) -> list[OrderHeader]:
    """Plan ``cfg.orders`` order headers sorted by date (so order ids grow with time)."""
    require_names("sales_channels", channels, sorted({c for p in CUSTOMER_TYPE_PROFILES.values() for c in p.channel_weights}))
    require_names("order_statuses", statuses, REQUIRED_STATUSES)
    unknown_types = {c.type_name for c in customers} - set(CUSTOMER_TYPE_PROFILES)
    if unknown_types:
        raise GenerationError(f"No customer profile for types {sorted(unknown_types)}; extend profiles.py")
    if not customers or not salespersons:
        raise GenerationError("Customers and salespersons are required to generate orders.")

    windows = customer_windows(cfg, rng, customers)
    weights = []
    for customer, window in zip(customers, windows):
        if window is None:
            weights.append(0.0)
            continue
        activity = CUSTOMER_TYPE_PROFILES[customer.type_name].activity * rng.lognormvariate(0, cfg.customer_activity_sigma)
        weights.append(activity * calendar.mass(*window))   # a recent customer has less time to buy
    if sum(weights) <= 0:
        raise GenerationError("No customer is able to place orders in the generation period.")

    everyone = sorted(salespersons, key=lambda s: s.salesperson_id)
    by_region: dict[int | None, list[SalespersonRef]] = {}
    for person in everyone:
        by_region.setdefault(person.region_id, []).append(person)
    primary = [rng.choice(by_region.get(c.region_id) or everyone) for c in customers]

    end_ts = datetime.combine(cfg.end_date, time.min)
    chosen = rng.choices(range(len(customers)), cum_weights=cumulative(weights), k=cfg.orders)
    headers: list[OrderHeader] = []
    for index in chosen:
        customer = customers[index]
        profile: CustomerTypeProfile = CUSTOMER_TYPE_PROFILES[customer.type_name]
        first, last = windows[index]  # type: ignore[misc]  # weight > 0 implies a window
        moment = datetime.combine(calendar.date_of(calendar.sample_day(rng, first, last)), _random_time(rng))

        channel_names = list(profile.channel_weights)
        channel = rng.choices(channel_names, weights=[profile.channel_weights[n] for n in channel_names], k=1)[0]
        status = choose_status(rng, moment, end_ts)
        note_probability, note_options = _NOTES[status]
        headers.append(OrderHeader(
            customer_id=customer.customer_id,
            type_name=customer.type_name,
            salesperson_id=_pick_salesperson(rng, customer, primary[index], by_region, everyone,
                                             moment.date(), channel),
            channel_id=channels[channel],
            status_id=statuses[status],
            status_name=status,
            order_date=moment,
            reference=f"PO-{rng.randint(100000, 999999)}" if rng.random() < profile.reference_prob else None,
            notes=rng.choice(note_options) if rng.random() < note_probability else None,
        ))
    headers.sort(key=lambda header: header.order_date)
    return headers


# ---------------------------------------------------------------------------
# Items: what is ordered
# ---------------------------------------------------------------------------
class ProductPool:
    """Products with popularity weights and availability windows."""

    def __init__(self, cfg: GenerationConfig, rng: random.Random, products: Sequence[ProductRef]) -> None:
        if not products:
            raise GenerationError("No products found. Run `python main.py products` first.")
        unknown = {p.subcategory_name for p in products} - set(SUBCATEGORY_PROFILES)
        if unknown:
            raise GenerationError(f"No product profile for subcategories {sorted(unknown)}")
        self.products = list(products)
        self.size = len(self.products)
        self._indices = range(self.size)
        start_ts = datetime.combine(cfg.start_date, time.min)
        end_ts = datetime.combine(cfg.end_date, time.min)

        ranks = list(range(1, self.size + 1))
        rng.shuffle(ranks)  # popularity is independent of the id / insertion order
        self._base = [
            SUBCATEGORY_PROFILES[p.subcategory_name].demand / (ranks[i] ** cfg.product_zipf_exponent)
            for i, p in enumerate(self.products)
        ]
        self._cum_by_type: dict[str, list[float]] = {}

        self.available_from: list[datetime] = []
        self.available_until: list[datetime | None] = []
        for product in self.products:
            self.available_from.append(product.created_at)
            if product.status_name == "Active":
                self.available_until.append(None)
            elif product.status_name == "Preorder":
                self.available_until.append(product.created_at)   # empty window: not sold yet
            else:  # Discontinued / Temporarily Unavailable: sold until a cut-off date
                low = max(product.created_at, start_ts)
                self.available_until.append(low + (end_ts - low) * rng.uniform(0.25, 0.85))

    def _cum(self, type_name: str) -> list[float]:
        if type_name not in self._cum_by_type:
            affinity = CUSTOMER_TYPE_PROFILES[type_name].category_affinity
            self._cum_by_type[type_name] = cumulative(
                [w * affinity.get(p.category_name, 1.0) for w, p in zip(self._base, self.products)]
            )
        return self._cum_by_type[type_name]

    def sellable_at(self, index: int, moment: datetime) -> bool:
        until = self.available_until[index]
        return self.available_from[index] <= moment and (until is None or moment < until)

    def pick(self, rng: random.Random, type_name: str, moment: datetime, count: int) -> list[int]:
        """``count`` distinct product indexes that can be sold at ``moment`` (fewer if none left)."""
        cum = self._cum(type_name)
        chosen: list[int] = []
        seen: set[int] = set()
        for _ in range(20):
            for index in rng.choices(self._indices, cum_weights=cum, k=max(6, (count - len(chosen)) * 3)):
                if index not in seen and self.sellable_at(index, moment):
                    seen.add(index)
                    chosen.append(index)
                    if len(chosen) == count:
                        return chosen
        if not chosen:  # extremely small catalogue: deterministic fallback
            chosen = [i for i in self._indices if self.sellable_at(i, moment)][:count]
        return chosen


def _quantity(rng: random.Random, subcategory: str, profile: CustomerTypeProfile) -> int:
    """Line quantity: mostly small, long tail for consumables and for large customers."""
    sub = SUBCATEGORY_PROFILES[subcategory]
    mean = max(1.0, sub.qty_mean * profile.qty_mult)
    extra = rng.expovariate(1.0 / (mean - 1.0)) if mean > 1.0 else 0.0
    return int(clamp(1 + int(extra), 1, sub.qty_max))


def price_line(rng: random.Random, profile: CustomerTypeProfile, product: ProductRef,
               quantity: int) -> tuple[Decimal, Decimal, Decimal]:
    """Return ``(unit_sale_price, unit_cost, discount_amount)``; discount is for the whole line."""
    unit_cost = money(float(product.purchase_price) * rng.uniform(0.985, 1.015))
    unit_price = money(float(product.standard_sale_price) * profile.price_factor * rng.uniform(0.975, 1.025))
    unit_price = max(unit_price, money(float(unit_cost) * MIN_MARGIN_OVER_COST))

    discount = Decimal("0.00")
    if rng.random() < profile.discount_prob:
        percent = rng.triangular(0.02, 0.12, 0.05) + (0.03 if quantity >= 10 else 0.0)
        line_amount = unit_price * quantity
        wanted = money(float(line_amount) * percent)
        room = line_amount - money(float(unit_cost) * quantity * MIN_NET_MARGIN)  # keep the line above cost
        discount = max(Decimal("0.00"), min(wanted, room))
    return unit_price, unit_cost, discount


def plan_items(rng: random.Random, cfg: GenerationConfig, pool: ProductPool, header: OrderHeader,
               order_id: int) -> list[tuple[Any, ...]]:
    """Order lines for one order; layout follows :data:`ITEM_COLUMNS`."""
    profile = CUSTOMER_TYPE_PROFILES[header.type_name]
    wanted = int(clamp(round(rng.lognormvariate(profile.items_mu, profile.items_sigma)), 1, cfg.max_items_per_order))
    indexes = pool.pick(rng, header.type_name, header.order_date, wanted)
    if not indexes:
        raise GenerationError(f"No product is sellable at {header.order_date}")
    rows = []
    for index in indexes:
        product = pool.products[index]
        quantity = _quantity(rng, product.subcategory_name, profile)
        unit_price, unit_cost, discount = price_line(rng, profile, product, quantity)
        rows.append((order_id, product.product_id, quantity, unit_price, unit_cost, discount))
    return rows


def iter_order_items(rng: random.Random, cfg: GenerationConfig, pool: ProductPool,
                     headers: Sequence[OrderHeader], order_ids: Sequence[int]) -> Iterator[tuple[Any, ...]]:
    """Stream all order lines, header by header (keeps memory flat for large volumes)."""
    for header, order_id in zip(headers, order_ids):
        yield from plan_items(rng, cfg, pool, header, order_id)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def generate_orders(cfg: GenerationConfig, conn: Any | None = None) -> dict[str, int]:
    """Plan and insert orders and order items into empty tables; return row counts."""
    if conn is None:
        with get_connection() as own_conn:
            return generate_orders(cfg, own_conn)

    print(f"Generating {cfg.orders} orders ...")
    with conn.cursor() as cur:
        ensure_empty(cur, ["orders", "order_items"], "orders")

        cur.execute(
            "SELECT c.customer_id, t.type_name, ci.region_id, c.registration_date, c.is_active "
            "FROM customers c "
            "JOIN customer_types t ON t.customer_type_id = c.customer_type_id "
            "LEFT JOIN cities ci ON ci.city_id = c.city_id "
            "ORDER BY c.customer_id"
        )
        customers = [CustomerRef(int(i), t, r, reg, bool(active)) for i, t, r, reg, active in cur.fetchall()
                     if reg is not None]
        cur.execute("SELECT salesperson_id, region_id, hire_date FROM salespersons "
                    "WHERE is_active ORDER BY salesperson_id")
        salespersons = [SalespersonRef(int(i), r, h) for i, r, h in cur.fetchall()]
        channels = fetch_name_map(cur, "sales_channels", "sales_channel_id", "channel_name")
        statuses = fetch_name_map(cur, "order_statuses", "order_status_id", "status_name")
        cur.execute(
            "SELECT p.product_id, s.subcategory_name, c.category_name, p.purchase_price, "
            "       p.standard_sale_price, ps.status_name, p.created_at "
            "FROM products p "
            "JOIN subcategories s ON s.subcategory_id = p.subcategory_id "
            "JOIN categories c ON c.category_id = s.category_id "
            "JOIN product_statuses ps ON ps.product_status_id = p.product_status_id "
            "ORDER BY p.product_id"
        )
        products = [ProductRef(int(i), sub, cat, Decimal(pp), Decimal(sp), st, created)
                    for i, sub, cat, pp, sp, st, created in cur.fetchall()]

        calendar = Calendar(cfg)
        pool = ProductPool(cfg, make_rng(cfg.seed, "orders:pool"), products)
        headers = plan_order_headers(cfg, make_rng(cfg.seed, "orders:headers"), calendar,
                                     customers, salespersons, channels, statuses)
        order_ids = reserve_ids(cur, "orders", "order_id", len(headers))

        order_rows = (
            (oid, h.customer_id, h.salesperson_id, h.channel_id, h.status_id, h.order_date, h.reference, h.notes)
            for oid, h in zip(order_ids, headers)
        )
        orders_written = copy_rows(cur, "orders", ORDER_COLUMNS, order_rows)
        items_written = copy_rows(
            cur, "order_items", ITEM_COLUMNS,
            iter_order_items(make_rng(cfg.seed, "orders:items"), cfg, pool, headers, order_ids),
        )
    print(f"Orders inserted: {orders_written}, order items inserted: {items_written}")
    return {"orders": orders_written, "order_items": items_written}


if __name__ == "__main__":
    generate_orders(GenerationConfig.from_env())
