"""
Generate a SYNTHETIC dataset of Indian data-analytics job postings.

All companies are fictional. Salary bands, skill mixes and city premiums are
modelled to mirror realistic Indian market patterns, but every row is
generated — this is NOT scraped from real job boards.

Run:  python generate_data.py
Seed: 42 (reproducible)
"""

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_POSTINGS = 1200
END_DATE = date(2026, 10, 19)  # "today" for this project

random.seed(SEED)
np.random.seed(SEED)

BASE = Path(__file__).parent
OUT = BASE / "data" / "job_postings.csv"

# ---------------------------------------------------------------- companies
PREFIXES = [
    "NorthPeak", "DataVista", "InsightForge", "QuantNest", "BlueOrbit",
    "MetricMinds", "PixelLedger", "NovaGrid", "Crestline", "BrightStack",
    "TrueSignal", "ZenithWorks", "CloudSlate", "PrimeVector", "SwiftKite",
    "ApexLoop", "ClearPath", "DeepCurrent", "EdgeStone", "FluxWorks",
    "GoldRidge", "HarborLine", "IronPeak", "JetStream", "KeyStone",
    "LumenArc", "MoonRidge", "NimbusWorks", "OpalGrid", "PineCrest",
]
SUFFIXES = [
    "Analytics", "Labs", "Technologies", "Solutions", "Systems",
    "Consulting", "Insights", "Dataworks",
]
COMPANIES = [f"{p} {s}" for p in PREFIXES for s in SUFFIXES]
random.shuffle(COMPANIES)
COMPANIES = COMPANIES[:120]  # 120 fictional employers

# ------------------------------------------------------------------- cities
CITIES = [
    "Delhi NCR", "Mumbai", "Bengaluru", "Hyderabad", "Chennai", "Pune",
    "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
]
CITY_W = [0.18, 0.16, 0.18, 0.12, 0.09, 0.10, 0.06, 0.04, 0.04, 0.03]
# Tier-1 salary multiplier (relative to baseline)
CITY_MULT = {
    "Delhi NCR": 1.07, "Mumbai": 1.08, "Bengaluru": 1.08, "Hyderabad": 1.05,
    "Chennai": 1.03, "Pune": 1.05, "Kolkata": 1.00, "Ahmedabad": 0.97,
    "Jaipur": 0.95, "Lucknow": 0.93,
}

# ------------------------------------------------------------------- titles
TITLES = ["Data Analyst", "Business Analyst", "MIS Executive",
          "Senior Data Analyst", "Analytics Associate"]
TITLE_W = [0.55, 0.15, 0.13, 0.10, 0.07]

SKILLS = ["SQL", "Python", "Excel", "Power BI", "Tableau", "Statistics",
          "Machine Learning", "Data Modeling", "ETL", "Power Query", "DAX",
          "R", "SAS", "Communication", "Stakeholder Management"]

# Per-title probability of each skill appearing in a posting
TITLE_SKILL_P = {
    "Data Analyst":        [0.95, 0.55, 0.90, 0.60, 0.35, 0.50, 0.15, 0.25, 0.25, 0.40, 0.35, 0.15, 0.10, 0.50, 0.20],
    "Business Analyst":    [0.80, 0.25, 0.90, 0.45, 0.25, 0.35, 0.05, 0.40, 0.15, 0.30, 0.20, 0.05, 0.10, 0.85, 0.80],
    "MIS Executive":       [0.60, 0.10, 0.98, 0.35, 0.10, 0.15, 0.02, 0.10, 0.15, 0.60, 0.25, 0.03, 0.08, 0.60, 0.35],
    "Senior Data Analyst": [0.95, 0.85, 0.70, 0.55, 0.35, 0.70, 0.55, 0.60, 0.55, 0.25, 0.30, 0.25, 0.10, 0.60, 0.45],
    "Analytics Associate": [0.90, 0.60, 0.90, 0.50, 0.30, 0.60, 0.12, 0.20, 0.20, 0.35, 0.30, 0.15, 0.08, 0.55, 0.20],
}

