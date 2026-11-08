import os
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))          # lets tests import src.cleaning

DB_PATH = os.environ.get("WAREHOUSE_DB", str(ROOT / "warehouse.duckdb"))
PROCESSED = Path(os.environ.get("PROCESSED_DIR", ROOT / "data" / "processed"))


@pytest.fixture(scope="session")
def con():
    """Raw warehouse, opened read-only so a test can never change it."""
    connection = duckdb.connect(DB_PATH, read_only=True)
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def processed_dir():
    return PROCESSED
