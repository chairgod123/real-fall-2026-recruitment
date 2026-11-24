import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so config imports
import config
"""
PSE Closed Rush Scoring Pipeline — v3 (Fall 2026)
===================================================
Weights (set in config.py; Fall 2026 values shown):
  DWA:              25%
  CC Observer:      15%
  CC Judge Indiv:   10%
  CC Judge Team:     5%
  Open Rush:        10%
  Final Interview:  35%   ← included automatically once INTERVIEW_FILE exists
"""

import os
import re
import glob
import pandas as pd
from thefuzz import process

BASE = str(config.DATA_DIR) + "/"   # set DATA_DIR in .env

def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def find_file(base_dir, *keywords, required=True):
    matches = []
    for path in glob.glob(os.path.join(base_dir, "*.csv")):
        name_norm = _norm(os.path.basename(path))
        if all(_norm(k) in name_norm for k in keywords):
            matches.append(path)
    if len(matches) == 1:
        return matches[0]
    available = "\n    ".join(os.path.basename(p) for p in glob.glob(os.path.join(base_dir, "*.csv"))) or "(no CSVs found)"
    if len(matches) > 1:
        raise FileNotFoundError(
            f"Multiple files match keywords {keywords} in {base_dir}:\n    "
            + "\n    ".join(matches) + "\n  Rename one so only one matches."
        )
    if required:
        raise FileNotFoundError(
            f"No file matching keywords {keywords} found in {base_dir}.\n  Files present:\n    {available}"
        )
    return None

def find_open_rush_file(base_dir, exclude):
    """The open rush export has no distinctive keyword in its filename (it's
    just the base report name with no suffix), so identify it by its columns
    instead: it's the only file with both PNM Email and Event columns."""
    for path in glob.glob(os.path.join(base_dir, "*.csv")):
        if path in exclude:
            continue
        try:
            cols = set(pd.read_csv(path, encoding="latin1", nrows=0).columns)
        except Exception:
            continue
        if {"PNM Email", "Event"} <= cols:
            return path
    raise FileNotFoundError(
        f"Couldn't find the open rush file in {base_dir} "
        "(looking for a CSV with both 'PNM Email' and 'Event' columns)."
    )

CLOSED_BIDS_FILE = find_file(BASE, "closed", "bids")          # roster: Name, Email
DWA_FILE         = find_file(BASE, "dwa")
OBSERVER_FILE    = find_file(BASE, "observer")
INDIVIDUAL_FILE  = find_file(BASE, "individual")
TEAM_FILE        = find_file(BASE, "team")
INTERVIEW_FILE   = find_file(BASE, "interview", required=False)  # None if not conducted yet — that's fine
OPEN_RUSH_FILE   = find_open_rush_file(
    BASE, exclude={CLOSED_BIDS_FILE, DWA_FILE, OBSERVER_FILE, INDIVIDUAL_FILE, TEAM_FILE, INTERVIEW_FILE}
)

# ── Weights ───────────────────────────────────────────────────────────────────
# Defined in config.py so you can change them without touching this script.
W_DWA       = config.W_DWA
W_OBS       = config.W_OBS
W_JUDGE_IND = config.W_JUDGE_IND
W_JUDGE_TM  = config.W_JUDGE_TM
W_OPEN_RUSH = config.W_OPEN_RUSH
W_INTERVIEW = config.W_INTERVIEW   # only applied if INTERVIEW_FILE is present

FUZZY_THRESHOLD = config.FUZZY_THRESHOLD   # min score to accept a fuzzy match to the roster

# Withdrawn PNMs and nickname aliases are PNM data, so they are read from
# DATA_DIR/roster_overrides.json (optional, never committed). See config.py.
WITHDRAWN_PNMS, NAME_ALIASES = config.load_roster_overrides()

# ── Helpers ───────────────────────────────────────────────────────────────────
def normalize_fixed(series, raw_max, weight):
    """Scale a raw score (0-raw_max) to weighted points (0-weight*100)."""
    return (series / raw_max) * (weight * 100)

def clean_name(s):
    return str(s).strip().lower()

def clean_email(s):
    return str(s).strip().lower()

# ── 0. Closed-rush roster — this defines who we're scoring, full stop ─────────
print("── Roster ──")
roster = pd.read_csv(CLOSED_BIDS_FILE, encoding="latin1")

