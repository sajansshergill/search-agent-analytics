"""
app.py
Streamlit dashboard — Job Search Agent Analytics.

Run: streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import streamlit as st
from src.analysis import agent_drift, funnel_conversion, match_quality
from src.reporting.charts import (
    apply_rate_trend,
    calibration_error_bar,
    calibration_scatter,
    category_bias_heatmap,
    drift_alert_bars,
    drift_heatmap,
    funnel_by_segment_bar,
    funnel_waterfall,
    kpi_indicator,
    score_histogram,
)
from src.utils.config import DB_PATH, EXPERIENCE_LEVELS, JOB_CATEGORIES
from src.utils.db import table_exists

st.set_page_config(
    page_title="Agent Analytics Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _db_ready() -> bool:
    return DB_PATH.exists() and table_exists("recommendations")


if not _db_ready():
    st.error(
        "**Database not found.** Run the pipeline first:\n\n"
        "```bash\nmake generate\nmake load\n```"
    )
    st.stop()


@st.cache_data(ttl=300, show_spinner="Loading match quality data ...")
def load_match():
    return match_quality.run()


@st.cache_data(ttl=300, show_spinner="Loading funnel data ...")
def load_funnel():
    return funnel_conversion.run()


@st.cache_data(ttl=300, show_spinner="Loading drift data ...")
def load_drift():
    return agent_drift.run()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Agent Analytics")
    st.caption("Job Search Agent · Performance Dashboard")
    st.divider()
    st.subheader("Filters")

    selected_levels = st.multiselect(
        "Experience level", options=EXPERIENCE_LEVELS, default=EXPERIENCE_LEVELS
    )
    selected_categories = st.multiselect(
        "Job category", options=JOB_CATEGORIES, default=JOB_CATEGORIES
    )
    st.divider()
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Load ──────────────────────────────────────────────────────────────────────
mq = load_match()
fn = load_funnel()
dr = load_drift()


def filter_df(df: pd.DataFrame) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if "experience_level" in df.columns:
        mask &= df["experience_level"].isin(selected_levels)
    if "category" in df.columns:
        mask &= df["category"].isin(selected_categories)
    return df[mask]


mq_raw = filter_df(mq["raw"])
fn_raw = filter_df(fn["raw"])
dr_raw = filter_df(dr["raw"])

# Recompute on filtered data
filtered_summary   = match_quality.calibration_summary(mq_raw)
filtered_by_cat    = match_quality.calibration_by_category(mq_raw)
filtered_by_exp    = match_quality.calibration_by_experience(mq_raw)
filtered_funnel    = funnel_conversion.overall_funnel(fn_raw)
filtered_fn_exp    = funnel_conversion.funnel_by_segment(fn_raw, "experience_level")
filtered_fn_cat    = funnel_conversion.funnel_by_segment(fn_raw, "category")
filtered_weekly    = funnel_conversion.funnel_weekly_trend(fn_raw)
filtered_drift     = agent_drift.rolling_drift_score(dr_raw)
filtered_drift_sum = agent_drift.drift_summary(filtered_drift)
filtered_cat_bias  = agent_drift.category_bias(dr_raw)


# ── KPI Row ───────────────────────────────────────────────────────────────────
st.header("📊 Weekly snapshot")
k1, k2, k3, k4, k5 = st.columns(5)

mean_match  = round(filtered_summary[filtered_summary["metric"] == "match_score"]["mean"].values[0] * 100, 1)
calib_err   = round(filtered_summary[filtered_summary["metric"] == "calibration_error"]["mean"].values[0], 3)
applied_row = filtered_funnel[filtered_funnel["stage"] == "applied"]
apply_pct   = applied_row["pct_of_recommended"].values[0] if len(applied_row) else 0
drift_pct   = round(filtered_drift["drifted"].mean() * 100, 1) if len(filtered_drift) else 0
total_recs  = filtered_funnel[filtered_funnel["stage"] == "recommended"]["count"].values[0] if len(filtered_funnel) else 0

with k1: st.plotly_chart(kpi_indicator(mean_match,       "Avg match score",  suffix="%"), use_container_width=True)
with k2: st.plotly_chart(kpi_indicator(calib_err,        "Calibration error"           ), use_container_width=True)
with k3: st.plotly_chart(kpi_indicator(apply_pct,        "Apply rate",       suffix="%"), use_container_width=True)
with k4: st.plotly_chart(kpi_indicator(drift_pct,        "Drift alert rate", suffix="%"), use_container_width=True)
with k5: st.plotly_chart(kpi_indicator(float(total_recs),"Total recs"                  ), use_container_width=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎯 Match Quality", "🔽 Funnel Conversion", "📡 Agent Drift", "📋 Raw Data"]
)

with tab1:
    st.subheader("Match quality overview")
    c1, c2 = st.columns([3, 2])
    with c1: st.plotly_chart(calibration_scatter(mq_raw), use_container_width=True)
    with c2: st.plotly_chart(calibration_error_bar(filtered_by_cat), use_container_width=True)
    c3, c4 = st.columns(2)
    with c3: st.plotly_chart(score_histogram(match_quality.score_distribution_bins(mq_raw, "match_score"), "Agent match score distribution"), use_container_width=True)
    with c4: st.plotly_chart(score_histogram(match_quality.score_distribution_bins(mq_raw, "true_jaccard"), "True Jaccard distribution"), use_container_width=True)
    st.subheader("Calibration by experience level")
    st.dataframe(filtered_by_exp, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Application funnel")
    c1, c2 = st.columns([1, 2])
    with c1: st.plotly_chart(funnel_waterfall(filtered_funnel), use_container_width=True)
    with c2: st.plotly_chart(apply_rate_trend(filtered_weekly), use_container_width=True)
    st.plotly_chart(funnel_by_segment_bar(filtered_fn_exp, "experience_level"), use_container_width=True)
    st.plotly_chart(funnel_by_segment_bar(filtered_fn_cat, "category"), use_container_width=True)
    st.subheader("Top drop-off segments")
    st.dataframe(funnel_conversion.drop_off_analysis(fn_raw), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Agent drift monitor")
    if len(filtered_drift) == 0:
        st.info("Not enough data. Try increasing dataset size or selecting more segments.")
    else:
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(drift_alert_bars(filtered_drift_sum), use_container_width=True)
        with c2: st.plotly_chart(drift_heatmap(filtered_drift), use_container_width=True)
        st.plotly_chart(category_bias_heatmap(filtered_cat_bias), use_container_width=True)
        st.subheader("Drift summary by segment")
        st.dataframe(filtered_drift_sum, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Explore raw tables")
    choice = st.selectbox("Table", ["recommendations", "funnel", "drift windows"])
    if choice == "recommendations":
        st.dataframe(mq_raw.head(500), use_container_width=True, hide_index=True)
    elif choice == "funnel":
        st.dataframe(fn_raw.head(500), use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered_drift.head(500), use_container_width=True, hide_index=True)