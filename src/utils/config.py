"""
config.py
Central configuration: paths, constants, segment definitions.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parents[2]
DATA_RAW      = ROOT_DIR / "data" / "raw"
DATA_PROCESSED= ROOT_DIR / "data" / "processed"
REPORTS_DIR   = ROOT_DIR / "reports"
DB_PATH       = DATA_PROCESSED / "agent_analytics.duckdb"

for _d in [DATA_RAW, DATA_PROCESSED, REPORTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Synthetic data defaults ───────────────────────────────────────────────────
DEFAULT_USERS  = 5_000
DEFAULT_JOBS   = 2_000
DEFAULT_EVENTS = 50_000
RANDOM_SEED    = 42

# ── Domain vocabulary ─────────────────────────────────────────────────────────
EXPERIENCE_LEVELS = ["entry", "mid", "senior"]

JOB_CATEGORIES = [
    "Data Engineering",
    "Data Science",
    "Machine Learning Engineering",
    "Analytics Engineering",
    "Business Intelligence",
    "AI Research",
    "Product Analytics",
    "Data Governance",
]

SKILLS_POOL = [
    "Python", "R", "SQL", "Scala", "Java", "Go",
    "Pandas", "NumPy", "Scikit-learn", "PyTorch", "TensorFlow",
    "Spark", "Kafka", "Airflow", "dbt", "MLflow",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes",
    "Tableau", "Power BI", "Looker", "Plotly", "Streamlit",
    "PostgreSQL", "BigQuery", "Snowflake", "DuckDB", "Redshift",
    "Git", "Linux", "REST APIs", "Statistics", "A/B Testing",
]

SKILLS_BY_LEVEL = {
    "entry":  (3, 7),
    "mid":    (6, 12),
    "senior": (10, 18),
}

EVENT_TYPES = ["viewed", "clicked", "applied"]

FUNNEL_PROBS = {
    "viewed":  0.70,
    "clicked": 0.40,
    "applied": 0.20,
}

# ── Drift detection ───────────────────────────────────────────────────────────
DRIFT_WINDOW_DAYS   = 7
DRIFT_CHI2_ALPHA    = 0.05
MIN_RECS_FOR_DRIFT  = 30

# ── MLflow ────────────────────────────────────────────────────────────────────
MLFLOW_EXPERIMENT = "agent-analytics"