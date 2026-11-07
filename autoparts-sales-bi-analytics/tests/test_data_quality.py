from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection


def test_database_data_quality():
    """Test to validate data quality in the database using SQL checks."""

    sql_file_path = Path(__file__).resolve().parent.parent / "sql" / "02_data_quality_checks.sql"
    
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

    # If there are any failures, fail the test and provide a detailed message
    if failures:
        failure_message = "\n".join(f"  ❌ {f}" for f in failures)
        pytest.fail(
            f"\nData Quality Validation FAILED!\n"
            f"Errors found in data quality checks:\n{failure_message}"
        )