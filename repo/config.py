"""
Central configuration for the PSE recruitment pipeline.

Everything a new VPR is likely to change lives here: where the data is,
what the input files are called, and the closed rush weights. The scoring
scripts import from this file, so you should rarely need to edit them.

Real PNM data is NOT in this repository. Point DATA_DIR at the local, synced
copy of the semester's shared Drive folder (see README.md, "Data").

Set values in a `.env` file (copy `.env.example`) or as environment variables.
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def _load_env_file(path):
    """Tiny .env reader so no extra package is required. Existing
    environment variables win over the file."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(REPO_ROOT / ".env")

# ── Where the data lives ─────────────────────────────────────────────────────
# Local folder holding this semester's input CSVs and where outputs are
# written. Defaults to ./sample_data so the pipeline runs out of the box on
# the fake data.
DATA_DIR = Path(os.environ.get("DATA_DIR", REPO_ROOT / "sample_data")).expanduser()

if not DATA_DIR.exists():
    sys.exit(
        f"DATA_DIR does not exist: {DATA_DIR}\n"
        "Set DATA_DIR in .env to your local copy of the semester's Drive folder."
    )

# ── Open rush scoring (scoring/fall2026scoring*.py) ──────────────────────────
# Update these each semester to match the exported file names exactly.
SCORES_FILE = DATA_DIR / os.environ.get(
    "SCORES_FILE", "open_rush_scores.csv"
)  # long-format combined scores (Power Query output)
APPLICANTS_FILE = DATA_DIR / os.environ.get(
    "APPLICANTS_FILE", "applications_form_responses.csv"
)  # raw Google Form export of applications

OPEN_RUSH_XLSX = DATA_DIR / "recruitment_scores.xlsx"
OPEN_RUSH_ALL_XLSX = DATA_DIR / "recruitment_scores_all.xlsx"

# Open rush model parameters. See docs/scoring_concepts.md for what each does.
PRO_DEFICIT_WEIGHT = 0.5   # extra penalty applied to negative professional scores
SOCIAL_DEFICIT_WEIGHT = 1.0  # extra penalty applied to negative social scores
BONUS_SCALE = 0.5          # maximum size of the memorability bonus
BONUS_STEEPNESS = 0.3      # how quickly the bonus rises around the median

# ── Closed rush scoring (scoring/closed_rush_scoring.py) ─────────────────────
# Weights must sum to 1.0 once the Final Interview file is present.
W_DWA = 0.25
W_OBS = 0.15          # Case Comp observer
W_JUDGE_IND = 0.10    # Case Comp judge, individual
W_JUDGE_TM = 0.05     # Case Comp judge, team
W_OPEN_RUSH = 0.10
W_INTERVIEW = 0.35    # only applied if an interview file is present

# Max possible raw value for each component (used to scale to weighted points).
MAX_DWA = 10          # (pro + 3) + (social + 3), scores run -2..+2
MAX_OBS = 30          # 6 criteria x 5
MAX_JUDGE_IND = 15    # 3 criteria x 5
MAX_JUDGE_TM = 15     # 3 criteria x 5
MAX_OPEN_RUSH = 10    # same shifted pro + social scale as DWA
MAX_INTERVIEW = 30    # TMAY, Why PSE, S&W, Teamwork (1-5 each) + Resume Deep Dive (1-10)

_total_weight = W_DWA + W_OBS + W_JUDGE_IND + W_JUDGE_TM + W_OPEN_RUSH + W_INTERVIEW
if abs(_total_weight - 1.0) > 1e-9:
    print(
        f"WARNING: closed rush weights add up to {_total_weight:.2f}, not 1.00. "
        "Totals will not be out of 100 until they do. Check config.py."
    )

FUZZY_THRESHOLD = 90  # minimum fuzzy-match score to accept a name match to the roster

CLOSED_RUSH_OUTPUT = DATA_DIR / "closed_rush_scores.csv"

# ── Per-semester roster overrides (kept OUT of git) ──────────────────────────
# Names of withdrawn PNMs and nickname -> roster-name aliases are PNM data, so
# they are read from a JSON file in DATA_DIR instead of being hardcoded here.
# Create DATA_DIR/roster_overrides.json like:
#   {"withdrawn": ["First Last"], "aliases": {"nickname": "Roster Name"}}
# The file is optional.
def load_roster_overrides():
    path = DATA_DIR / "roster_overrides.json"
    if not path.exists():
        return set(), {}
    data = json.loads(path.read_text())
    return set(data.get("withdrawn", [])), dict(data.get("aliases", {}))


# ── Slideshow (slides/build_slides.py) ───────────────────────────────────────
SLIDES_TEMPLATE_PATH = Path(
    os.environ.get("SLIDES_TEMPLATE", REPO_ROOT / "slides" / "template" / "template.pptx")
)
SLIDES_CSV = DATA_DIR / os.environ.get("SLIDES_CSV", "slides_input.csv")
HEADSHOTS_DIR = DATA_DIR / os.environ.get("HEADSHOTS_DIR", "headshots")
SLIDES_OUTPUT = DATA_DIR / "recruitment_slides.pptx"

# ── Comment summaries (scoring/summarize_comments.py) ────────────────────────
# Your own key goes in .env as ANTHROPIC_API_KEY. Never commit it.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUMMARY_MODEL = os.environ.get("SUMMARY_MODEL", "claude-sonnet-4-6")
