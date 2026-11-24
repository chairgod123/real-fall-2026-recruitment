import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so config imports
import config
import pandas as pd

# ── 1. Load combined scores file ─────────────────────────────────────
# All events (MTC, Game Night, and eventually Small Group Networking)
# live in ONE long-format file now, stacked and distinguished by the
# "Event" column.
#
# cp1252 (not latin1) so smart quotes/apostrophes in comments decode
# correctly instead of turning into stray \x92-style characters.
all_scores = pd.read_csv(config.SCORES_FILE, encoding="cp1252")

# ── 2. Standardize column names ──────────────────────────────────────
all_scores = all_scores.rename(columns={
    "PNM Name":  "Name",
    "PNM Email": "Email",
})

# Keep only the columns we care about
cols = ["Event", "Name", "Email", "Professional Score", "Social Score"]
all_scores = all_scores[cols]

print(all_scores.head(10))
print()
print("Total rows:", len(all_scores))
print("Events:", all_scores["Event"].value_counts().to_dict())

import re

def clean_name(name):
    if pd.isna(name):
        return None

    name = str(name).strip()           # remove leading/trailing spaces
    name = re.sub(r'\s+', ' ', name)   # collapse double spaces into one
    name = name.title()                # normalize capitalization: "john smith" → "John Smith"

    # Fix "Last, First" → "First Last"
    if ',' in name:
        parts = name.split(',', 1)  # the 1 means "split on the first comma only"
        name = parts[1].strip() + ' ' + parts[0].strip()

    return name

all_scores["Name"] = all_scores["Name"].apply(clean_name)

from thefuzz import fuzz

def find_likely_duplicates(names, threshold=85):
    names = list(names)
    flagged = []

    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            score = fuzz.ratio(name1, name2)
            if score >= threshold:
                flagged.append((name1, name2, score))

    return sorted(flagged, key=lambda x: x[2], reverse=True)

unique_names = all_scores["Name"].dropna().unique()
duplicates = find_likely_duplicates(unique_names)

print("Likely duplicates:")
for name1, name2, score in duplicates:
    print(f"  {score}%  '{name1}'  vs  '{name2}'")

def asymmetric_score(row):
    pro = row["Professional Score"]
    soc = row["Social Score"]

    pro_deficit = min(0, pro)  # negative if below 0, else 0
    soc_deficit = min(0, soc)  # same

    adjusted = (pro + soc
                + config.PRO_DEFICIT_WEIGHT * pro_deficit
                + config.SOCIAL_DEFICIT_WEIGHT * soc_deficit)
    return adjusted

all_scores["Adjusted Score"] = all_scores.apply(asymmetric_score, axis=1)

import numpy as np

# ── 3. Aggregate per PNM — EVERYONE who was ever scored, no roster to
# check against. Grouping by Email, not Name: names get typos/nicknames
# across separate score sheets, email doesn't. ─────────────────────────
all_scores["Email"] = all_scores["Email"].str.strip().str.lower()

grouped = all_scores.groupby("Email").agg(
    Name               = ("Name", lambda x: x.mode().iat[0]),  # most common spelling
    avg_score          = ("Adjusted Score", "mean"),
    interaction_count  = ("Adjusted Score", "count"),
).reset_index()

# ── BAYESIAN SHRINKAGE ─────────────────────────────────────────────────
global_mean = all_scores["Adjusted Score"].mean()
k = grouped["interaction_count"].median()  # semester median interaction count

def bayesian_shrink(row):
    n, avg = row["interaction_count"], row["avg_score"]
    if n == 0 or pd.isna(avg):
        # Every score this person got happened to be blank/NaN — treat
        # them as unscored rather than crashing on 0 * NaN.
        return global_mean
    return ((n * avg) + (k * global_mean)) / (n + k)

grouped["Shrunk Score"] = grouped.apply(bayesian_shrink, axis=1)

# ── SIGMOID MEMORABILITY BONUS ─────────────────────────────────────────
# Bonus is based on interaction count — rewards PNMs who were memorable
# enough to get scored by many brothers, with diminishing returns
midpoint = grouped["interaction_count"].median()

def sigmoid_bonus(count, scale=config.BONUS_SCALE):
    return scale / (1 + np.exp(-config.BONUS_STEEPNESS * (count - midpoint)))

grouped["Bonus"] = grouped["interaction_count"].apply(sigmoid_bonus)
grouped["Final Score"] = grouped["Shrunk Score"] + grouped["Bonus"]

# ── 4. Percentile + final ranking ───────────────────────────────────────
grouped["Percentile"] = (grouped["Final Score"].rank(pct=True) * 100).round(1)

final = grouped.sort_values("Final Score", ascending=False).reset_index(drop=True)
final.index += 1

final.to_excel(config.OPEN_RUSH_ALL_XLSX, index=True, sheet_name="Scores")
print(f"Saved to {config.OPEN_RUSH_ALL_XLSX}")
