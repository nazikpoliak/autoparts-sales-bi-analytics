"""Unit tests of the generators' pure logic. They need no database and no psycopg."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from common import make_rng
from config import GenerationConfig
from generators.customer_generator import CUSTOMER_COLUMNS, build_customers
from generators.product_generator import PRODUCT_COLUMNS, build_products
from generators.returns_generator import (
    CompletedOrder, SoldLine, pick_return_date, plan_return_items, plan_returns, refund_unit_price,
)
from seeds.reference_data import (
    BRANDS, CITIES, CUSTOMER_TYPES, PRODUCT_STATUSES, SUBCATEGORIES, SUPPLIERS,
)

END = date(2026, 11, 1)


def _cfg(**kw) -> GenerationConfig:
    base = dict(seed=7, end_date=END, customers=120, products=400, orders=500)
    base.update(kw)
    return GenerationConfig(**base)


def _ids(names):
    return {name: i + 1 for i, name in enumerate(names)}


def _customers(cfg):
    types = _ids(r["customer_type_name"] for r in CUSTOMER_TYPES)
    cities = [(i + 1, r["city_name"]) for i, r in enumerate(CITIES)]
    return build_customers(cfg, make_rng(cfg.seed, "customers"), types, cities)


def _products(cfg):
    subs = [(i + 1, r["subcategory_name"], r["category_name"]) for i, r in enumerate(SUBCATEGORIES)]
    return build_products(
        cfg, make_rng(cfg.seed, "products"), subs,
        _ids(r["brand_name"] for r in BRANDS), _ids(r["supplier_name"] for r in SUPPLIERS),
        _ids(r["status_name"] for r in PRODUCT_STATUSES))


# ---- config ---------------------------------------------------------------------------------
def test_config_defaults_are_valid():
    _cfg().validate()


@pytest.mark.parametrize("bad", [dict(customers=0), dict(orders=-1), dict(return_rate=1.5),
                                 dict(history_months=0), dict(inactive_customer_share=-0.1)])
def test_config_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        _cfg(**bad).validate()


def test_period_is_half_open_and_in_the_past():
    cfg = _cfg()
    assert cfg.start_date < cfg.end_date
    assert cfg.period_days == (cfg.end_date - cfg.start_date).days


# ---- customers / products -------------------------------------------------------------------
def test_customers_reproducible_and_unique():
    first, second = _customers(_cfg()), _customers(_cfg())
    assert first == second
    assert len(first) == 120
    name_i, mail_i = CUSTOMER_COLUMNS.index("customer_name"), CUSTOMER_COLUMNS.index("email")
    assert len({r[name_i] for r in first}) == len(first)
    assert len({r[mail_i] for r in first}) == len(first)
    assert _customers(_cfg(seed=8)) != first


def test_products_prices_and_uniqueness():
    rows = _products(_cfg())
    assert len(rows) == 400
    col = {c: i for i, c in enumerate(PRODUCT_COLUMNS)}
    assert len({r[col["sku"]] for r in rows}) == len(rows)
    assert len({r[col["product_name"]] for r in rows}) == len(rows)
    assert all(r[col["standard_sale_price"]] > r[col["purchase_price"]] > 0 for r in rows)


# ---- returns --------------------------------------------------------------------------------
def test_refund_is_per_unit_and_respects_discount():
    # 10 units x 100.00, line discount 50.00 -> customer paid 950.00 -> 95.00 per unit
    assert refund_unit_price(Decimal("100.00"), Decimal("10"), Decimal("50.00")) == Decimal("95.00")
    # never above the paid net unit price (rounded down to cents)
    value = refund_unit_price(Decimal("33.33"), Decimal("3"), Decimal("1.00"))
    assert value * 3 <= Decimal("33.33") * 3 - Decimal("1.00")
    assert refund_unit_price(Decimal("10.00"), Decimal("2"), Decimal("0")) == Decimal("10.00")
    with pytest.raises(ValueError):
        refund_unit_price(Decimal("1"), Decimal("0"), Decimal("0"))


def test_return_date_always_after_order_and_before_end():
    rng = random.Random(1)
    end_ts = datetime.combine(END, datetime.min.time())
    order_date = end_ts - timedelta(days=2)
    for _ in range(500):
        d = pick_return_date(rng, order_date, end_ts, 45)
        assert order_date < d < end_ts
    old = datetime(2025, 1, 10, 12, 0)
    for _ in range(500):
        d = pick_return_date(rng, old, end_ts, 45)
        assert old + timedelta(days=1) <= d <= old + timedelta(days=46)


def test_plan_returns_one_per_order_and_only_eligible():
    cfg = _cfg(return_rate=0.2)
    end_ts = datetime.combine(END, datetime.min.time())
    orders = [CompletedOrder(i, i, end_ts - timedelta(days=i % 200, hours=1)) for i in range(1, 1001)]
    plan = plan_returns(cfg, random.Random(3), orders, {"Defective Product": 1, "Warranty Claim": 2})
    ids = [p[0].order_id for p in plan]
    assert len(ids) == len(set(ids))
    assert all(p[0].order_date < p[1] < end_ts for p in plan)
    assert abs(len(plan) - 200) <= 5


def test_plan_return_items_picks_distinct_lines():
    lines = [SoldLine(i, i, 100 + i, Decimal("3"), Decimal("10.00"), Decimal("0")) for i in range(1, 6)]
    for seed in range(50):
        chosen = plan_return_items(random.Random(seed), lines)
        assert 1 <= len(chosen) <= 3
        assert len({c.order_item_id for c in chosen}) == len(chosen)
