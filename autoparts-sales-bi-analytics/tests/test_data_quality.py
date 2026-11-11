from pathlib import Path
import sys
import pytest

# 1. Жорстко і чітко визначаємо корінь проєкту (папка autoparts-sales-bi-analytics)
# Оскільки test_data_quality.py лежить у папці tests, корінь — це один рівень вище.
ROOT_DIR = Path(__file__).resolve().parent.parent

# 2. Додаємо шлях до папки python, де лежить db.py
PYTHON_DIR = ROOT_DIR / "python"
sys.path.append(str(PYTHON_DIR))

try:
    from db import get_connection
except ImportError:
    # Якщо раптом db.py лежить в іншій папці, пробуємо імпортувати напряму з кореня
    sys.path.append(str(ROOT_DIR))
    from db import get_connection


def test_database_data_quality():
    """Test to validate data quality in the database using SQL checks."""

    # 3. Шукаємо файл SQL у папці sql в корені проєкту
    sql_file_path = ROOT_DIR / "sql" / "01_data_quality_checks.sql"
    
    if not sql_file_path.exists():
        pytest.skip(f"SQL file not found at {sql_file_path}. Skipping DQ tests.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            sql_script = sql_file_path.read_text(encoding="utf-8")
            cur.execute(sql_script)
            cur.execute("SELECT check_name, severity, failed_rows FROM dq_results;")
            results = cur.fetchall()

    failures = []
    for check_name, severity, failed_rows in results:
        if failed_rows > 0:
            failures.append(f"[{severity}] «{check_name}»: found {failed_rows} failed rows.")

    if failures:
        failure_message = "\n".join(f"  ❌ {f}" for f in failures)
        pytest.fail(
            f"\nData Quality Validation FAILED!\n"
            f"Errors found in data quality checks:\n{failure_message}"
        )