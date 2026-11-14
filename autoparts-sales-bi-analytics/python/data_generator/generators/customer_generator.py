"""Customer generator: B2B customers of an auto-parts distributor.

Customer types come from the ``customer_types`` dictionary (store, service station, fleet
operator, dealer, corporate customer). Corporate customers include agricultural, construction
and industrial companies. Every customer gets a unique name, tax id, phone and e-mail.
All e-mail addresses use the reserved ``.example`` domain, so no real mailbox can be addressed.
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Sequence

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common import GenerationError, make_rng, require_names, slugify  # noqa: E402
from config import GenerationConfig  # noqa: E402
from db import copy_rows, ensure_empty, fetch_name_map, get_connection  # noqa: E402
from profiles import CITY_WEIGHTS, CUSTOMER_TYPE_PROFILES  # noqa: E402

CUSTOMER_COLUMNS = (
    "customer_type_id", "city_id", "customer_name", "tax_id", "phone", "email", "address",
    "registration_date", "is_active",
)

STORE_WORDS = ["Avto", "Moto", "Express", "Apex", "Master", "Mega", "Karat", "Delta", "Alfa", "Garant",
               "Optima", "Profi", "Vektor", "Zakhid", "Skhid", "Centr", "Ukr", "Premium", "Universal", "Trast"]
STORE_SUFFIXES = ["Parts", "Shop", "Market", "Store", "Hub", "Depot", "Center"]
SERVICE_WORDS = ["Turbo", "Pro", "Fast", "Elite", "City", "Modern", "Mecano", "Master", "Drive", "Gear",
                 "Piston", "Motor", "Lux", "Racer", "Shield", "Torque", "Axis", "Optimal"]
SERVICE_SUFFIXES = ["Service", "Garage", "Station", "Center", "Repair", "Tech"]
FLEET_WORDS = ["Carpathian", "Dnipro", "Galych", "Podillia", "Slobozhanshchyna", "Prymorye", "Nova", "Euro",
               "Ukr", "Zakhid", "Skhid", "Vector", "Omega", "Prime", "Inter", "Tranzyt"]
FLEET_SUFFIXES = ["Logistics", "Transport", "Cargo", "Fleet", "Trans", "Bus Park"]
DEALER_WORDS = ["Avto", "Premium", "Grand", "Royal", "Capital", "Euro", "Master", "Alliance", "Prestige", "Stolytsia"]
CORPORATE_WORDS = ["Agro", "Zerno", "Lan", "Silhosp", "Budinvest", "Promtekh", "Komunalnyk", "Energo", "Metal",
                   "Kharchoprom", "Ahrosvit", "Stalbud", "Naftotrans", "Tekhnopark"]
CORPORATE_SUFFIXES = ["Plus", "Group", "Holding", "Invest", "Service", "Pro", "Ahro", "Prom"]
LAST_NAMES = ["Koval", "Melnyk", "Boyko", "Shevchuk", "Tkachenko", "Bondar", "Marchenko", "Savchenko",
              "Klymenko", "Kravets", "Lysenko", "Tymoshenko", "Pavlenko", "Moroz", "Kozak", "Oliinyk",
              "Polishchuk", "Hrytsenko", "Zakharchuk", "Kovalchuk", "Berezovskyi", "Danyliuk", "Fedorchuk",
              "Bilyk", "Rudenko", "Kravchuk", "Honcharenko", "Shapoval", "Petrenko", "Ivanenko"]
INITIALS = ["A.", "V.", "I.", "M.", "O.", "S.", "T.", "Y.", "D.", "R."]
STREETS = ["vul. Shevchenka", "vul. Ivana Franka", "vul. Lesi Ukrainky", "pr. Chornovola", "vul. Halytska",
           "vul. Sadova", "vul. Zamkova", "vul. Industrialna", "vul. Kyivska", "vul. Lvivska", "pr. Svobody",
           "vul. Kopernyka", "vul. Horodotska", "vul. Stryiska", "vul. Volodymyra Velykoho", "vul. Bandery",
           "vul. Vyhovskoho", "vul. Patona", "pr. Peremohy", "vul. Zavodska", "vul. Promyslova", "vul. Skladska"]
MOBILE_CODES = ["50", "63", "66", "67", "68", "73", "93", "95", "96", "97", "98", "99"]


class _Uniques:
    """Keeps already used names, tax ids, phones and e-mails (including those already in the DB)."""

    def __init__(self, tax_ids: set[str] | None = None) -> None:
        self.names: set[str] = set()
        self.tax_ids: set[str] = set(tax_ids or ())
        self.phones: set[str] = set()
        self.emails: set[str] = set()

    def unique_name(self, base: str) -> str:
        """Return ``base`` or ``base`` with a ``#n`` suffix if the name is already taken."""
        name, number = base, 1
        while name in self.names:
            number += 1
            name = f"{base} #{number}"
        self.names.add(name)
        return name


def _tax_id(rng: random.Random, length: int, used: set[str]) -> str:
    """Random unique numeric tax id (8 digits for companies, 10 for sole proprietors)."""
    while True:
        value = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(length - 1))
        if value not in used:
            used.add(value)
            return value


def _phone(rng: random.Random, used: set[str]) -> str:
    while True:
        value = f"+380{rng.choice(MOBILE_CODES)}{rng.randint(1_000_000, 9_999_999)}"
        if value not in used:
            used.add(value)
            return value


