import pandas as pd
import pytest

from src.analysis.agent_drift import (
    category_bias,
    compute_baseline_distribution,
    drift_summary,
    rolling_drift_score,
)


@pytest.fixture
def sample_recs() -> pd.DataFrame:
    import numpy as np
    rng        = np.random.default_rng(42)
    n          = 120
    categories = ["Data Science","ML Engineering","Data Engineering","Analytics Engineering"]
    levels     = ["entry","mid","senior"]
    return pd.DataFrame({
        "rec_id":           [f"r{i}" for i in range(n)],
        "user_id":          [f"u{i%20}" for i in range(n)],
        "experience_level": rng.choice(levels, n),
        "category":         rng.choice(categories, n),
        "recommended_at":   pd.date_range("2024-04-01", periods=n, freq="6h"),
    })


def test_baseline_sums_to_one(sample_recs):
    baseline = compute_baseline_distribution(sample_recs)
    assert abs(baseline.sum() - 1.0) < 1e-6


def test_baseline_covers_all_categories(sample_recs):
    baseline = compute_baseline_distribution(sample_recs)
    assert set(baseline.index) == set(sample_recs["category"].unique())


def test_drift_score_columns(sample_recs):
    result = rolling_drift_score(sample_recs)
    for col in ["week","segment","chi2_stat","p_value","drifted","n_recs"]:
        assert col in result.columns


def test_p_value_range(sample_recs):
    result = rolling_drift_score(sample_recs)
    if len(result) > 0:
        assert (result["p_value"] >= 0).all()
        assert (result["p_value"] <= 1).all()


def test_drift_summary_rate_bounds(sample_recs):
    drift_df = rolling_drift_score(sample_recs)
    if len(drift_df) == 0:
        pytest.skip("No drift windows computed")
    summary = drift_summary(drift_df)
    assert (summary["drift_rate"] >= 0).all()
    assert (summary["drift_rate"] <= 100).all()


def test_bias_labels_valid(sample_recs):
    result = category_bias(sample_recs)
    assert set(result["bias_label"].unique()).issubset({"over","under","neutral"})