import pandas as pd
import pytest

from src.analysis.match_quality import (
    calibration_by_category,
    calibration_by_experience,
    calibration_summary,
    score_distribution_bins,
    top_miscalibrated_categories,
)


@pytest.fixture
def sample_recs() -> pd.DataFrame:
    return pd.DataFrame({
        "rec_id":            ["r1","r2","r3","r4","r5","r6"],
        "user_id":           ["u1"]*6,
        "job_id":            ["j1","j2","j3","j4","j5","j6"],
        "experience_level":  ["entry","entry","mid","mid","senior","senior"],
        "category":          ["Data Science","Data Science","ML Engineering",
                              "ML Engineering","Data Engineering","Data Engineering"],
        "true_jaccard":      [0.3, 0.5, 0.4, 0.6, 0.7, 0.8],
        "match_score":       [0.4, 0.6, 0.5, 0.7, 0.75, 0.85],
        "calibration_error": [0.1, 0.1, 0.1, 0.1, 0.05, 0.05],
        "recommended_at":    pd.date_range("2024-01-01", periods=6, freq="D"),
        "user_location":     ["NY"]*6,
        "company":           ["ACME"]*6,
        "salary_min":        [100_000]*6,
        "salary_max":        [150_000]*6,
    })


def test_calibration_summary_shape(sample_recs):
    result = calibration_summary(sample_recs)
    assert set(result["metric"]) == {"true_jaccard", "match_score", "calibration_error"}
    assert "mean" in result.columns and "median" in result.columns


def test_calibration_error_positive(sample_recs):
    result = calibration_summary(sample_recs)
    err = result[result["metric"] == "calibration_error"]["mean"].values[0]
    assert err > 0


def test_calibration_by_category_count(sample_recs):
    result = calibration_by_category(sample_recs)
    assert len(result) == sample_recs["category"].nunique()


def test_calibration_by_experience_levels(sample_recs):
    result = calibration_by_experience(sample_recs)
    assert set(result["experience_level"]) == {"entry", "mid", "senior"}


def test_score_bins_total(sample_recs):
    result = score_distribution_bins(sample_recs, col="match_score", bins=5)
    assert result["count"].sum() == len(sample_recs)


def test_top_miscalibrated_count(sample_recs):
    result = top_miscalibrated_categories(sample_recs, top_n=2)
    assert len(result) == 2
    assert "abs_error" in result.columns