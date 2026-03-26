import pandas as pd
import pytest

from src.analysis.funnel_conversion import (
    drop_off_analysis,
    funnel_by_segment,
    funnel_weekly_trend,
    overall_funnel,
)


@pytest.fixture
def sample_funnel() -> pd.DataFrame:
    return pd.DataFrame({
        "rec_id":           [f"r{i}" for i in range(10)],
        "user_id":          [f"u{i}" for i in range(10)],
        "job_id":           [f"j{i}" for i in range(10)],
        "experience_level": ["entry"]*5 + ["mid"]*5,
        "category":         ["Data Science"]*5 + ["ML Engineering"]*5,
        "match_score":      [0.5]*10,
        "recommended_at":   pd.date_range("2024-01-01", periods=10, freq="D"),
        "viewed":           [1,1,1,0,0,1,1,0,0,0],
        "clicked":          [1,1,0,0,0,1,0,0,0,0],
        "applied":          [1,0,0,0,0,1,0,0,0,0],
    })


def test_overall_funnel_stages(sample_funnel):
    result = overall_funnel(sample_funnel)
    assert list(result["stage"]) == ["recommended","viewed","clicked","applied"]


def test_overall_funnel_counts(sample_funnel):
    result = overall_funnel(sample_funnel)
    assert result[result["stage"] == "recommended"]["count"].values[0] == 10
    assert result[result["stage"] == "viewed"]["count"].values[0]      == 5
    assert result[result["stage"] == "clicked"]["count"].values[0]     == 3
    assert result[result["stage"] == "applied"]["count"].values[0]     == 2


def test_recommended_always_100pct(sample_funnel):
    result = overall_funnel(sample_funnel)
    assert result[result["stage"] == "recommended"]["pct_of_recommended"].values[0] == 100.0


def test_segment_has_rates(sample_funnel):
    result = funnel_by_segment(sample_funnel, "experience_level")
    for col in ["view_rate","click_rate","apply_rate","end_to_end"]:
        assert col in result.columns


def test_weekly_trend_columns(sample_funnel):
    result = funnel_weekly_trend(sample_funnel)
    assert "week" in result.columns and "apply_rate" in result.columns


def test_drop_off_is_dataframe(sample_funnel):
    result = drop_off_analysis(sample_funnel)
    assert isinstance(result, pd.DataFrame)