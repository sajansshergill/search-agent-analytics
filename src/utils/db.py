"""
db.py
DuckDB connection helpers with context manager support.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import duckdb
import pandas as pd

from src.utils.config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_conn(
    db_path: Path = DB_PATH, read_only: bool = False
) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = duckdb.connect(str(db_path), read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    with get_conn(db_path, read_only=True) as conn:
        return conn.execute(sql).df()


def execute(sql: str, db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(sql)
        logger.debug("Executed: %s", sql[:120])


def table_exists(table: str, db_path: Path = DB_PATH) -> bool:
    with get_conn(db_path, read_only=True) as conn:
        result = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()
        return result[0] > 0


def load_df(
    df: pd.DataFrame,
    table: str,
    db_path: Path = DB_PATH,
    if_exists: str = "replace",
) -> None:
    with get_conn(db_path) as conn:
        if if_exists == "replace":
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df")
        logger.info("Loaded %d rows into '%s'", len(df), table)


def row_count(table: str, db_path: Path = DB_PATH) -> int:
    with get_conn(db_path, read_only=True) as conn:
        return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]