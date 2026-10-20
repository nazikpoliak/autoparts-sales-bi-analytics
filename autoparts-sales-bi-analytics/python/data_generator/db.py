import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Load environment variables from the .env file located next to db.py
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


def get_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_vars = [
        var for var in required_vars
        if not os.getenv(var)
    ]

    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables in .env: {', '.join(missing_vars)}"
        )

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )


def test_connection():
    """Tests the database connection and prints current database name and version."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version();")
            db_name, db_version = cur.fetchone()

    print(f"Connection successful! Database: {db_name}")
    print(f"PostgreSQL version: {db_version}")


if __name__ == "__main__":
    test_connection()