# --------------------------------------------------------------- experience
BANDS = ["fresher", "1-3", "3-5", "5+"]
BAND_W = [0.22, 0.38, 0.27, 0.13]
BAND_EXP = {  # (min, max) years sampling ranges
    "fresher": (0, 1),
    "1-3": (1, 3),
    "3-5": (3, 5),
    "5+": (5, 9),
}
BAND_BASE_MID = {"fresher": 4.5, "1-3": 7.5, "3-5": 11.5, "5+": 17.0}

COMPANY_TYPES = ["Startup", "Mid-size", "MNC"]
COMPANY_W = [0.30, 0.42, 0.28]
COMPANY_MULT = {"Startup": 0.97, "Mid-size": 1.00, "MNC": 1.05}

WORK_MODES = ["On-site", "Hybrid", "Remote"]
WORK_W = [0.55, 0.30, 0.15]

PREMIUM_SKILLS = {"Python": 1.05, "Machine Learning": 1.06, "Data Modeling": 1.03}


def pick_skills(title: str) -> str:
    probs = TITLE_SKILL_P[title]
    chosen = [s for s, p in zip(SKILLS, probs) if random.random() < p]
    # Guarantee a sensible 3–7 skills per posting
    if len(chosen) < 3:
        for s in sorted(SKILLS, key=lambda x: -TITLE_SKILL_P[title][SKILLS.index(x)]):
            if s not in chosen:
                chosen.append(s)
            if len(chosen) == 3:
                break
    if len(chosen) > 7:
        chosen = sorted(chosen,
                        key=lambda x: -TITLE_SKILL_P[title][SKILLS.index(x)])[:7]
    random.shuffle(chosen)
    return ";".join(chosen)


def salary_for(band: str, city: str, ctype: str, skills: str):
    mid = BAND_BASE_MID[band] * np.random.uniform(0.88, 1.12)
    mid *= CITY_MULT[city] * COMPANY_MULT[ctype]
    for sk, mult in PREMIUM_SKILLS.items():
        if sk in skills.split(";"):
            mid *= mult
    width = mid * np.random.uniform(0.22, 0.34)
    lo = max(2.5, round((mid - width / 2) * 2) / 2)
    hi = round((mid + width / 2) * 2) / 2
    return lo, hi


rows = []
for i in range(N_POSTINGS):
    band = random.choices(BANDS, weights=BAND_W)[0]
    exp_lo, exp_hi = BAND_EXP[band]
    exp_min = exp_lo if band != "5+" else random.randint(5, 6)
    exp_max = exp_hi if band != "5+" else random.randint(7, 10)
    if band == "fresher":
        exp_min, exp_max = 0, random.choice([0, 1])

    title = random.choices(TITLES, weights=TITLE_W)[0]
    city = random.choices(CITIES, weights=CITY_W)[0]
    ctype = random.choices(COMPANY_TYPES, weights=COMPANY_W)[0]
    wmode = random.choices(WORK_MODES, weights=WORK_W)[0]
    skills = pick_skills(title)
    sal_lo, sal_hi = salary_for(band, city, ctype, skills)
    posted = END_DATE - timedelta(days=random.randint(0, 89))

    rows.append({
        "job_id": f"JMA-{i + 1:04d}",
        "job_title": title,
        "company": random.choice(COMPANIES),
        "city": city,
        "exp_min_yrs": exp_min,
        "exp_max_yrs": exp_max,
        "salary_min_lpa": sal_lo,
        "salary_max_lpa": sal_hi,
        "skills": skills,
        "company_type": ctype,
        "work_mode": wmode,
        "posted_date": posted.isoformat(),
    })

df = pd.DataFrame(rows).sort_values("posted_date", ascending=False).reset_index(drop=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {len(df)} synthetic postings -> {OUT}")
print(df.head(3).to_string(index=False))
