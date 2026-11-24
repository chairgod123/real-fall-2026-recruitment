"""
Run this before anything else, and any time something seems off:

    python3 check_setup.py        (Windows: python check_setup.py)

It checks that Python and the required packages are installed, that your
data folder is found, and that the files each script needs are present and
named so the scripts can find them. It changes nothing; it only reports.

  [ok]    fine
  [FIX]   something is wrong and a script will fail until you fix it
  [note]  not necessarily a problem (for example, a file not created yet)
"""

import importlib
import re
import sys
from pathlib import Path

problems = 0


def ok(msg):
    print(f"  [ok]   {msg}")


def fix(msg):
    global problems
    problems += 1
    print(f"  [FIX]  {msg}")


def note(msg):
    print(f"  [note] {msg}")


print("\n1. Python and packages")
if sys.version_info >= (3, 9):
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    fix(f"Python {sys.version_info.major}.{sys.version_info.minor} is too old. Install Python 3.10 or newer.")

for module, pip_name in [
    ("pandas", "pandas"), ("numpy", "numpy"), ("openpyxl", "openpyxl"),
    ("pptx", "python-pptx"), ("PIL", "Pillow"), ("thefuzz", "thefuzz"),
]:
    try:
        importlib.import_module(module)
        ok(pip_name)
    except ImportError:
        fix(f"{pip_name} is not installed. Run: pip install -r requirements.txt")
try:
    importlib.import_module("anthropic")
    ok("anthropic (only needed for comment summaries)")
except ImportError:
    note("anthropic is not installed (only needed for comment summaries)")

print("\n2. Data folder")
try:
    import config
except SystemExit as e:
    fix(str(e))
    print("\nStopped: fix the data folder first, then run this again.\n")
    sys.exit(1)

data_dir = Path(config.DATA_DIR)
ok(f"Using: {data_dir}")
if data_dir.name == "sample_data":
    note("This is the fake practice data. For real data, set DATA_DIR in your .env file (see docs/01_setup.md).")
csvs = sorted(data_dir.glob("*.csv"))
note(f"{len(csvs)} CSV file(s) in this folder")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


print("\n3. Open rush files")
for label, path in [("Open rush scores file", config.SCORES_FILE),
                    ("Applications file", config.APPLICANTS_FILE)]:
    if Path(path).exists():
        ok(f"{label}: {Path(path).name}")
    else:
        fix(f"{label} not found: {Path(path).name}. Save it in the data folder with exactly this name, "
            "or change its name in .env.")

print("\n4. Closed rush files (found by a word in the file name)")
for label, words, required in [
    ("Roster", ("closed", "bids"), True),
    ("DWA scores", ("dwa",), True),
    ("Case comp observer scores", ("observer",), True),
    ("Case comp judge, individual", ("individual",), True),
    ("Case comp judge, team", ("team",), True),
    ("Final interview scores", ("interview",), False),
]:
    hits = [p.name for p in csvs if all(norm(w) in norm(p.name) for w in words)]
    word_text = " + ".join(f'"{w}"' for w in words)
    if len(hits) == 1:
        ok(f"{label}: {hits[0]}")
    elif len(hits) > 1:
        fix(f"{label}: several files contain {word_text}: {', '.join(hits)}. Move or rename the old ones.")
    elif required:
        note(f"{label}: no file yet with {word_text} in its name (needed for closed rush)")
    else:
        note(f"{label}: none yet. Closed rush totals stay provisional until this exists.")

print("\n5. Slideshow")
if Path(config.SLIDES_TEMPLATE_PATH).exists():
    ok(f"Template: {Path(config.SLIDES_TEMPLATE_PATH).name}")
else:
    fix("Slide template not found. It belongs in slides/template/template.pptx.")
if Path(config.SLIDES_CSV).exists():
    ok(f"Slides input: {Path(config.SLIDES_CSV).name}")
else:
    note(f"Slides input file not found yet: {Path(config.SLIDES_CSV).name}")
hs = Path(config.HEADSHOTS_DIR)
if hs.exists():
    n = len([p for p in hs.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".heic", ".heif"}])
    ok(f"Headshots folder: {n} photo(s)")
else:
    note("No headshots folder yet")

print("\n6. Optional")
if (data_dir / "roster_overrides.json").exists():
    ok("roster_overrides.json found (withdrawn PNMs / nicknames)")
else:
    note("No roster_overrides.json. You only need it for withdrawn PNMs or nickname fixes.")
if config.ANTHROPIC_API_KEY:
    ok("API key is set (for comment summaries)")
else:
    note("No API key set. Only needed for comment summaries.")

print()
if problems:
    print(f"{problems} thing(s) to fix before running. See docs/04_troubleshooting.md.\n")
else:
    print("Everything needed looks fine.\n")
