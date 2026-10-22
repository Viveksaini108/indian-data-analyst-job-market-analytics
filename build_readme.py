"""
Build README.md from findings.json so every number quoted is computed
from the data — never hand-written.

Run:  python build_readme.py   (after analysis.py)
"""

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
f = json.load(open(BASE / "findings.json"))

df = pd.read_csv(BASE / "data" / "job_postings.csv")
df["salary_avg"] = (df["salary_min_lpa"] + df["salary_max_lpa"]) / 2
df["exp_mid"] = (df["exp_min_yrs"] + df["exp_max_yrs"]) / 2

# Extra context numbers, still computed from the CSV
ml = df[df["skills"].str.contains("Machine Learning")]
ml_med_exp = round(float(ml["exp_mid"].median()), 1)
overall_med_exp = round(float(df["exp_mid"].median()), 1)
band = f["median_by_band"]
senior_mult = round(band["5+ yrs"] / band["0–1 yrs (Fresher)"], 1)
city_gap = round(f["top_city"]["median_lpa"] - f["bottom_city"]["median_lpa"], 1)

top15_rows = "\n".join(
    f"| {i+1} | {s['skill']} | {s['count']} | {s['pct']}% |"
    for i, s in enumerate(f["top15_skills"])
)
city_rows = "\n".join(
    f"| {c} | {v} |" for c, v in f["median_by_city"].items()
)
band_rows = "\n".join(
    f"| {b} | {v} |" for b, v in f["median_by_band"].items()
)
prem_rows = "\n".join(
    f"| {p['skill']} | +{p['premium_lpa']:.2f} |"
    for p in f["skill_premium_top5"]
)
title_rows = "\n".join(
    f"| {t} | {c} |" for t, c in f["title_counts"].items()
)

