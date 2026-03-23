"""
match_quality.py
Calibration analysis: agent match_score vs true Jaccard skill overlap.

Usage
-----
    python src/analysis/match_quality.py
"""

from __future__ import annotations

import logging

import mlflow
import pandas as pd

from src.utils.config import DB_PATH, MLFLOW_EXPERIMENT
from src.utils.db import query

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_recommendations() -> pd.DataFrame:
    return query("SELECT * FROM v_recommendations", db_path=DB_PATH)


def calibration_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "metric": ["true_jaccard", "match_score", "calibration_error"],
        "mean":   [df["true_jaccard"].mean(), df["match_score"].mean(), df["calibration_error"].mean()],
        "median": [df["true_jaccard"].median(), df["match_score"].median(), df["calibration_error"].median()],
        "std":    [df["true_jaccard"].std(), df["match_score"].std(), df["calibration_error"].std()],
    }).round(4)


def calibration_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("category")[["true_jaccard", "match_score", "calibration_error"]]
        .mean()
        .round(4)
        .reset_index()
        .sort_values("calibration_error", ascending=False)
    )


def calibration_by_experience(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("experience_level")[["true_jaccard", "match_score", "calibration_error"]]
        .mean()
        .round(4)
        .reset_index()
    )


def score_distribution_bins(
    df: pd.DataFrame, col: str = "match_score", bins: int = 10
) -> pd.DataFrame:
    df = df.copy()
    df["bin"] = pd.cut(df[col], bins=bins)
    return (
        df.groupby("bin", observed=True)
        .size()
        .reset_index(name="count")
        .assign(bin=lambda x: x["bin"].astype(str))
    )


def top_miscalibrated_categories(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    by_cat = calibration_by_category(df)
    by_cat["abs_error"] = by_cat["calibration_error"].abs()
    return by_cat.nlargest(top_n, "abs_error")[["category", "calibration_error", "abs_error"]]


def log_to_mlflow(summary: pd.DataFrame, by_category: pd.DataFrame) -> None:
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(run_name="match_quality"):
        for _, row in summary.iterrows():
            mlflow.log_metric(f"{row['metric']}_mean",   row["mean"])
            mlflow.log_metric(f"{row['metric']}_median", row["median"])
            mlflow.log_metric(f"{row['metric']}_std",    row["std"])
        worst = by_category.iloc[0]
        mlflow.log_metric("worst_category_calibration_error", worst["calibration_error"])
        mlflow.log_param("worst_category", worst["category"])
    logger.info("Metrics logged to MLflow experiment '%s'", MLFLOW_EXPERIMENT)


def run() -> dict[str, pd.DataFrame]:
    logger.info("Running match quality analysis ...")
    df = load_recommendations()

    summary       = calibration_summary(df)
    by_category   = calibration_by_category(df)
    by_experience = calibration_by_experience(df)
    miscalibrated = top_miscalibrated_categories(df)
    score_dist    = score_distribution_bins(df, col="match_score")
    jaccard_dist  = score_distribution_bins(df, col="true_jaccard")

    logger.info("\n%s", summary.to_string(index=False))
    logger.info("\nCalibration by category:\n%s", by_category.to_string(index=False))

    try:
        log_to_mlflow(summary, by_category)
    except Exception as exc:
        logger.warning("MLflow logging skipped: %s", exc)

    return {
        "summary":       summary,
        "by_category":   by_category,
        "by_experience": by_experience,
        "miscalibrated": miscalibrated,
        "score_dist":    score_dist,
        "jaccard_dist":  jaccard_dist,
        "raw":           df,
    }


if __name__ == "__main__":
    run()