# Weekly Agent Performance Summary
**Period:** {{week_start}} - {{week_end}}
**Prepared by:** Sajan Singh Shergill, Data Science
**Audience:** Product & Engineering

---

## Executive Summary

This report summarises AI job search agent perfromance acorss three dimensions:
recommendation match quality, application funnel conversion, and category-level drift.

---

## 1. Match Quality
| Metric | This Week |
|---|---|
| Mean agent match score | {{match_score_mean}} |
| Mean true Jaccard | {{jaccard_mean}} |
| Mean calibration error | {{calibration_error_mean}} |

**Key finding:** {{match_quality_finding}}

---

## 2. Funnel Conversion

| Stage | Count | % of Recommended | Stage Conversion |
|---|---|---|---|
| Recommended | {{rec_count}} | 100% | — |
| Viewed | {{viewed_count}} | {{viewed_pct}}% | {{view_rate}}% |
| Clicked | {{clicked_count}} | {{clicked_pct}}% | {{click_rate}}% |
| Applied | {{applied_count}} | {{applied_pct}}% | {{apply_rate}}% |

**Key finding:** {{funnel_finding}}

---

## 3. Agent Drift Alerts
| Segment | Drift Rate | Status |
|---|---|---|
{{drift_table_rows}}

**Key finding:** {{drift_finding}}

## Recommended Actions

1. {{action_1}}
2. {{action_2}}
3. {{action_3}}

