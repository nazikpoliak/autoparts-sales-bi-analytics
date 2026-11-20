"""Command line entry point of the synthetic data generation.

Run from the ``python/data_generator`` folder::

    python main.py check-connection         # connectivity only, nothing is written
    python main.py all                      # seeds -> customers -> products -> orders -> returns -> validate
    python main.py all --seed 7 --orders 50000
    python main.py orders                   # a single step (parents must already exist)
    python main.py validate                 # read-only quality checks of the current database

Safety rules
------------
* Every writing command prints the target database and asks for confirmation (``--yes`` skips it).
* Each generation step is one transaction: a failure leaves the database as it was before the step.
* Generators refuse to run on non-empty target tables, so the initial population cannot be
  duplicated by an accidental second run. Use a NEW empty database (see README), never the old one.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Sequence

# Our folder goes FIRST, so a same-named third-party package (e.g. "common") cannot shadow our modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import GenerationError  # noqa: E402
from config import GenerationConfig  # noqa: E402
from db import describe_target, get_connection, test_connection  # noqa: E402

STEPS = ("seeds", "customers", "products", "orders", "returns")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoParts synthetic data generator")
    parser.add_argument("command", choices=("all", *STEPS, "validate", "check-connection"))
    parser.add_argument("--seed", type=int, help="random seed (default 42)")
    parser.add_argument("--end-date", type=date.fromisoformat, help="last day of the period, exclusive (YYYY-MM-DD, default today)")
    parser.add_argument("--history-months", type=int, help="length of the period in months (default 30)")
    parser.add_argument("--customers", type=int)
    parser.add_argument("--products", type=int)
    parser.add_argument("--orders", type=int)
    parser.add_argument("--return-rate", type=float, help="share of Completed orders with a return (default 0.035)")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation before writing")
    return parser


def _step_runner(step: str) -> Callable[[GenerationConfig, object], object]:
    """Import lazily so that `validate` and `check-connection` need no generator modules."""
    if step == "seeds":
        from load_seeds import load_reference_data
        return lambda cfg, conn: load_reference_data(conn)
    if step == "customers":
        from generators.customer_generator import generate_customers
        return generate_customers
    if step == "products":
        from generators.product_generator import generate_products
        return generate_products
    if step == "orders":
        from generators.orders_generator import generate_orders
        return generate_orders
    from generators.returns_generator import generate_returns
    return generate_returns


def _confirm(target: str, steps: Sequence[str], assume_yes: bool) -> None:
    print(f"Target database: {target}")
    print(f"Steps to run:    {', '.join(steps)}")
    if assume_yes:
        return
    if not sys.stdin.isatty():
        raise GenerationError("Refusing to write without confirmation. Pass --yes in non-interactive mode.")
    if input("Type 'yes' to continue: ").strip().lower() != "yes":
        raise GenerationError("Cancelled by user.")


def run(argv: Sequence[str] | None = None) -> int:
    """Execute the requested command; return the process exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "check-connection":
        test_connection()
        return 0

    cfg = GenerationConfig.from_env().with_overrides(
        seed=args.seed, end_date=args.end_date, history_months=args.history_months,
        customers=args.customers, products=args.products, orders=args.orders, return_rate=args.return_rate,
    )
    print("Configuration:", cfg.describe())

    if args.command == "validate":
        from validation import has_errors, run_on_database
        return 1 if has_errors(run_on_database(cfg)) else 0

    steps = STEPS if args.command == "all" else (args.command,)
    with get_connection() as conn:
        with conn.cursor() as cur:
            _confirm(describe_target(cur), steps, args.yes)
        conn.rollback()
        for step in steps:
            # One transaction per step: commit after success, automatic rollback on error.
            _step_runner(step)(cfg, conn)
            conn.commit()

    if args.command == "all":
        from validation import has_errors, run_on_database
        return 1 if has_errors(run_on_database(cfg)) else 0
    return 0


def main() -> None:
    try:
        sys.exit(run())
    except (GenerationError, ValueError) as error:  # ValueError: invalid configuration values
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()