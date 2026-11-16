"""Small helpers shared by all generators (no database access here)."""

from __future__ import annotations

import random
import re
import unicodedata
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Mapping, Sequence, TypeVar

T = TypeVar("T")

CENT = Decimal("0.01")


class GenerationError(RuntimeError):
    """Raised when generation cannot continue safely (bad input data, guard violation)."""


def make_rng(seed: int, stream: str) -> random.Random:
    """Return an independent, reproducible RNG for one generation stage.

    String seeding is deterministic across runs and platforms (it does not depend
    on ``PYTHONHASHSEED``). Separate streams mean that changing, for example, the
    number of customers does not reshuffle the products.
    """
    return random.Random(f"{seed}:{stream}")


def money(value: float | Decimal) -> Decimal:
    """Round to cents (half up) and return a ``Decimal`` suitable for NUMERIC(12,2)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def floor_money(value: float | Decimal) -> Decimal:
    """Round *down* to cents. Used for refunds so that a refund never exceeds what was paid."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_DOWN)


def clamp(value: float, low: float, high: float) -> float:
    """Limit ``value`` to the closed interval ``[low, high]``."""
    return max(low, min(high, value))


def slugify(text: str, max_len: int = 24) -> str:
    """ASCII lower-case slug (letters and digits only) used to build e-mail addresses."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", normalized.lower())[:max_len] or "client"


def weighted_choice(rng: random.Random, weights: Mapping[T, float]) -> T:
    """Pick one key of ``weights`` with probability proportional to its value."""
    keys = list(weights)
    return rng.choices(keys, weights=[weights[key] for key in keys], k=1)[0]


def cumulative(weights: Sequence[float]) -> list[float]:
    """Cumulative sums (``len(weights)`` items) for ``random.choices(cum_weights=...)``."""
    total = 0.0
    result: list[float] = []
    for weight in weights:
        total += weight
        result.append(total)
    return result


def require_names(kind: str, available: Mapping[str, int], required: Sequence[str]) -> None:
    """Fail loudly when a reference table lacks names the generator relies on."""
    missing = [name for name in required if name not in available]
    if missing:
        raise GenerationError(
            f"Reference data for {kind} is missing {missing}. Run `python main.py seeds` first "
            f"(available: {sorted(available)})."
        )
