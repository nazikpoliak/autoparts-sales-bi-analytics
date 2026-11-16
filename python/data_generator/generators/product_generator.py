"""Product generator: a realistic auto-parts catalogue.

* Brands are matched to categories (no spark plugs by an oil brand, batteries only by battery
  makers) and suppliers to the categories they specialise in.
* Purchase prices follow a price band per *subcategory*, scaled by the brand's positioning
  (premium / standard / value); the markup depends on the category, so margins differ.
* Status and ``created_at`` are generated together: discontinued items are old, pre-order items
  are brand new, some regular items are launched during the generation period. The order
  generator later respects both (nothing is sold before it exists).
"""

from __future__ import annotations

import random
import string
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Sequence

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common import GenerationError, make_rng, money, require_names  # noqa: E402
from config import GenerationConfig  # noqa: E402
from db import copy_rows, ensure_empty, fetch_name_map, get_connection  # noqa: E402
from profiles import (  # noqa: E402
    BRAND_TIER_MULTIPLIER,
    BRAND_TIERS,
    CATEGORY_BRANDS,
    CATEGORY_MARKUP,
    POSITIONS,
    PRODUCT_STATUS_WEIGHTS,
    SUBCATEGORY_PROFILES,
    SUPPLIER_SPECIALISATION,
)

PRODUCT_COLUMNS = (
    "subcategory_id", "brand_id", "supplier_id", "product_status_id", "sku", "product_name",
    "description", "unit_of_measure", "purchase_price", "standard_sale_price", "weight_kg", "created_at",
)
LEGACY_CATALOGUE_YEARS = 4


def _random_moment(rng: random.Random, first_day: date, last_day: date, early_bias: bool = False) -> datetime:
    """Random timestamp between two dates (inclusive); ``early_bias`` favours earlier days."""
    span = max((last_day - first_day).days, 0)
    fraction = rng.betavariate(1.0, 1.5) if early_bias else rng.random()
    day = first_day + timedelta(days=int(fraction * span))
    return datetime.combine(day, time(rng.randint(8, 18), rng.randint(0, 59), rng.randint(0, 59)))


def _created_at(rng: random.Random, cfg: GenerationConfig, status: str) -> datetime:
    """Creation timestamp consistent with the product status."""
    last_day = cfg.end_date - timedelta(days=1)
    if status == "Preorder":  # newly announced, not on sale yet
        return _random_moment(rng, max(cfg.start_date, cfg.end_date - timedelta(days=45)), last_day)
    launched_in_period = rng.random() < (0.05 if status != "Active" else 0.15)
    if launched_in_period:
        return _random_moment(rng, cfg.start_date, max(cfg.start_date, cfg.end_date - timedelta(days=60)),
                              early_bias=True)
    first_day = cfg.start_date - timedelta(days=365 * LEGACY_CATALOGUE_YEARS)
    return _random_moment(rng, first_day, cfg.start_date - timedelta(days=1))


def _purchase_price(rng: random.Random, price_min: float, price_max: float, tier_multiplier: float) -> float:
    """Skewed towards the cheaper end of the band (few expensive parts), scaled by brand tier."""
    position = rng.betavariate(1.2, 2.2)
    base = price_min * (price_max / price_min) ** position
    return max(5.0, base * tier_multiplier * rng.uniform(0.95, 1.05))


def _supplier_weights(category: str, suppliers: dict[str, int]) -> tuple[list[int], list[float]]:
    """Supplier ids and weights for a category: specialists dominate, other specialists are excluded."""
    ids: list[int] = []
    weights: list[float] = []
    for name, supplier_id in suppliers.items():
        categories = SUPPLIER_SPECIALISATION.get(name)
        if categories is None:
            weight = 1.0                      # generalist
        elif category in categories:
            weight = 4.0                      # specialist of this category
        else:
            continue                          # specialist of other categories
        ids.append(supplier_id)
        weights.append(weight)
    return ids, weights


def _unique_part_number(rng: random.Random, prefix: str, used_skus: set[str]) -> tuple[str, str]:
    """Return ``(sku, manufacturer part number)`` not used before."""
    while True:
        number = f"{rng.randint(100, 999)}{rng.choice(string.ascii_uppercase)}{rng.randint(1000, 9999)}"
        sku = f"{prefix}-{number}"
        if sku not in used_skus:
            used_skus.add(sku)
            return sku, number


