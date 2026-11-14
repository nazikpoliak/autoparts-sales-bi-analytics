"""Read-only data quality check of a generated database.

Skipped unless ``RUN_DB_TESTS=1`` and the ``DB_*`` variables point to a database filled by
``python main.py all``. The test only reads data (read-only transaction) and never writes,
truncates or deletes anything.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1",
                                reason="set RUN_DB_TESTS=1 to check a generated database")


def test_database_passes_all_validation_checks():
    from python.data_generator.config import GenerationConfig
    from tests.db import get_connection
    from python.data_generator.validation import format_report, has_errors, run_validation

    cfg = GenerationConfig.from_env()
    with get_connection() as conn:
        results = run_validation(conn, cfg)
    report = format_report(results)
    assert not has_errors(results), "\n" + report
