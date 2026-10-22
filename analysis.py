"""
Indian Data Analyst Job Market Analytics — analysis script.

Loads data/job_postings.csv (synthetic data, see generate_data.py),
computes market insights, saves charts to charts/ and machine-readable
findings to findings.json (used to build README.md so quoted numbers
always match the data).

Run:  python analysis.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

BASE = Path(__file__).parent
DATA = BASE / "data" / "job_postings.csv"
CHART_DIR = BASE / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

# ------------------------------------------------------------------ load
df = pd.read_csv(DATA)
df["salary_avg"] = (df["salary_min_lpa"] + df["salary_max_lpa"]) / 2
df["exp_mid"] = (df["exp_min_yrs"] + df["exp_max_yrs"]) / 2
df["n_skills"] = df["skills"].str.split(";").str.len()


def exp_band(r):
    if r["exp_max_yrs"] <= 1:
        return "0–1 yrs (Fresher)"
    if r["exp_min_yrs"] >= 5:
        return "5+ yrs"
    if r["exp_min_yrs"] >= 3:
        return "3–5 yrs"
    return "1–3 yrs"


df["exp_band"] = df.apply(exp_band, axis=1)
BAND_ORDER = ["0–1 yrs (Fresher)", "1–3 yrs", "3–5 yrs", "5+ yrs"]

overall_median = round(float(df["salary_avg"].median()), 1)
n = len(df)

# ------------------------------------------------------- 1. skill demand
exploded = df.assign(skill=df["skills"].str.split(";")).explode("skill")
skill_counts = exploded["skill"].value_counts()
top15 = skill_counts.head(15)

# ------------------------------------------- 2. median salary by city
med_city = df.groupby("city")["salary_avg"].median().sort_values(ascending=False)

# ------------------------------------------- 3. median salary by exp band
med_band = df.groupby("exp_band")["salary_avg"].median().reindex(BAND_ORDER)

# ------------------------------------------- 4. salary premium per skill
prem = {}
for sk, grp in exploded.groupby("skill"):
    prem[sk] = round(float(grp["salary_avg"].median()) - overall_median, 2)
prem_s = pd.Series(prem).sort_values(ascending=False)

# ------------------------------------------- 5. counts: company type / mode
ctype_counts = df["company_type"].value_counts()
wmode_counts = df["work_mode"].value_counts()
title_counts = df["job_title"].value_counts()

# ------------------------------------------- 6. correlations & extras
corr_exp_sal = round(float(df["exp_mid"].corr(df["salary_avg"])), 2)
corr_nskills_sal = round(float(df["n_skills"].corr(df["salary_avg"])), 2)
remote_pct = round(float((df["work_mode"] == "Remote").mean() * 100), 1)
top_city = med_city.index[0]
top_skill = top15.index[0]

# Top 3 skills per experience band (demand shifts with seniority)
top3_by_band = {
    b: exploded[exploded["exp_band"] == b]["skill"].value_counts().head(3).index.tolist()
    for b in BAND_ORDER
}

# --------------------------------------------------------------- charts
def save(fig, name):
    fig.tight_layout()
    fig.savefig(CHART_DIR / name, bbox_inches="tight")
    plt.close(fig)
    print("chart:", name)

# 1. Top-15 demanded skills
fig, ax = plt.subplots(figsize=(9, 6))
sns.barplot(x=top15.values, y=top15.index, hue=top15.index, ax=ax,
            palette="Blues_r", legend=False)
ax.set_title("Top 15 Most Demanded Skills (n=1,200 postings)")
ax.set_xlabel("Number of postings")
for i, v in enumerate(top15.values):
    ax.text(v + 8, i, str(v), va="center", fontsize=9)
save(fig, "top_skills.png")

# 2. Median salary by city
fig, ax = plt.subplots(figsize=(9, 5.5))
sns.barplot(x=med_city.values, y=med_city.index, hue=med_city.index, ax=ax,
            palette="Greens_r", legend=False)
ax.set_title("Median Salary by City (LPA, avg of posted range)")
ax.set_xlabel("Median salary (₹ LPA)")
for i, v in enumerate(med_city.values):
    ax.text(v + 0.08, i, f"{v:.1f}", va="center", fontsize=9)
save(fig, "salary_by_city.png")

# 3. Median salary by experience band
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(x=med_band.index, y=med_band.values, hue=med_band.index, ax=ax,
            palette="Oranges_r", order=BAND_ORDER, legend=False)
ax.set_title("Median Salary by Experience Band (LPA)")
ax.set_ylabel("Median salary (₹ LPA)")
ax.set_xlabel("")
for i, v in enumerate(med_band.values):
    ax.text(i, v + 0.25, f"{v:.1f}", ha="center", fontsize=10, fontweight="bold")
save(fig, "salary_by_experience.png")

# 4. Salary premium per skill (top 10)
top_prem = prem_s.head(10)
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = ["#2ca02c" if v >= 0 else "#d62728" for v in top_prem.values]
sns.barplot(x=top_prem.values, y=top_prem.index, hue=top_prem.index, ax=ax,
            palette=colors, legend=False)
ax.set_title(f"Salary Premium per Skill (median vs overall {overall_median} LPA)")
ax.set_xlabel("Premium (₹ LPA)")
ax.axvline(0, color="black", linewidth=0.8)
save(fig, "skill_premium.png")

# 5. Postings by company type & work mode
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
sns.barplot(x=ctype_counts.index, y=ctype_counts.values, hue=ctype_counts.index,
            ax=axes[0], palette="Purples_r", legend=False)
axes[0].set_title("Postings by Company Type")
axes[0].set_ylabel("Postings")
for i, v in enumerate(ctype_counts.values):
    axes[0].text(i, v + 10, str(v), ha="center", fontsize=10)
sns.barplot(x=wmode_counts.index, y=wmode_counts.values, hue=wmode_counts.index,
            ax=axes[1], palette="Reds_r", legend=False)
axes[1].set_title("Postings by Work Mode")
axes[1].set_ylabel("Postings")
for i, v in enumerate(wmode_counts.values):
    axes[1].text(i, v + 10, str(v), ha="center", fontsize=10)
save(fig, "postings_company_workmode.png")

# 6. Experience vs salary scatter
fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=df, x="exp_mid", y="salary_avg", alpha=0.25, s=18, ax=ax)
sns.regplot(data=df, x="exp_mid", y="salary_avg", scatter=False,
            color="red", line_kws={"linewidth": 1.5}, ax=ax)
ax.set_title("Experience vs Salary (midpoint of posted range)")
ax.set_xlabel("Experience midpoint (years)")
ax.set_ylabel("Salary (₹ LPA)")
save(fig, "experience_vs_salary.png")

# --------------------------------------------------------------- findings
findings = {
    "n_postings": n,
    "overall_median_lpa": overall_median,
    "top_skill": {"name": top_skill, "count": int(top15.iloc[0]),
                  "pct": round(float(top15.iloc[0] / n * 100), 1)},
    "top15_skills": [{"skill": s, "count": int(c),
                      "pct": round(float(c / n * 100), 1)}
                     for s, c in top15.items()],
    "median_by_city": {c: round(float(v), 1) for c, v in med_city.items()},
    "top_city": {"name": top_city, "median_lpa": round(float(med_city.iloc[0]), 1)},
    "bottom_city": {"name": med_city.index[-1],
                    "median_lpa": round(float(med_city.iloc[-1]), 1)},
    "median_by_band": {b: round(float(med_band[b]), 1) for b in BAND_ORDER},
    "skill_premium_top5": [{"skill": s, "premium_lpa": float(v)}
                           for s, v in prem_s.head(5).items()],
    "company_type_counts": {k: int(v) for k, v in ctype_counts.items()},
    "work_mode_counts": {k: int(v) for k, v in wmode_counts.items()},
    "work_mode_pct": {k: round(float(v / n * 100), 1)
                      for k, v in wmode_counts.items()},
    "title_counts": {k: int(v) for k, v in title_counts.items()},
    "corr_exp_salary": corr_exp_sal,
    "corr_nskills_salary": corr_nskills_sal,
    "remote_pct": remote_pct,
    "top3_skills_by_band": top3_by_band,
}

with open(BASE / "findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print("\n================ KEY FINDINGS ================")
print(f"Postings analysed : {n}")
print(f"Overall median salary : {overall_median} LPA")
print(f"Top skill : {top_skill} ({top15.iloc[0]} postings, "
      f"{top15.iloc[0]/n*100:.1f}%)")
print("Median salary by city:")
for c, v in med_city.items():
    print(f"  {c:12s} {v:.1f} LPA")
print("Median salary by experience band:")
for b in BAND_ORDER:
    print(f"  {b:20s} {med_band[b]:.1f} LPA")
print("Top-5 salary premiums (skill median − overall median):")
for s, v in prem_s.head(5).items():
    print(f"  {s:22s} +{v:.2f} LPA")
print(f"Work modes : {dict(wmode_counts)} | Remote = {remote_pct}%")
print(f"Company types : {dict(ctype_counts)}")
print(f"Corr(experience, salary) = {corr_exp_sal} | "
      f"Corr(#skills, salary) = {corr_nskills_sal}")
print("findings.json written.")