def build_products(
    cfg: GenerationConfig,
    rng: random.Random,
    subcategories: Sequence[tuple[int, str, str]],
    brands: dict[str, int],
    suppliers: dict[str, int],
    statuses: dict[str, int],
    existing_skus: set[str] | None = None,
) -> list[tuple[Any, ...]]:
    """Create ``cfg.products`` product rows (pure function, no database access).

    ``subcategories`` is a list of ``(subcategory_id, subcategory_name, category_name)``.
    Row layout follows :data:`PRODUCT_COLUMNS`.
    """
    require_names("product_statuses", statuses, list(PRODUCT_STATUS_WEIGHTS))
    unknown = [name for _, name, _ in subcategories if name not in SUBCATEGORY_PROFILES]
    if unknown:
        raise GenerationError(f"No product profile for subcategories {unknown}; extend profiles.py")
    if not suppliers:
        raise GenerationError("No suppliers found. Run `python main.py seeds` first.")

    used_skus = set(existing_skus or ())
    status_names = list(PRODUCT_STATUS_WEIGHTS)
    status_weights = [PRODUCT_STATUS_WEIGHTS[name] for name in status_names]
    # Catalogue breadth follows demand only partially: niche subcategories still have many items.
    subcategory_weights = [0.5 + SUBCATEGORY_PROFILES[name].demand for _, name, _ in subcategories]

    rows: list[tuple[Any, ...]] = []
    for _ in range(cfg.products):
        subcategory_id, subcategory, category = rng.choices(list(subcategories), weights=subcategory_weights, k=1)[0]
        profile = SUBCATEGORY_PROFILES[subcategory]

        brand_names = [name for name in (profile.brands or CATEGORY_BRANDS[category]) if name in brands]
        if not brand_names:
            raise GenerationError(f"No known brands for subcategory '{subcategory}' (category '{category}')")
        brand = rng.choice(brand_names)
        supplier_ids, supplier_weights = _supplier_weights(category, suppliers)
        supplier_id = rng.choices(supplier_ids, weights=supplier_weights, k=1)[0]
        status = rng.choices(status_names, weights=status_weights, k=1)[0]

        prefix = "".join(ch for ch in brand.upper() if ch.isalnum())[:3].ljust(3, "X")
        sku, part_number = _unique_part_number(rng, prefix, used_skus)
        noun = rng.choice(profile.nouns)
        position = rng.choice(POSITIONS) if profile.positions else None
        product_name = f"{brand} {noun}{' ' + position if position else ''}, {part_number}"
        description = (f"{noun}{' (' + position.lower() + ')' if position else ''} by {brand} "
                       f"for passenger cars and light commercial vehicles. Subcategory: {subcategory}.")

        tier = BRAND_TIERS.get(brand, "standard")
        purchase = _purchase_price(rng, profile.price_min, profile.price_max, BRAND_TIER_MULTIPLIER[tier])
        markup_low, markup_high = profile.markup or CATEGORY_MARKUP[category]
        markup = rng.uniform(markup_low, markup_high) - (0.03 if tier == "premium" else 0.0)
        purchase_price = money(purchase)
        sale_price = money(float(purchase_price) * markup)

        weight = money(rng.uniform(profile.weight_min, profile.weight_max)) if rng.random() > 0.05 else None
        rows.append((
            subcategory_id, brands[brand], supplier_id, statuses[status], sku, product_name, description,
            "pcs", purchase_price, sale_price, weight, _created_at(rng, cfg, status),
        ))
    return rows


def generate_products(cfg: GenerationConfig, conn: Any | None = None) -> int:
    """Insert products into an empty ``products`` table; return the number of rows."""
    if conn is None:
        with get_connection() as own_conn:
            return generate_products(cfg, own_conn)

    print(f"Generating {cfg.products} products ...")
    with conn.cursor() as cur:
        ensure_empty(cur, ["products"], "products")
        cur.execute(
            "SELECT s.subcategory_id, s.subcategory_name, c.category_name "
            "FROM subcategories s JOIN categories c ON c.category_id = s.category_id "
            "ORDER BY s.subcategory_id"
        )
        subcategories = [(int(i), name, category) for i, name, category in cur.fetchall()]
        brands = fetch_name_map(cur, "brands", "brand_id", "brand_name")
        suppliers = fetch_name_map(cur, "suppliers", "supplier_id", "supplier_name")
        statuses = fetch_name_map(cur, "product_statuses", "product_status_id", "status_name")
        rows = build_products(cfg, make_rng(cfg.seed, "products"), subcategories, brands, suppliers, statuses)
        written = copy_rows(cur, "products", PRODUCT_COLUMNS, rows)
    print(f"Products inserted: {written}")
    return written


if __name__ == "__main__":
    generate_products(GenerationConfig.from_env())