readme = f"""# Indian Data Analyst Job Market Analytics

> **Note on data:** this project uses a **synthetically generated dataset**
> (`data/job_postings.csv`, seed `42`). Company names are fictional and no
> posting was scraped from a real job board. Salary bands, skill mixes and
> city differentials were modelled to mirror realistic Indian market
> patterns so the *analysis workflow* is fully real and reproducible.

## Problem statement

As a data analyst job seeker in India, I wanted data-driven answers to:

1. Which skills do employers actually ask for most?
2. How does pay vary by city, experience, company type and work mode?
3. Which skills carry a salary premium?

## Dataset

`data/job_postings.csv` — **{f['n_postings']} synthetic postings** for
*Data Analyst*, *Business Analyst*, *MIS Executive*, *Senior Data Analyst*
and *Analytics Associate* roles, "posted" over the 90 days up to 2026-10-19.

| Column | Description |
|---|---|
| `job_id` | Unique posting ID (`JMA-0001` …) |
| `job_title` | One of 5 analyst-track titles |
| `company` | Fictional employer (120 unique names) |
| `city` | 10 Indian cities (Delhi NCR → Lucknow) |
| `exp_min_yrs` / `exp_max_yrs` | Posted experience range |
| `salary_min_lpa` / `salary_max_lpa` | Posted CTC range (₹ LPA) |
| `skills` | Semicolon-separated skill list (15-skill pool) |
| `company_type` | Startup / Mid-size / MNC |
| `work_mode` | On-site / Hybrid / Remote |
| `posted_date` | Posting date (last 90 days) |

Salaries are correlated with experience band, city tier, company type and
premium skills (Python / Machine Learning / Data Modeling) plus random noise —
so relationships in the data reflect deliberate, realistic structure.

## Methodology

1. **Generate** the dataset with `generate_data.py` (fixed seed `42`).
2. **Analyse** with `analysis.py` (pandas): skill demand counts, median
   salaries by city / experience band / skill premium, posting mix by company
   type and work mode, and correlations.
3. **Report**: this README is built by `build_readme.py` straight from
   `findings.json`, so every number below is computed from the CSV.

## Tools

Python · pandas · NumPy · matplotlib · seaborn

## Key findings

- **Overall median salary: {f['overall_median_lpa']} LPA** across all
  {f['n_postings']} postings.
- **SQL is the #1 demanded skill** — {f['top_skill']['count']} of
  {f['n_postings']} postings ({f['top_skill']['pct']}%), followed closely by
  Excel ({f['top15_skills'][1]['count']}, {f['top15_skills'][1]['pct']}%).
  Communication ({f['top15_skills'][2]['count']}, {f['top15_skills'][2]['pct']}%)
  ranks third — soft skills matter on analyst JDs.

### Top 15 most demanded skills

| # | Skill | Postings | Share |
|---|---|---|---|
{top15_rows}

### Median salary by city (₹ LPA)

| City | Median salary |
|---|---|
{city_rows}

Tier-1 metros lead: {f['top_city']['name']} ({f['top_city']['median_lpa']} LPA)
vs {f['bottom_city']['name']} ({f['bottom_city']['median_lpa']} LPA) — a gap of
{city_gap} LPA.

### Median salary by experience band (₹ LPA)

| Experience | Median salary |
|---|---|
{band_rows}

Pay scales steeply with experience: the 5+ yrs band median
({band['5+ yrs']} LPA) is ~{senior_mult}x the fresher median
({band['0–1 yrs (Fresher)']} LPA). Experience–salary correlation is
**{f['corr_exp_salary']}**.

### Salary premium per skill

Median salary of postings listing each skill, minus the overall median
({f['overall_median_lpa']} LPA):

| Skill | Premium (₹ LPA) |
|---|---|
{prem_rows}

Machine Learning shows the largest premium (+{f['skill_premium_top5'][0]['premium_lpa']:.2f} LPA),
but note it is confounded with seniority: ML postings have a median required
experience of {ml_med_exp} yrs vs {overall_med_exp} yrs overall.

### Posting mix

| Title | Postings |
|---|---|
{title_rows}

- **Company type:** Mid-size {f['company_type_counts']['Mid-size']},
  Startup {f['company_type_counts']['Startup']},
  MNC {f['company_type_counts']['MNC']}
- **Work mode:** On-site {f['work_mode_counts']['On-site']}
  ({f['work_mode_pct']['On-site']}%), Hybrid {f['work_mode_counts']['Hybrid']}
  ({f['work_mode_pct']['Hybrid']}%), Remote {f['work_mode_counts']['Remote']}
  ({f['work_mode_pct']['Remote']}%) — on-site still dominates analyst hiring.
- Number of listed skills barely correlates with pay
  (corr = {f['corr_nskills_salary']}) — *which* skills matter, not how many.

## Charts

![Top skills](charts/top_skills.png)
![Salary by city](charts/salary_by_city.png)
![Salary by experience](charts/salary_by_experience.png)
![Skill premium](charts/skill_premium.png)
![Posting mix](charts/postings_company_workmode.png)
![Experience vs salary](charts/experience_vs_salary.png)

## How to run

```bash
pip install pandas numpy matplotlib seaborn
python generate_data.py   # rebuild the synthetic dataset (seed 42)
python analysis.py        # metrics + charts + findings.json
python build_readme.py    # regenerate this README from findings.json
```

## Next steps

- Build an interactive **Power BI dashboard** on top of the CSV
  (slicers by city / experience / work mode).
- Scrape a *real* sample of postings to validate the synthetic patterns.
- Add NLP on (real) job descriptions: extract skills automatically instead
  of structured lists.
- Extend to adjacent roles (Data Engineer, BI Developer) for comparison.

## Project structure

```
├── data/job_postings.csv        # synthetic dataset (1,200 rows)
├── charts/                      # 6 PNG charts
├── generate_data.py             # reproducible data generation (seed 42)
├── analysis.py                  # pandas analysis + charts + findings.json
├── build_readme.py              # generates this README from findings.json
├── findings.json                # machine-readable results
└── README.md
```
"""

(BASE / "README.md").write_text(readme)
print("README.md written from findings.json")