if WITHDRAWN_PNMS:
    before = len(roster)
    roster = roster[~roster["Name"].isin(WITHDRAWN_PNMS)].copy()
    print(f"  excluding {before - len(roster)} withdrawn PNM(s): {', '.join(sorted(WITHDRAWN_PNMS))}")

roster["name_clean"]  = roster["Name"].apply(clean_name)
roster["email_clean"] = roster["Email"].apply(clean_email)

if roster["name_clean"].duplicated().any() or roster["email_clean"].duplicated().any():
    print("  ⚠ roster itself has duplicate names or emails — fix this file first")

name_to_canon  = dict(zip(roster["name_clean"], roster["Name"]))   # clean -> display name
email_to_canon = dict(zip(roster["email_clean"], roster["Name"]))  # clean email -> display name
roster_clean_names = list(name_to_canon.keys())
print(f"  {len(roster)} PNMs on the closed-rush roster")

def match_name_to_roster(raw_name):
    """Match a raw name to the roster: check known aliases first, then an
    exact clean match, then fuzzy match. Returns the roster's canonical
    display name, or None if nothing scores above FUZZY_THRESHOLD."""
    clean = clean_name(raw_name)
    if clean in NAME_ALIASES:
        return NAME_ALIASES[clean]
    clean_words = set(clean.split())
    for alias, canon in NAME_ALIASES.items():
        if set(alias.split()) <= clean_words:   # e.g. alias "sam" also matches "Sam Lee"
            return canon
    if clean in name_to_canon:
        return name_to_canon[clean]
    match, score = process.extractOne(clean, roster_clean_names)
    return name_to_canon[match] if score >= FUZZY_THRESHOLD else None

def canonicalize_by_name(df, name_col):
    """Add pnm_canon by matching name_col against the roster; drop non-matches
    (they're not in closed rush) and report how many were dropped."""
    df = df.copy()
    df["pnm_canon"] = df[name_col].apply(match_name_to_roster)
    dropped = df["pnm_canon"].isna().sum()
    if dropped:
        print(f"    {dropped} rows didn't match anyone on the roster — excluded")
    return df[df["pnm_canon"].notna()]

# ── 1. DWA ────────────────────────────────────────────────────────────────────
print("── DWA ──")
dwa = pd.read_csv(DWA_FILE, encoding="latin1")
dwa = canonicalize_by_name(dwa, "PNM Name")

dwa["dwa_raw"] = (dwa["Professional Score"] + 3) + (dwa["Social Score"] + 3)  # 2..10

dwa_scores = dwa.groupby("pnm_canon")["dwa_raw"].mean().rename("dwa_avg")
dwa_comments = (
    dwa.groupby("pnm_canon")["Comments:"]
    .apply(lambda x: " | ".join(x.dropna().astype(str)))
    .rename("dwa_comments")
)
dwa_out = pd.concat([dwa_scores, dwa_comments], axis=1).reset_index()
print(f"  {len(dwa_out)} roster PNMs scored")

# ── 2. CC Observer (Power Query already averaged this — just read it) ─────────
print("── CC Observer ──")
obs = pd.read_csv(OBSERVER_FILE, encoding="latin1")
obs = canonicalize_by_name(obs, "Name")
obs_out = (
    obs.groupby("pnm_canon")["Final Score"].mean().rename("obs_raw").reset_index()
)
print(f"  {len(obs_out)} roster PNMs scored")

# ── 3. CC Judge Individual (use the precomputed avg column) ───────────────────
print("── CC Judge Individual ──")
ind = pd.read_csv(INDIVIDUAL_FILE, encoding="latin1")
ind = canonicalize_by_name(ind, "Name")
judge_ind_out = (
    ind.groupby("pnm_canon")["Individual Score (avg, out of 15)"]
    .mean()
    .rename("judge_ind_avg")
    .reset_index()
)
team_map = ind[["pnm_canon", "Team"]].drop_duplicates("pnm_canon")
print(f"  {len(judge_ind_out)} roster PNMs scored")

