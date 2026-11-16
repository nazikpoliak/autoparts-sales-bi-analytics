"""PostgreSQL connection and bulk-loading helpers.

Credentials come only from environment variables / the local ``.env`` file
(see ``.env.example``); nothing secret is stored in the code.

``psycopg`` is imported lazily, so the pure generation logic and its unit tests
can be used without a database driver installed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Sequence

from common import GenerationError

if TYPE_CHECKING:  # pragma: no cover
    import psycopg

ENV_PATH = Path(__file__).resolve().parent / ".env"
REQUIRED_VARS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def _identifier(name: str) -> str:
    """Validate a table/column name taken from the code (never from user input)."""
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


def load_env() -> None:
    """Load the ``.env`` file next to this module if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # the variables may be set in the shell instead
        return
    load_dotenv(ENV_PATH)


def get_connection(dbname: str | None = None) -> "psycopg.Connection":
    """Open a connection using ``DB_*`` variables; ``dbname`` overrides ``DB_NAME``.

    Used as a context manager the connection commits on success and rolls back on an
    exception, so each generation step is one atomic transaction.
    """
    load_env()
    missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill it in."
        )
    import psycopg

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=dbname or os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )


def describe_target(cur: Any) -> str:
    """Return ``database@host:port`` of the connection behind ``cur`` for log messages."""
    cur.execute("SELECT current_database(), inet_server_addr()::text, inet_server_port()")
    database, host, port = cur.fetchone()
    return f"{database} ({host or 'local socket'}:{port})"


def count_rows(cur: Any, table: str) -> int:
    """Return ``SELECT count(*)`` of a table."""
    cur.execute(f"SELECT count(*) FROM {_identifier(table)}")
    return int(cur.fetchone()[0])


def ensure_empty(cur: Any, tables: Sequence[str], step: str) -> None:
    """Refuse to run a generator on tables that already contain data.

    This is the idempotency guard: every generator is meant to be executed exactly once
    for the initial population, and a second run must never silently add duplicates.
    """
    filled = {table: count_rows(cur, table) for table in tables}
    filled = {table: rows for table, rows in filled.items() if rows}
    if filled:
        raise GenerationError(
            f"Step '{step}' stopped: target tables are not empty {filled}. "
            f"The generators populate an empty database exactly once. Use a new empty database."
        )


def reserve_ids(cur: Any, table: str, id_column: str, count: int) -> list[int]:
    """Reserve ``count`` consecutive-in-order identity values and return them ascending.

    The parent rows can then be bulk-loaded with ``COPY`` together with their children,
    without a ``RETURNING`` round trip per row. Values come from the column's own
    sequence, so the identity continues correctly afterwards.
    """
    if count <= 0:
        return []
    cur.execute(
        "SELECT nextval(pg_get_serial_sequence(%s, %s)) FROM generate_series(1, %s::int)",
        (_identifier(table), _identifier(id_column), count),
    )
    ids = sorted(int(row[0]) for row in cur.fetchall())
    if len(ids) != count:
        raise GenerationError(f"Could not reserve {count} ids for {table}.{id_column}")
    return ids


def copy_rows(cur: Any, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
    """Bulk insert rows with ``COPY ... FROM STDIN``; return the number of rows written."""
    column_list = ", ".join(_identifier(column) for column in columns)
    written = 0
    with cur.copy(f"COPY {_identifier(table)} ({column_list}) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)
            written += 1
    return written


def fetch_name_map(cur: Any, table: str, id_column: str, name_column: str) -> dict[str, int]:
    """Return ``{name: id}`` of a reference table."""
    cur.execute(
        f"SELECT {_identifier(name_column)}, {_identifier(id_column)} "
        f"FROM {_identifier(table)} ORDER BY {_identifier(id_column)}"
    )
    return {name: int(row_id) for name, row_id in cur.fetchall()}


def test_connection() -> None:
    """Print the database name and server version (a quick connectivity check)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version()")
            db_name, db_version = cur.fetchone()
    print(f"Connection successful! Database: {db_name}")
    print(f"PostgreSQL version: {db_version}")


test_connection.__test__ = False  # not a pytest test, although the name starts with "test"

if __name__ == "__main__":
    test_connection()
