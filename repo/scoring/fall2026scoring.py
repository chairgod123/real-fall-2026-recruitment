import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so config imports
import config
import pandas as pd

# ── 0. File locations ─────────────────────────────────────────────────
# Paths and file names are set in config.py / .env (DATA_DIR, SCORES_FILE,
# APPLICANTS_FILE). Update the names there each semester.
SCORES_FILE     = config.SCORES_FILE
APPLICANTS_FILE = config.APPLICANTS_FILE

# ── 1. Load combined scores file ─────────────────────────────────────
# All events (MTC, Game Night, and eventually Small Group Networking)
# live in ONE long-format file now, stacked and distinguished by the
# "Event" column. When Small Group Networking wraps, append its rows
# to this same file via Power Query using the same columns — no wide
# → long reshaping needed anymore.
#
# cp1252 (not latin1) so smart quotes/apostrophes in comments decode
# correctly instead of turning into stray \x92-style characters.
all_scores = pd.read_csv(SCORES_FILE, encoding="cp1252")

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

all_names = sorted(all_scores["Name"].dropna().str.strip().unique())

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

from thefuzz import fuzz, process

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

mean_pro = all_scores["Professional Score"].mean()
mean_social = all_scores["Social Score"].mean()
mean_combined = all_scores["Adjusted Score"].mean()

import numpy as np

# ── 3. Aggregate per PNM — using EVERYONE scored, not just applicants ──
# Grouping by Email, not Name: names get typos/nicknames across three
# separate score sheets, email doesn't. This keeps the population stats
# below (global_mean, k, sigmoid midpoint) statistically meaningful —
# they're the "fancy weighting" inputs and should reflect the full pool.
all_scores["Email"] = all_scores["Email"].str.strip().str.lower()

grouped = all_scores.groupby("Email").agg(
    avg_score          = ("Adjusted Score", "mean"),
    interaction_count  = ("Adjusted Score", "count"),
).reset_index()

# ── BAYESIAN SHRINKAGE ─────────────────────────────────────────────────
global_mean = all_scores["Adjusted Score"].mean()
k = grouped["interaction_count"].median()  # semester median interaction count

def bayesian_shrink(row):
    n, avg = row["interaction_count"], row["avg_score"]
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

# ── 4. Restrict to APPLICANTS ONLY ──────────────────────────────────────
# Build the applicant list straight from the raw Google Form export —
# no more manually creating an applicants_name_email.csv by hand each
# semester. The form export's IU Email column gets renamed to match
# the rest of the pipeline.
applicants_raw = pd.read_csv(APPLICANTS_FILE)
applicants_raw = applicants_raw.rename(columns={"IU Email:": "Email"})
applicants_raw["Email"] = applicants_raw["Email"].str.strip().str.lower()

# Drop rows with no real email (e.g. a stray "k" typed into both the
# Name and Email fields) — can't match these to scores or dedupe them
# meaningfully, so they're flagged for manual follow-up instead of
# silently entering the roster.
valid_email_mask = applicants_raw["Email"].str.contains("@", na=False)
invalid_rows = applicants_raw[~valid_email_mask]
if len(invalid_rows):
    print(f"\n⚠ Dropped {len(invalid_rows)} application row(s) with no valid email — review manually:")
    print(invalid_rows[["Timestamp", "Name", "Email"]].to_string(index=False))
applicants_raw = applicants_raw[valid_email_mask]

# Some PNMs submit the form more than once (edits, accidental double
# submit). Keep only their most recent submission per email so they
# don't get double-counted in the final roster.
applicants_raw["Timestamp"] = pd.to_datetime(applicants_raw["Timestamp"])
dupe_count = applicants_raw.duplicated(subset="Email", keep=False).sum()
if dupe_count:
    print(f"\n⚠ {dupe_count} application row(s) are repeat submissions (same email) — keeping most recent only:")
    print(applicants_raw.loc[applicants_raw.duplicated(subset="Email", keep=False), ["Timestamp", "Name", "Email"]]
          .sort_values(["Email", "Timestamp"]).to_string(index=False))
applicants_raw = applicants_raw.sort_values("Timestamp").drop_duplicates(subset="Email", keep="last")

applicants = applicants_raw[["Name", "Email"]].reset_index(drop=True)
print(f"\nFinal applicant count after cleanup: {len(applicants)}")

# Left-join on email so nobody errors out. Applicants who never got
# scored (didn't attend, or just weren't memorable) will have no match
# in `grouped` — that's expected, not a bug — and get explicit defaults
# below instead of a silent NaN.

final = applicants.merge(
    grouped, on="Email", how="left"
)

final["interaction_count"] = final["interaction_count"].fillna(0)
zero_score_bonus = sigmoid_bonus(0)
final["Shrunk Score"] = final["Shrunk Score"].fillna(global_mean)
final["Bonus"] = final["Bonus"].fillna(zero_score_bonus)
final["Final Score"] = final["Final Score"].fillna(final["Shrunk Score"] + final["Bonus"])
# avg_score intentionally stays NaN when there's nothing to average —
# that's honest, not an error.

no_score_count = (final["interaction_count"] == 0).sum()
print(f"\nApplicants with zero interactions (no scores at all): {no_score_count}")

# ── 5. Percentile ─────────────────────────────────────────────────────
# Only meaningful for applicants who actually have scores — an unscored
# PNM's "Final Score" is just the population mean, not a real measurement,
# so they get no percentile rather than a misleading one.
scored_mask = final["interaction_count"] > 0
final["Percentile"] = np.nan
final.loc[scored_mask, "Percentile"] = (
    final.loc[scored_mask, "Final Score"].rank(pct=True) * 100
).round(1)

# ── 6. Sort — scored PNMs ranked by Final Score, unscored pushed to the
# bottom (mixing them into the middle of the ranked list next to real
# scores would be misleading) ────────────────────────────────────────
scored = final[scored_mask].sort_values("Final Score", ascending=False)
unscored = final[~scored_mask].sort_values("Name")
final = pd.concat([scored, unscored], ignore_index=True)
final.index += 1

final.to_excel(config.OPEN_RUSH_XLSX, index=True, sheet_name="Scores")

# ── 7. Highlight unscored rows soft red ─────────────────────────────────
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

wb = load_workbook(config.OPEN_RUSH_XLSX)
ws = wb["Scores"]
soft_red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

interaction_col = final.columns.get_loc("interaction_count") + 2  # +1 for 1-index, +1 for the index column
for row_num in range(2, ws.max_row + 1):  # row 1 is the header
    if ws.cell(row=row_num, column=interaction_col).value == 0:
        for col_num in range(1, ws.max_column + 1):
            ws.cell(row=row_num, column=col_num).fill = soft_red

wb.save(config.OPEN_RUSH_XLSX)
print(f"Saved to {config.OPEN_RUSH_XLSX} (unscored PNMs sorted to bottom + highlighted)")