# ── 4. CC Judge Team ────────────────────────────────────────────────────────
print("── CC Judge Team ──")
team = pd.read_csv(TEAM_FILE, encoding="latin1")
team_scores = team[["Team", "Team Score (avg, out of 15)"]].rename(
    columns={"Team Score (avg, out of 15)": "team_raw"}
)
team_out = team_map.merge(team_scores, on="Team", how="left")[["pnm_canon", "team_raw"]]
print(f"  {len(team_out)} roster PNMs assigned team scores")

# ── 5. Open Rush — match by email first, fall back to name ────────────────────
print("── Open Rush ──")
orush = pd.read_csv(OPEN_RUSH_FILE, encoding="latin1")

missing = orush["Professional Score"].isna() | orush["Social Score"].isna()
if missing.any():
    print(f"  dropping {missing.sum()} rows with no score recorded")
orush = orush[~missing].copy()

orush["email_clean"] = orush["PNM Email"].apply(clean_email)
orush["pnm_canon"] = orush["email_clean"].map(email_to_canon)

unmatched = orush["pnm_canon"].isna()
if unmatched.any():
    orush.loc[unmatched, "pnm_canon"] = orush.loc[unmatched, "PNM Name"].apply(match_name_to_roster)

matched_by_email = (~unmatched).sum()
still_unmatched = orush["pnm_canon"].isna().sum()
matched_rows = (~orush["pnm_canon"].isna()).sum()
recovered_by_name = matched_rows - matched_by_email
print(f"  {matched_by_email} rows matched by email, {recovered_by_name} more recovered via name fallback, "
      f"{still_unmatched} rows excluded (not on the closed-rush roster)")
orush = orush[orush["pnm_canon"].notna()].copy()

orush["or_raw"] = (orush["Professional Score"] + 3) + (orush["Social Score"] + 3)  # 2..10
or_out = (
    orush.groupby("pnm_canon")["or_raw"].mean().rename("open_rush_avg").reset_index()
)
print(f"  {len(or_out)} roster PNMs scored across {orush['Event'].nunique()} open rush events")

# ── 6. Final Interview (optional — not conducted yet) ─────────────────────────
have_interview = INTERVIEW_FILE is not None
if have_interview:
    print("── Interview ──")
    iview = pd.read_csv(INTERVIEW_FILE, encoding="latin1")
    score_cols = [c for c in iview.columns if c.startswith("Score")]
    iview["interview_raw"] = iview[score_cols].sum(axis=1)
    iview = canonicalize_by_name(iview, "PNM Name")

    interview_scores = iview.groupby("pnm_canon")["interview_raw"].mean().rename("interview_avg")
    comment_cols = [c for c in iview.columns if "comment" in c.lower()]
    iview["interview_comments"] = iview[comment_cols].apply(
        lambda row: " | ".join(row.dropna().astype(str)), axis=1
    )
    interview_comments = (
        iview.groupby("pnm_canon")["interview_comments"]
        .apply(lambda x: " || ".join(x.dropna().astype(str)))
        .rename("interview_comments")
    )
    interview_out = pd.concat([interview_scores, interview_comments], axis=1).reset_index()
    print(f"  {len(interview_out)} roster PNMs scored")
else:
    print("── Interview ── not conducted yet, skipping (scores below are provisional)")

# ── 7. Merge — base list is the roster itself, not whoever shows up in a file ─
print("── Merging ──")
master = roster[["Name"]].rename(columns={"Name": "pnm_canon"})
master = master.merge(dwa_out,       on="pnm_canon", how="left")
master = master.merge(obs_out,       on="pnm_canon", how="left")
master = master.merge(judge_ind_out, on="pnm_canon", how="left")
master = master.merge(team_out,      on="pnm_canon", how="left")
master = master.merge(or_out,        on="pnm_canon", how="left")
if have_interview:
    master = master.merge(interview_out, on="pnm_canon", how="left")

# ── 8. Flag gaps ────────────────────────────────────────────────────────────
# Case comp: legitimately optional (not every closed-rush PNM does Case Comp
# scoring the same way) — impute with cohort average, same as before.
cc_cols = ["obs_raw", "judge_ind_avg", "team_raw"]
master["cc_missing"] = master[cc_cols].isna().any(axis=1)
master["obs_raw"]       = master["obs_raw"].fillna(master["obs_raw"].mean())
master["judge_ind_avg"] = master["judge_ind_avg"].fillna(master["judge_ind_avg"].mean())
master["team_raw"]      = master["team_raw"].fillna(master["team_raw"].mean())

