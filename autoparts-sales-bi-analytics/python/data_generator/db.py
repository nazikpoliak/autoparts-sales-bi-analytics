
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Завантажуємо параметри з .env, який лежить поруч із db.py
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


def get_connection():
    """Створює підключення до PostgreSQL."""
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
            f"Не задані параметри у .env: {', '.join(missing_vars)}"
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
    """Перевіряє підключення та назву поточної БД."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version();")
            db_name, db_version = cur.fetchone()

    print(f"Підключення успішне. База даних: {db_name}")
    print(f"Версія PostgreSQL: {db_version}")


if __name__ == "__main__":
    test_connection()
