"""
load_to_db.py
Loads raw CSVs into DuckDB with typed schemas and analytical views.

Usage
-----
    python src/ingestion/load_to_db.py
"""

from __future__ import annotations

import logging

import pandas as pd

from src.utils.config import DATA_RAW, DB_PATH
from src.utils.db import get_conn, load_df, row_count

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TABLES = {
    "users":           DATA_RAW / "users.csv",
    "jobs":            DATA_RAW / "jobs.csv",
    "recommendations": DATA_RAW / "recommendations.csv",
    "events":          DATA_RAW / "events.csv",
}

DATETIME_COLS: dict[str, list[str]] = {
    "users":           ["created_at"],
    "jobs":            ["posted_at"],
    "recommendations": ["recommended_at"],
    "events":          ["occurred_at"],
}


def load_all() -> None:
    logger.info("Loading CSVs into DuckDB at %s", DB_PATH)

    for table, csv_path in TABLES.items():
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV not found: {csv_path}\n"
                "Run `python src/ingestion/generate_data.py` first."
            )
        logger.info("Reading %s ...", csv_path.name)
        df = pd.read_csv(csv_path, parse_dates=DATETIME_COLS.get(table, []))
        load_df(df, table=table, db_path=DB_PATH, if_exists="replace")
        logger.info("  → %s: %d rows loaded", table, row_count(table))

    _create_views()
    logger.info("All tables loaded successfully.")


def _create_views() -> None:
    logger.info("Creating analytical views ...")
    with get_conn(DB_PATH) as conn:

        conn.execute("""
            CREATE OR REPLACE VIEW v_recommendations AS
            SELECT
                r.rec_id,
                r.user_id,
                r.job_id,
                r.experience_level,
                r.category,
                r.true_jaccard,
                r.match_score,
                r.match_score - r.true_jaccard       AS calibration_error,
                r.recommended_at,
                date_trunc('week', r.recommended_at) AS rec_week,
                u.location                           AS user_location,
                j.company,
                j.salary_min,
                j.salary_max
            FROM recommendations r
            JOIN users u ON r.user_id = u.user_id
            JOIN jobs  j ON r.job_id  = j.job_id
        """)

        conn.execute("""
            CREATE OR REPLACE VIEW v_funnel AS
            SELECT
                r.rec_id,
                r.user_id,
                r.job_id,
                r.experience_level,
                r.category,
                r.match_score,
                r.recommended_at,
                MAX(CASE WHEN e.event_type = 'viewed'  THEN 1 ELSE 0 END) AS viewed,
                MAX(CASE WHEN e.event_type = 'clicked' THEN 1 ELSE 0 END) AS clicked,
                MAX(CASE WHEN e.event_type = 'applied' THEN 1 ELSE 0 END) AS applied
            FROM recommendations r
            LEFT JOIN events e ON r.rec_id = e.rec_id
            GROUP BY
                r.rec_id, r.user_id, r.job_id,
                r.experience_level, r.category,
                r.match_score, r.recommended_at
        """)

        conn.execute("""
            CREATE OR REPLACE VIEW v_weekly_recs AS
            SELECT
                date_trunc('week', recommended_at) AS week,
                category,
                experience_level,
                count(*)                           AS rec_count
            FROM recommendations
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """)

    logger.info("Views created: v_recommendations, v_funnel, v_weekly_recs")


if __name__ == "__main__":
    load_all()