# DWA / Open Rush: everyone on the roster should have these. A gap here is
# almost always a name/email typo, not a legitimate absence — flag, don't
# silently impute, so it gets checked by hand.
master["dwa_missing"]       = master["dwa_avg"].isna()
master["open_rush_missing"] = master["open_rush_avg"].isna()
for col, label in [("dwa_missing", "DWA"), ("open_rush_missing", "Open Rush")]:
    n = master[col].sum()
    if n:
        print(f"  ⚠ {n} roster PNM(s) missing {label} data — check spelling/email in the raw export:")
        print("    " + ", ".join(master.loc[master[col], "pnm_canon"].tolist()))

# ── 9. Scale to weighted points ────────────────────────────────────────────────
master["pts_dwa"]       = normalize_fixed(master["dwa_avg"],       config.MAX_DWA, W_DWA)
master["pts_obs"]       = normalize_fixed(master["obs_raw"],       config.MAX_OBS, W_OBS)
master["pts_judge_ind"] = normalize_fixed(master["judge_ind_avg"], config.MAX_JUDGE_IND, W_JUDGE_IND)
master["pts_judge_tm"]  = normalize_fixed(master["team_raw"],      config.MAX_JUDGE_TM, W_JUDGE_TM)
master["pts_open_rush"] = normalize_fixed(master["open_rush_avg"], config.MAX_OPEN_RUSH, W_OPEN_RUSH)

pt_cols = ["pts_dwa", "pts_obs", "pts_judge_ind", "pts_judge_tm", "pts_open_rush"]
weight_captured = W_DWA + W_OBS + W_JUDGE_IND + W_JUDGE_TM + W_OPEN_RUSH  # 0.65

if have_interview:
    master["pts_interview"] = normalize_fixed(master["interview_avg"], config.MAX_INTERVIEW, W_INTERVIEW)
    pt_cols.append("pts_interview")
    weight_captured += W_INTERVIEW  # 1.00

# ── 10. Total + rank ────────────────────────────────────────────────────────
master["total_score"] = master[pt_cols].sum(axis=1, min_count=1)
master["pct_of_captured_weight"] = (master["total_score"] / (weight_captured * 100) * 100).round(1)
master["percentile"] = master["total_score"].rank(pct=True).mul(100).round(1)
master["rank"]        = master["total_score"].rank(ascending=False, method="min").astype(int)

# ── 11. Output ────────────────────────────────────────────────────────────────
output_cols = [
    "pnm_canon", "rank", "percentile", "total_score", "pct_of_captured_weight",
    "pts_dwa", "pts_obs", "pts_judge_ind", "pts_judge_tm", "pts_open_rush",
]
if have_interview:
    output_cols.append("pts_interview")
output_cols += [
    "dwa_avg", "obs_raw", "judge_ind_avg", "team_raw", "open_rush_avg",
]
if have_interview:
    output_cols += ["interview_avg", "interview_comments"]
output_cols += ["cc_missing", "dwa_missing", "open_rush_missing", "dwa_comments"]
output_cols = [c for c in output_cols if c in master.columns]

out = master[output_cols].sort_values("rank")
out.to_csv(config.CLOSED_RUSH_OUTPUT, index=False)

print()
print("── Summary ──")
print(f"  Total PNMs (roster):     {len(out)}")
print(f"  CC missing (flagged):    {master['cc_missing'].sum()}")
print(f"  Weight captured so far:  {weight_captured*100:.0f}% of full model"
      + ("" if have_interview else " (Final Interview not yet run)"))
print(f"  Score range:             {out['total_score'].min():.1f} – {out['total_score'].max():.1f}")
print(f"  Mean score:              {out['total_score'].mean():.1f}")
print()
print(out[["pnm_canon", "rank", "total_score", "pct_of_captured_weight", "cc_missing"]]
      .head(20).to_string(index=False))
print()
print(f"✓ Output saved to {config.CLOSED_RUSH_OUTPUT}")
if not have_interview:
    print("  NOTE: this is provisional — rerun after adding the Final Interview file")
    print(f'        (drop a CSV with "interview" in the filename into {BASE} and rerun)')
