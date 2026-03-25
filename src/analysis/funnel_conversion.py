"""
funnel_conversion.py
Stage-by-stage funnel: Recommended → Viewed → Clicked → Applied.

Usage
-----
    python src/analysis/funnel_conversion.py
"""

from __future__ import annotations

import logging

import mlflow
import pandas as pd

from src.utils.config import DB_PATH, MLFLOW_EXPERIMENT
from src.utils.db import query

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STAGES = ["recommended", "viewed", "clicked", "applied"]


def load_funnel() -> pd.DataFrame:
    return query("SELECT * FROM v_funnel", db_path=DB_PATH)


def overall_funnel(df: pd.DataFrame) -> pd.DataFrame:
    total   = len(df)
    viewed  = df["viewed"].sum()
    clicked = df["clicked"].sum()
    applied = df["applied"].sum()

    funnel = pd.DataFrame({
        "stage": STAGES,
        "count": [total, viewed, clicked, applied],
    })
    funnel["pct_of_recommended"] = (funnel["count"] / total * 100).round(2)
    funnel["stage_conversion"]   = [
        100.0,
        round(viewed  / total   * 100, 2) if total   else 0,
        round(clicked / viewed  * 100, 2) if viewed  else 0,
        round(applied / clicked * 100, 2) if clicked else 0,
    ]
    return funnel


def funnel_by_segment(df: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    grp = df.groupby(segment_col).agg(
        total  =("rec_id", "count"),
        viewed =("viewed",  "sum"),
        clicked=("clicked", "sum"),
        applied=("applied", "sum"),
    ).reset_index()

    grp["view_rate"]  = (grp["viewed"]  / grp["total"]   * 100).round(2)
    grp["click_rate"] = (grp["clicked"] / grp["viewed"]  * 100).round(2).fillna(0)
    grp["apply_rate"] = (grp["applied"] / grp["clicked"] * 100).round(2).fillna(0)
    grp["end_to_end"] = (grp["applied"] / grp["total"]   * 100).round(2)
    return grp.sort_values("end_to_end", ascending=False)


def funnel_weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["week"] = pd.to_datetime(df["recommended_at"]).dt.to_period("W").dt.start_time
    trend = (
        df.groupby("week")
        .agg(total=("rec_id", "count"), applied=("applied", "sum"))
        .reset_index()
    )
    trend["apply_rate"] = (trend["applied"] / trend["total"] * 100).round(2)
    return trend


def drop_off_analysis(df: pd.DataFrame) -> pd.DataFrame:
    seg = df.groupby(["category", "experience_level"]).agg(
        clicked=("clicked", "sum"),
        applied=("applied", "sum"),
    ).reset_index()
    seg = seg[seg["clicked"] >= 10]
    seg["click_to_apply"] = (seg["applied"] / seg["clicked"] * 100).round(2)
    return seg.sort_values("click_to_apply").head(10)


def log_to_mlflow(overall: pd.DataFrame) -> None:
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(run_name="funnel_conversion"):
        for _, row in overall.iterrows():
            mlflow.log_metric(f"funnel_{row['stage']}_count",            int(row["count"]))
            mlflow.log_metric(f"funnel_{row['stage']}_pct_recommended",  row["pct_of_recommended"])
            mlflow.log_metric(f"funnel_{row['stage']}_stage_conversion", row["stage_conversion"])
    logger.info("Funnel metrics logged to MLflow")


def run() -> dict[str, pd.DataFrame]:
    logger.info("Running funnel conversion analysis ...")
    df = load_funnel()

    overall       = overall_funnel(df)
    by_experience = funnel_by_segment(df, "experience_level")
    by_category   = funnel_by_segment(df, "category")
    weekly_trend  = funnel_weekly_trend(df)
    drop_off      = drop_off_analysis(df)

    logger.info("\nOverall funnel:\n%s", overall.to_string(index=False))
    logger.info("\nBy experience level:\n%s", by_experience.to_string(index=False))

    try:
        log_to_mlflow(overall)
    except Exception as exc:
        logger.warning("MLflow logging skipped: %s", exc)

    return {
        "overall":       overall,
        "by_experience": by_experience,
        "by_category":   by_category,
        "weekly_trend":  weekly_trend,
        "drop_off":      drop_off,
        "raw":           df,
    }


if __name__ == "__main__":
    run()