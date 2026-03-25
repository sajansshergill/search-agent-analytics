"""
charts.py
Reusable Plotly chart builders for the dashboard and reports.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = px.colors.qualitative.Set2

LAYOUT_BASE = dict(
    font_family="Inter, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


# ── Match Quality ─────────────────────────────────────────────────────────────

def calibration_scatter(df: pd.DataFrame) -> go.Figure:
    sample = df.sample(min(3000, len(df)), random_state=42)
    fig = px.scatter(
        sample, x="true_jaccard", y="match_score", color="experience_level",
        opacity=0.45, color_discrete_sequence=PALETTE,
        labels={"true_jaccard": "True Jaccard", "match_score": "Agent match score"},
        title="Agent score vs true skill overlap",
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                  line=dict(dash="dash", color="gray", width=1))
    fig.update_layout(**LAYOUT_BASE)
    return fig


def calibration_error_bar(by_category: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        by_category.sort_values("calibration_error"),
        x="calibration_error", y="category", orientation="h",
        color="calibration_error",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        labels={"calibration_error": "Mean calibration error", "category": ""},
        title="Calibration error by job category",
    )
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
    return fig


def score_histogram(score_dist: pd.DataFrame, title: str = "Score distribution") -> go.Figure:
    fig = px.bar(
        score_dist, x="bin", y="count", title=title,
        labels={"bin": "Score range", "count": "Recommendations"},
        color_discrete_sequence=[PALETTE[0]],
    )
    fig.update_layout(**LAYOUT_BASE)
    fig.update_xaxes(tickangle=-45)
    return fig


# ── Funnel ────────────────────────────────────────────────────────────────────

def funnel_waterfall(overall: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Funnel(
        y=overall["stage"].str.capitalize(),
        x=overall["count"],
        textinfo="value+percent initial",
        marker=dict(color=["#3498db", "#2ecc71", "#f39c12", "#e74c3c"]),
    ))
    fig.update_layout(title="Job application funnel", **LAYOUT_BASE)
    return fig


def funnel_by_segment_bar(segment_df: pd.DataFrame, segment_col: str) -> go.Figure:
    melted = segment_df[[segment_col, "view_rate", "click_rate", "apply_rate"]].melt(
        id_vars=segment_col, var_name="stage", value_name="rate"
    )
    fig = px.bar(
        melted, x=segment_col, y="rate", color="stage", barmode="group",
        color_discrete_sequence=PALETTE,
        labels={"rate": "Conversion rate (%)", segment_col: ""},
        title=f"Funnel conversion by {segment_col.replace('_', ' ')}",
    )
    fig.update_layout(**LAYOUT_BASE)
    return fig


def apply_rate_trend(weekly: pd.DataFrame) -> go.Figure:
    fig = px.line(
        weekly, x="week", y="apply_rate", markers=True,
        labels={"week": "Week", "apply_rate": "Apply rate (%)"},
        title="Weekly apply rate trend",
        color_discrete_sequence=[PALETTE[2]],
    )
    fig.update_layout(**LAYOUT_BASE)
    return fig


# ── Drift ─────────────────────────────────────────────────────────────────────

def drift_heatmap(drift_df: pd.DataFrame) -> go.Figure:
    pivot = drift_df.pivot_table(
        index="segment", columns="week", values="chi2_stat", aggfunc="mean"
    )
    fig = px.imshow(
        pivot, color_continuous_scale="OrRd",
        labels=dict(color="Chi² stat"),
        title="Agent drift score by segment × week",
        aspect="auto",
    )
    fig.update_layout(**LAYOUT_BASE)
    return fig


def drift_alert_bars(summary: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        summary.sort_values("drift_rate"),
        x="drift_rate", y="segment", orientation="h",
        color="drift_rate", color_continuous_scale=["#2ecc71", "#e74c3c"],
        labels={"drift_rate": "Drift rate (%)", "segment": ""},
        title="Drift rate by user segment",
    )
    fig.add_vline(x=20, line_dash="dash", line_color="#e74c3c",
                  annotation_text="20% threshold", annotation_position="top right")
    fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
    return fig


def category_bias_heatmap(cat_bias: pd.DataFrame) -> go.Figure:
    pivot = cat_bias.pivot_table(
        index="category", columns="experience_level",
        values="bias_ratio", aggfunc="mean"
    )
    fig = px.imshow(
        pivot, color_continuous_scale="RdBu_r", color_continuous_midpoint=1.0,
        labels=dict(color="Bias ratio"),
        title="Recommendation bias ratio (1.0 = neutral)",
        aspect="auto", text_auto=".2f",
    )
    fig.update_layout(**LAYOUT_BASE)
    return fig


# ── KPI ───────────────────────────────────────────────────────────────────────

def kpi_indicator(
    value: float, label: str, ref: float | None = None, suffix: str = ""
) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="number+delta" if ref is not None else "number",
        value=value,
        delta={"reference": ref, "relative": False} if ref is not None else None,
        number={"suffix": suffix, "font": {"size": 36}},
        title={"text": label, "font": {"size": 14}},
    ))
    fig.update_layout(height=140, margin=dict(l=10, r=10, t=40, b=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig