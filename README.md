# Job Search Agent Analytics Dashboard

End-to-end analytics pipeline for monitoring AI job search agent performance-tracking match quality, application funnel conversion, and recommendation drift across user segments.

## Overview
This project simulates and analyzes the data layer behind an AI-powered job search agent (insipired by platforms like Jobright). It ingests synthetic user, job posting, and behavioral event data, runs three core analytical modules, and surfaces insights through an interactive Streamlit dashboard and auto-generated weekly summary reports.

Built to mirror real responsibilities at AI-first product companies: intergating data insights into agent decision-making loops and communicating findings to both technical teams and non-technical stakeholders.


## Live DEMO


## Architecture
Raw Synthetic Data
        │
        ▼
Python Ingestion Pipeline (Pandas + Faker → DuckDB)
        │
        ├──▶ Match Quality Module     → Skill overlap score per recommendation
        ├──▶ Funnel Conversion Module → Recommend → Click → Apply rates
        └──▶ Agent Drift Monitor      → Bias detection across user segments
                                              │
                                              ▼
                              Reporting Layer (Plotly + Markdown)
                                              │
                                              ▼
                        Streamlit Dashboard + Weekly Report Notebook

## Key Features
- **Synthetic data generation** - Faker-based pipeline producing realistic user profiles, job postings, agent recommendations, and click/apply events
- **Match quality scoring** - Skill overalp computation between user profiles and recommended jobs, scored per recommendation
- **Funnel analysis** - Stage -by-stage drop-off tracking from recommendation -> click -> application, segmented by job ategory and user experience level
- **Agent drift monitoring** - Statistical detection of whether the agent systematically over/under-recommends certain categories for specific user segments
- **Interactive dashboard** - Streamlit app with date range and segment filters
- **Automated reporting** - Jupyter notebook that generates a weekly PDF/HTML summary report with a plain-language stakeholder memo

## Tech Stack
<img width="535" height="391" alt="image" src="https://github.com/user-attachments/assets/d2847acf-e3f4-494e-8ec3-671836f2b650" />

## Project Structure
<img width="374" height="803" alt="image" src="https://github.com/user-attachments/assets/120d117d-0c18-4291-81a3-f5f39f3934d4" />

## Quickstart
### 1. Clone the repository
bashgit clone https://github.com/sajanshergill/job-search-agent-analytics.git
cd job-search-agent-analytics

### 2. Set up the environment
bashpython -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

### 3. Generate synthetic data
bashpython src/ingestion/generate_data.py --users 5000 --jobs 2000 --events 50000
python src/ingestion/load_to_db.py

### 4. Run the dashboard
bashstreamlit run dashboard/app.py

### 5. Generate a weekly report
bashjupyter nbconvert --to html --execute notebooks/05_weekly_report.ipynb

### Docker (optional)
bashdocker-compose up --build

## Data Schema
users
<img width="558" height="270" alt="image" src="https://github.com/user-attachments/assets/6e2d3d47-44cb-46b9-9080-f58d3680ebe3" />

jobs 
<img width="558" height="270" alt="image" src="https://github.com/user-attachments/assets/fa82b4b2-68b1-4454-b0bd-2a30fe9b93c0" />

recommendations
<img width="559" height="241" alt="image" src="https://github.com/user-attachments/assets/b93dcaee-a036-4e72-ab47-c539e5274650" />

events
<img width="559" height="241" alt="image" src="https://github.com/user-attachments/assets/b55d44de-68ee-405e-837a-dd1ac3dcd704" />

## Analytical Modules
### 1. Match Quality (src/analysis/match_quality.py)
COmputes Jaccard similarity between user.skills and job.requried_skills for each recommendation. Compares computed overlap against agent-assigned match_score to detect miscaliberation. Outpus a calibration scatter and average overlap by job category.

### 2. Funnel Conversion (src/analysis/funnel_conversion.py)
Tracks the conversion rate at each stage: recommendation -> view -> click -> application. Segments results by experience_level and job_category. Identifies which segments show the steepest drop-off.

### 3. Agent Drift Monitor (src/analysis/agent_drift.py)
Aggregates recommendatio distributions per user segment over rolling 7-day windows. First categories where representation deiverges significantly from the overall distribution using a chi-square test. Designed to catch silent drift in agent behavior before it affects user outcomes.

## Dashboard Panels
<img width="610" height="239" alt="image" src="https://github.com/user-attachments/assets/707df355-145b-4b21-a36f-c97c12907f3a" />

### Sample Insights (from synthetic data)
- ENtry-level users showed a 23% lower click-to-apply-rate on Data Engineering roles compared to mid-level users, despite similar recommendation volumes
- Agent match_score overestimated skill overlap by an average of 0.12 for senior-level profiles - indeicating a calibration gap
- "Machine Learning Engineer" postings were over-represented for users with Python skills by 1.8 * relative to the baseline distribution

## Roadmap
- Add A/B testing module for agent recommendation strategy comparison
- Intergate real job posting feed via public API (e.g, Adzuna)
- Add SHAP-based explainability for match score drivers
- Export stakeholder report to PDF via WeasyPrint
- Deploy dashboard to Streamlit Community Cloud

## Skills Demonstrated
Python · SQL (DuckDB) · Pandas · Data Modeling · Funnel Analysis · Statistical Drift Detection · Plotly · Streamlit · Jupyter · Docker · Data Storytelling



