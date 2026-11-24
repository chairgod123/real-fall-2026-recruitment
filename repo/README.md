# PSE Recruitment Pipeline

This folder holds the tools Atulya used in Fall 2026 to score PNMs, build the deliberation slideshow, and summarize actives' comments. It is a **reference and a starting point**. You have the final say on how recruitment is scored and run, and you are free to change, simplify, or replace any of it.

## Start here

You do not need to read this whole folder, and you do not need to understand how the code works. Almost everything in it is for later, when you need it.

**Right now: nothing.** Atulya will walk you through all of it in person. This folder is here so you have something to look back at afterward.

**When you are ready to try it yourself (about 15 minutes):**
1. Follow [`docs/01_setup.md`](docs/01_setup.md) once.
2. Run the practice data (it contains only made-up people, so you cannot break anything).

**After that, use this folder like a recipe book. Find the moment you are in:**

| Where you are in recruitment | Open this |
|---|---|
| Getting set up for the first time | [`docs/01_setup.md`](docs/01_setup.md) |
| Running scores after an event, or getting ready for deliberation | [`docs/02_semester_runbook.md`](docs/02_semester_runbook.md) |
| Deciding how scoring should work, or someone asks "why is this person ranked there?" | [`docs/03_scoring_in_plain_english.md`](docs/03_scoring_in_plain_english.md) |
| Check-in form, application headshots, or the roster slideshow in Google | [`docs/06_google_check_in_tools.md`](docs/06_google_check_in_tools.md) |
| Something broke or looks wrong | [`docs/04_troubleshooting.md`](docs/04_troubleshooting.md) |
| Looking up exact column names, weights, or settings | [`docs/05_technical_reference.md`](docs/05_technical_reference.md) (you can ignore this unless you are looking something up) |

## The three commands you will use most

Run these in the Terminal, from inside this folder. On Windows, type `python` instead of `python3`.

| I want to... | Type this |
|---|---|
| Check that everything is in place | `python3 check_setup.py` |
| Rank PNMs after open rush | `python3 scoring/fall2026scoring.py` |
| Rank PNMs for closed rush | `python3 scoring/closed_rush_scoring.py` |

The other scripts (`fall2026scoring_allpnms.py` and `slides/build_slides.py`) are covered in the runbook.

## Three rules that prevent most problems

1. **PNM data never goes in this folder or in git.** It lives in the shared Drive folder. This folder holds tools only.
2. **Everything is matched by IU email.** Names get misspelled and nicknamed. Emails do not. If a PNM is missing from the results, the cause is almost always a typo in an email or name in a score sheet.
3. **Read the messages the script prints.** They tell you about missing data, duplicates, and typos. You do not have to understand all of the numbers, but do read the warnings.

## What is in this folder

| Name | What it is |
|---|---|
| `docs/` | The instructions above |
| `scoring/` | The scoring tools |
| `slides/` | The deliberation slideshow tool and its template |
| `apps_script/` | Backup copies of the four Google tools (check-in cleanup and roster slideshow; application headshot conversion and renaming). They live inside Google Sheets, not on your computer. See `docs/06_google_check_in_tools.md` |
| `sample_data/` | Made-up people for practice. Safe to experiment with |
| `config.py` | The settings, including how much each closed rush event counts. Open it in any text editor |
| `check_setup.py` | A checker that tells you in plain language what is missing |
| `.env.example` | A template for your personal settings |

## If you get stuck

Text Atulya. Include the last line the Terminal printed. That line is usually all he needs.

Atulya Prasad, atprasad@iu.edu
