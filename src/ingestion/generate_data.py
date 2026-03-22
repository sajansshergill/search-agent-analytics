"""
generate_data.py
Generates synthetic users, jobs, recommendations, and events.

Usage
-----
    python src/ingestion/generate_data.py
    python src/ingestion/generate_data.py --users 1000 --jobs 500 --events 10000
"""

from __future__ import annotations

import argparse
import logging
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from src.utils.config import (
    DATA_RAW,
    DEFAULT_EVENTS,
    DEFAULT_JOBS,
    DEFAULT_USERS,
    EXPERIENCE_LEVELS,
    FUNNEL_PROBS,
    JOB_CATEGORIES,
    RANDOM_SEED,
    SKILLS_BY_LEVEL,
    SKILLS_POOL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

SIM_END   = datetime(2024, 6, 30)
SIM_START = SIM_END - timedelta(days=90)


def _rand_skills(level: str) -> list[str]:
    lo, hi = SKILLS_BY_LEVEL[level]
    n = random.randint(lo, hi)
    return random.sample(SKILLS_POOL, k=min(n, len(SKILLS_POOL)))


def _rand_ts(start: datetime = SIM_START, end: datetime = SIM_END) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta))


def generate_users(n: int) -> pd.DataFrame:
    logger.info("Generating %d users ...", n)
    records = []
    for _ in range(n):
        level  = random.choice(EXPERIENCE_LEVELS)
        skills = _rand_skills(level)
        records.append({
            "user_id":          str(uuid.uuid4()),
            "name":             fake.name(),
            "experience_level": level,
            "skills":           ",".join(skills),
            "num_skills":       len(skills),
            "target_role":      random.choice(JOB_CATEGORIES),
            "location":         f"{fake.city()}, {fake.state_abbr()}",
            "created_at":       _rand_ts(SIM_START - timedelta(days=180), SIM_START),
        })
    df = pd.DataFrame(records)
    logger.info("Users generated: %d rows", len(df))
    return df


def generate_jobs(n: int) -> pd.DataFrame:
    logger.info("Generating %d jobs ...", n)
    records = []
    for _ in range(n):
        n_skills        = random.randint(4, 12)
        required_skills = random.sample(SKILLS_POOL, k=n_skills)
        category        = random.choice(JOB_CATEGORIES)
        records.append({
            "job_id":             str(uuid.uuid4()),
            "title":              f"{random.choice(['Senior ', 'Lead ', 'Staff ', ''])}{category.split()[0]} Engineer",
            "category":           category,
            "company":            fake.company(),
            "required_skills":    ",".join(required_skills),
            "num_required_skills":n_skills,
            "location":           f"{fake.city()}, {fake.state_abbr()}",
            "salary_min":         random.randint(80, 160) * 1000,
            "salary_max":         random.randint(160, 300) * 1000,
            "posted_at":          _rand_ts(),
        })
    df = pd.DataFrame(records)
    logger.info("Jobs generated: %d rows", len(df))
    return df


def generate_recommendations(
    users: pd.DataFrame, jobs: pd.DataFrame, recs_per_user: int = 10
) -> pd.DataFrame:
    logger.info("Generating recommendations (%d per user) ...", recs_per_user)
    records = []
    job_ids = jobs["job_id"].tolist()

    for _, user in users.iterrows():
        user_skills  = set(user["skills"].split(","))
        sampled_jobs = random.sample(job_ids, k=min(recs_per_user, len(job_ids)))

        for job_id in sampled_jobs:
            job_row    = jobs[jobs["job_id"] == job_id].iloc[0]
            job_skills = set(job_row["required_skills"].split(","))

            intersection  = len(user_skills & job_skills)
            union         = len(user_skills | job_skills)
            true_jaccard  = intersection / union if union > 0 else 0.0

            noise       = np.random.normal(loc=0.08, scale=0.06)
            agent_score = float(np.clip(true_jaccard + noise, 0.0, 1.0))

            rec_ts = _rand_ts(
                start=max(SIM_START, job_row["posted_at"]),
                end=SIM_END,
            )
            records.append({
                "rec_id":           str(uuid.uuid4()),
                "user_id":          user["user_id"],
                "job_id":           job_id,
                "experience_level": user["experience_level"],
                "category":         job_row["category"],
                "true_jaccard":     round(true_jaccard, 4),
                "match_score":      round(agent_score, 4),
                "recommended_at":   rec_ts,
            })

    df = pd.DataFrame(records)
    logger.info("Recommendations generated: %d rows", len(df))
    return df


def generate_events(
    recommendations: pd.DataFrame, target_events: int
) -> pd.DataFrame:
    logger.info("Generating events (target ~%d) ...", target_events)
    records = []

    for _, rec in recommendations.iterrows():
        rec_ts: datetime = rec["recommended_at"]

        if random.random() < FUNNEL_PROBS["viewed"]:
            records.append({
                "event_id":         str(uuid.uuid4()),
                "user_id":          rec["user_id"],
                "job_id":           rec["job_id"],
                "rec_id":           rec["rec_id"],
                "experience_level": rec["experience_level"],
                "category":         rec["category"],
                "event_type":       "viewed",
                "occurred_at":      rec_ts + timedelta(minutes=random.randint(1, 60)),
            })

            if random.random() < FUNNEL_PROBS["clicked"]:
                records.append({
                    "event_id":         str(uuid.uuid4()),
                    "user_id":          rec["user_id"],
                    "job_id":           rec["job_id"],
                    "rec_id":           rec["rec_id"],
                    "experience_level": rec["experience_level"],
                    "category":         rec["category"],
                    "event_type":       "clicked",
                    "occurred_at":      rec_ts + timedelta(minutes=random.randint(5, 120)),
                })

                if random.random() < FUNNEL_PROBS["applied"]:
                    records.append({
                        "event_id":         str(uuid.uuid4()),
                        "user_id":          rec["user_id"],
                        "job_id":           rec["job_id"],
                        "rec_id":           rec["rec_id"],
                        "experience_level": rec["experience_level"],
                        "category":         rec["category"],
                        "event_type":       "applied",
                        "occurred_at":      rec_ts + timedelta(hours=random.randint(1, 48)),
                    })

        if len(records) >= target_events:
            break

    df = pd.DataFrame(records)
    logger.info("Events generated: %d rows", len(df))
    return df


def main(n_users: int, n_jobs: int, n_events: int) -> None:
    users  = generate_users(n_users)
    jobs   = generate_jobs(n_jobs)
    recs   = generate_recommendations(users, jobs)
    events = generate_events(recs, target_events=n_events)

    users.to_csv(DATA_RAW / "users.csv",           index=False)
    jobs.to_csv(DATA_RAW / "jobs.csv",             index=False)
    recs.to_csv(DATA_RAW / "recommendations.csv",  index=False)
    events.to_csv(DATA_RAW / "events.csv",         index=False)

    logger.info("All CSVs written to %s", DATA_RAW)
    logger.info(
        "Summary → users: %d | jobs: %d | recommendations: %d | events: %d",
        len(users), len(jobs), len(recs), len(events),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users",  type=int, default=DEFAULT_USERS)
    parser.add_argument("--jobs",   type=int, default=DEFAULT_JOBS)
    parser.add_argument("--events", type=int, default=DEFAULT_EVENTS)
    args = parser.parse_args()
    main(n_users=args.users, n_jobs=args.jobs, n_events=args.events)