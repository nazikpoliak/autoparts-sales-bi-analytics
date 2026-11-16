"""Central configuration of the synthetic data generation.

Every tunable number of the generators lives here, so a run can be described
by one object and reproduced with the same seed.

Parameters can be set (in increasing priority):

1. defaults below;
2. environment variables ``GEN_*`` (also read from ``.env``);
3. command line options of ``main.py``.

The generation period is the half-open interval ``[start_date, end_date)``.
``end_date`` defaults to today, therefore every generated timestamp is
strictly in the past. Pass ``--end-date`` (or ``GEN_END_DATE``) to get the
exact same dataset on a different day.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields, replace
from datetime import date, timedelta
from typing import Any, Mapping

DAYS_PER_MONTH = 30.4375

# Minimum volumes required by the project (see README, section "Dataset").
TARGET_MINIMUMS: dict[str, int] = {
    "customers": 1_000,
    "products": 5_000,
    "orders": 50_000,
    "order_items": 250_000,
    "brands": 30,
    "categories": 15,
    "subcategories": 30,
    "salespersons": 20,
}
TARGET_HISTORY_MONTHS = (24, 36)


@dataclass(frozen=True)
class GenerationConfig:
    """Immutable set of generation parameters."""

    # Reproducibility
    seed: int = 42
    end_date: date = field(default_factory=date.today)

    # Volumes
    history_months: int = 30
    customers: int = 2_000
    products: int = 10_000
    orders: int = 60_000
    return_rate: float = 0.035  # share of Completed orders that get a return

    # Customers
    customer_history_years: int = 3  # how long before the period customers may be registered
    inactive_customer_share: float = 0.08

    # Orders
    trend_growth: float = 0.25  # relative growth of daily demand over the period
    customer_activity_sigma: float = 0.9  # log-normal spread of customer purchase activity
    product_zipf_exponent: float = 0.9  # Pareto-like popularity of products
    max_items_per_order: int = 25
    max_return_lag_days: int = 45

    # Technical
    copy_batch_rows: int = 20_000

    # ---- derived values -------------------------------------------------
    @property
    def start_date(self) -> date:
        """First day of the generation period."""
        return self.end_date - timedelta(days=round(self.history_months * DAYS_PER_MONTH))

    @property
    def period_days(self) -> int:
        """Number of whole days in ``[start_date, end_date)``."""
        return (self.end_date - self.start_date).days

    # ---- validation and construction --------------------------------------
    def validate(self) -> "GenerationConfig":
        """Raise ``ValueError`` for impossible parameters; return ``self``."""
        positive = ("history_months", "customers", "products", "orders",
                    "customer_history_years", "max_items_per_order", "max_return_lag_days",
                    "copy_batch_rows")
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)!r}")
        if not 0 <= self.return_rate < 1:
            raise ValueError("return_rate must be in [0, 1)")
        if not 0 <= self.inactive_customer_share < 1:
            raise ValueError("inactive_customer_share must be in [0, 1)")
        if self.end_date > date.today():
            raise ValueError("end_date must not be in the future")
        if self.trend_growth <= -1:
            raise ValueError("trend_growth must be greater than -1")
        return self

    def with_overrides(self, **overrides: Any) -> "GenerationConfig":
        """Return a copy with every non-``None`` override applied."""
        clean = {key: value for key, value in overrides.items() if value is not None}
        unknown = set(clean) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(f"Unknown config parameters: {sorted(unknown)}")
        return replace(self, **clean).validate()

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "GenerationConfig":
        """Build a config from ``GEN_*`` environment variables (missing ones use defaults)."""
        env = os.environ if env is None else env
        values: dict[str, Any] = {}
        for item in fields(cls):
            raw = env.get(f"GEN_{item.name.upper()}")
            if raw is None or raw == "":
                continue
            if item.name == "end_date":
                values[item.name] = date.fromisoformat(raw)
            elif item.type in ("float", float):
                values[item.name] = float(raw)
            else:
                values[item.name] = int(raw)
        return cls(**values).validate()

    def describe(self) -> str:
        """One-line human readable summary used in logs."""
        return (f"seed={self.seed}, period={self.start_date}..{self.end_date} "
                f"({self.history_months} months), customers={self.customers}, "
                f"products={self.products}, orders={self.orders}, return_rate={self.return_rate}")