def _email(base_name: str, used: set[str], local: str) -> str:
    slug = slugify(base_name)
    candidate, number = f"{local}@{slug}.example", 1
    while candidate in used:
        number += 1
        candidate = f"{local}@{slug}{number}.example"
    used.add(candidate)
    return candidate


def _address(rng: random.Random) -> str:
    base = f"{rng.choice(STREETS)}, {rng.randint(1, 220)}"
    return f"{base}, office {rng.randint(1, 60)}" if rng.random() < 0.3 else base


def _registration_date(rng: random.Random, cfg: GenerationConfig, type_name: str) -> date:
    """Registration date: most customers pre-date the period, the rest join during it."""
    last_day = cfg.end_date - timedelta(days=1)
    legacy_share = 0.75 if type_name == "Dealer" else 0.60
    if rng.random() < legacy_share:
        span = cfg.customer_history_years * 365
        return cfg.start_date - timedelta(days=rng.randint(1, span))
    # Joined during the period, earlier joins are somewhat more likely.
    offset = int(rng.betavariate(1.0, 1.8) * cfg.period_days)
    return min(cfg.start_date + timedelta(days=offset), last_day)


def _build_identity(rng: random.Random, type_name: str, city_name: str,
                    uniq: _Uniques) -> tuple[str, str, str]:
    """Return ``(customer_name, tax_id, email)`` appropriate for the customer type."""
    if type_name == "Auto Parts Store":
        base = f"{rng.choice(STORE_WORDS)} {rng.choice(STORE_SUFFIXES)} ({city_name})"
        local, length = "sales", 8
    elif type_name == "Service Station":
        if rng.random() < 0.45:  # sole proprietor
            base = f"FOP {rng.choice(LAST_NAMES)} {rng.choice(INITIALS)} ({city_name})"
            length = 10
        else:
            base = f"STO '{rng.choice(SERVICE_WORDS)} {rng.choice(SERVICE_SUFFIXES)}' ({city_name})"
            length = 8
        local = "service"
    elif type_name == "Fleet Operator":
        base = f"TOV {rng.choice(FLEET_WORDS)} {rng.choice(FLEET_SUFFIXES)} ({city_name})"
        local, length = "fleet", 8
    elif type_name == "Dealer":
        base = f"{rng.choice(DEALER_WORDS)} Auto Center ({city_name})"
        local, length = "dealer", 8
    elif type_name == "Corporate Customer":
        base = f"TOV {rng.choice(CORPORATE_WORDS)} {rng.choice(CORPORATE_SUFFIXES)} ({city_name})"
        local, length = "office", 8
    else:  # guarded earlier by require_names, kept for safety
        raise GenerationError(f"No customer profile for type '{type_name}'")
    name = uniq.unique_name(base)
    return name, _tax_id(rng, length, uniq.tax_ids), _email(name, uniq.emails, local)


def build_customers(
    cfg: GenerationConfig,
    rng: random.Random,
    customer_types: dict[str, int],
    cities: Sequence[tuple[int, str]],
    existing_tax_ids: set[str] | None = None,
) -> list[tuple[Any, ...]]:
    """Create ``cfg.customers`` customer rows (pure function, no database access).

    ``customer_types`` maps type name -> id; ``cities`` is a list of ``(city_id, city_name)``.
    Row layout follows :data:`CUSTOMER_COLUMNS`.
    """
    require_names("customer_types", customer_types, list(CUSTOMER_TYPE_PROFILES))
    if not cities:
        raise GenerationError("No cities found. Run `python main.py seeds` first.")

    type_names = list(CUSTOMER_TYPE_PROFILES)
    type_weights = [CUSTOMER_TYPE_PROFILES[name].share for name in type_names]
    city_weights = [CITY_WEIGHTS.get(name, 1.0) for _, name in cities]
    uniq = _Uniques(existing_tax_ids)

    rows: list[tuple[Any, ...]] = []
    for _ in range(cfg.customers):
        type_name = rng.choices(type_names, weights=type_weights, k=1)[0]
        city_id, city_name = rng.choices(list(cities), weights=city_weights, k=1)[0]
        name, tax_id, email = _build_identity(rng, type_name, city_name, uniq)
        rows.append((
            customer_types[type_name],
            city_id,
            name,
            tax_id,
            _phone(rng, uniq.phones),
            email,
            _address(rng),
            _registration_date(rng, cfg, type_name),
            rng.random() >= cfg.inactive_customer_share,
        ))
    return rows


def generate_customers(cfg: GenerationConfig, conn: Any | None = None) -> int:
    """Insert customers into an empty ``customers`` table; return the number of rows."""
    if conn is None:
        with get_connection() as own_conn:
            return generate_customers(cfg, own_conn)

    print(f"Generating {cfg.customers} customers ...")
    with conn.cursor() as cur:
        ensure_empty(cur, ["customers"], "customers")
        customer_types = fetch_name_map(cur, "customer_types", "customer_type_id", "type_name")
        cur.execute("SELECT city_id, city_name FROM cities ORDER BY city_id")
        cities = [(int(city_id), name) for city_id, name in cur.fetchall()]
        rows = build_customers(cfg, make_rng(cfg.seed, "customers"), customer_types, cities)
        written = copy_rows(cur, "customers", CUSTOMER_COLUMNS, rows)
    print(f"Customers inserted: {written}")
    return written


if __name__ == "__main__":
    generate_customers(GenerationConfig.from_env())
