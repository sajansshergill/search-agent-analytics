"""
agent_drift.py
Rolling chi-square drift detection per user segment.

Usage
-----
    python src/analysis/agent_drift.py
"""

from __future__ import annotations

import logging

import mlflow
import pandas as pd
from scipy.stats import chi2

from src.utils.config import (
    DB_PATH,
    DRIFT_CHI2_ALPHA,
    DRIFT_WINDOW_DAYS,
    MIN_RECS_FOR_DRIFT,
    MLFLOW_EXPERIMENT,
)
from src.utils.db import query

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_recommendations() -> pd.DataFrame:
    df = query(
        "SELECT rec_id, experience_level, category, recommended_at FROM recommendations",
        db_path=DB_PATH,
    )
    df["recommended_at"] = pd.to_datetime(df["recommended_at"])
    return df


def compute_baseline_distribution(df: pd.DataFrame) -> pd.Series:
    return df["category"].value_counts(normalize=True)


def rolling_drift_score(
    df: pd.DataFrame,
    segment_col: str = "experience_level",
    window_days: int = DRIFT_WINDOW_DAYS,
) -> pd.DataFrame:
    baseline   = compute_baseline_distribution(df)
    categories = baseline.index.tolist()

    df = df.copy()
    df["week"] = df["recommended_at"].dt.to_period("W").dt.start_time

    results = []
    for segment_val, seg_df in df.groupby(segment_col):
        for week, wk_df in seg_df.groupby("week"):
            if len(wk_df) < MIN_RECS_FOR_DRIFT:
                continue

            observed_counts = wk_df["category"].value_counts().reindex(categories, fill_value=0)
            expected_counts = (baseline * len(wk_df)).reindex(categories, fill_value=0)

            mask = expected_counts > 0
            obs  = observed_counts[mask].values.astype(float)
            exp  = expected_counts[mask].values.astype(float)

            if exp.sum() == 0:
                continue

            chi2_stat = float(((obs - exp) ** 2 / exp).sum())
            dof       = len(obs) - 1
            p_value   = float(1 - chi2.cdf(chi2_stat, df=dof)) if dof > 0 else 1.0

            dominant_cat   = observed_counts.idxmax()
            dominant_share = round(observed_counts.max() / len(wk_df) * 100, 2)

            results.append({
                "week":             week,
                "segment":          segment_val,
                "n_recs":           len(wk_df),
                "chi2_stat":        round(chi2_stat, 4),
                "p_value":          round(p_value, 4),
                "drifted":          p_value < DRIFT_CHI2_ALPHA,
                "dominant_category":dominant_cat,
                "dominant_share":   dominant_share,
            })

    drift_cols = [
        "week",
        "segment",
        "n_recs",
        "chi2_stat",
        "p_value",
        "drifted",
        "dominant_category",
        "dominant_share",
    ]
    if not results:
        return pd.DataFrame(columns=drift_cols)
    return pd.DataFrame(results).sort_values(["week", "segment"])


def drift_summary(drift_df: pd.DataFrame) -> pd.DataFrame:
    return (
        drift_df.groupby("segment")
        .agg(
            total_windows  =("week",     "count"),
            drifted_windows=("drifted",  "sum"),
            mean_chi2      =("chi2_stat","mean"),
            mean_p_value   =("p_value",  "mean"),
        )
        .assign(drift_rate=lambda x: (x["drifted_windows"] / x["total_windows"] * 100).round(2))
        .reset_index()
        .sort_values("drift_rate", ascending=False)
    )


def category_bias(df: pd.DataFrame) -> pd.DataFrame:
    total        = len(df)
    n_categories = df["category"].nunique()
    expected     = 1 / n_categories

    counts = (
        df.groupby(["category", "experience_level"])
        .size()
        .reset_index(name="count")
    )
    counts["actual_share"]   = (counts["count"] / total).round(4)
    counts["expected_share"] = expected
    counts["bias_ratio"]     = (counts["actual_share"] / expected).round(3)
    counts["bias_label"]     = counts["bias_ratio"].apply(
        lambda r: "over" if r > 1.2 else ("under" if r < 0.8 else "neutral")
    )
    return counts.sort_values("bias_ratio", ascending=False)


def log_to_mlflow(drift_df: pd.DataFrame, summary: pd.DataFrame) -> None:
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(run_name="agent_drift"):
        overall_drift_rate = drift_df["drifted"].mean() * 100
        mlflow.log_metric("overall_drift_rate_pct", round(overall_drift_rate, 2))
        mlflow.log_metric("total_windows_tested",   len(drift_df))
        mlflow.log_metric("drifted_windows",        int(drift_df["drifted"].sum()))
        for _, row in summary.iterrows():
            mlflow.log_metric(f"drift_rate_{row['segment']}", row["drift_rate"])
            mlflow.log_metric(f"mean_chi2_{row['segment']}",  round(row["mean_chi2"], 4))
    logger.info("Drift metrics logged to MLflow")


def run() -> dict[str, pd.DataFrame]:
    logger.info("Running agent drift analysis ...")
    df       = load_recommendations()
    baseline = compute_baseline_distribution(df)

    drift_df = rolling_drift_score(df, segment_col="experience_level")
    summary  = drift_summary(drift_df)
    cat_bias = category_bias(df)

    logger.info("\nDrift summary:\n%s", summary.to_string(index=False))
    logger.info("Overall drift rate: %.1f%%", drift_df["drifted"].mean() * 100)

    try:
        log_to_mlflow(drift_df, summary)
    except Exception as exc:
        logger.warning("MLflow logging skipped: %s", exc)

    return {
        "drift_windows": drift_df,
        "summary":       summary,
        "category_bias": cat_bias,
        "baseline":      baseline.reset_index().rename(columns={"proportion": "share"}),
        "raw":           df,
    }


if __name__ == "__main__":
    run()