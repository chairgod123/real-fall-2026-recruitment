# 5. Technical Reference

**You can ignore this file until you are looking something up.** It holds the exact details that the other pages leave out: column names, settings, formulas, and how the pieces connect. Everything here is for lookup, not for reading through.

---

## Map of the tools

| File | What it does | Writes |
|---|---|---|
| `check_setup.py` | Checks Python, packages, the data folder, and file names | nothing |
| `scoring/fall2026scoring.py` | Ranks **applicants** after open rush | `recruitment_scores.xlsx` |
| `scoring/fall2026scoring_allpnms.py` | Ranks **everyone who was scored**, with or without an application | `recruitment_scores_all.xlsx` |
| `scoring/closed_rush_scoring.py` | Ranks the closed rush roster | `closed_rush_scores.csv` |
| `scoring/summarize_comments.py` | AI comment summaries *(to be added to the folder)* | `closed_rush_scores_with_summaries.csv` |
| `slides/build_slides.py` | One slide per PNM | `recruitment_slides.pptx` |
| `apps_script/data_cleansing.gs` | Backup of the check-in cleanup and check-in photo-conversion code (runs inside a Google Sheet) | Columns E and F of the Sheet |
| `apps_script/slideshow_generator.gs` | Backup of the roster slideshow builder (runs inside the same Sheet) | A Google Slides deck in Drive |
| `apps_script/application_headshots.gs` | Backup of the application-photo converter (runs inside the application Sheet) | `<iu-email>.jpg` files in one Drive folder, plus a link column |
| `apps_script/rename_headshots.gs` | Backup of the rename fix-up (same project as the file above) | Renames existing Drive files |
| `config.py` | Every setting in one place | |

All inputs come from, and all outputs go to, the **data folder** (`DATA_DIR` in `.env`).

---

## Settings in `config.py`

Change a number, save, and re-run.

| Setting | Fall 2026 value | Meaning |
|---|---|---|
| `W_INTERVIEW` | 0.35 | Share of the closed rush total from the final interview |
| `W_DWA` | 0.25 | Dinner with Actives |
| `W_OBS` | 0.15 | Case Comp observer |
| `W_JUDGE_IND` | 0.10 | Case Comp judge, individual |
| `W_OPEN_RUSH` | 0.10 | Open rush |
| `W_JUDGE_TM` | 0.05 | Case Comp judge, team |
| `PRO_DEFICIT_WEIGHT` | 0.5 | Extra penalty on negative professional scores (0 = off) |
| `SOCIAL_DEFICIT_WEIGHT` | 1.0 | Extra penalty on negative social scores (0 = off) |
| `BONUS_SCALE` | 0.5 | Largest possible memorability bonus (0 = off) |
| `BONUS_STEEPNESS` | 0.3 | How sharply the bonus rises around the typical score count |
| `FUZZY_THRESHOLD` | 90 | How close two names must be (out of 100) to count as the same person |
| `MAX_*` | | The highest possible raw score for each component. Change only if a rubric changes |

The six `W_` shares must total 1.00.

---

## Input files and exact column names

Column names must match exactly, including punctuation and capitalization. Examples are in `sample_data/`.

| File | Columns needed |
|---|---|
| **Open rush scores** (combined, one row per score) | `Event`, `PNM Name`, `PNM Email`, `Professional Score`, `Social Score` |
| **Applications** (Google Form export) | `Timestamp`, `Name`, `IU Email:` (the colon is part of the name) |
| **Closed rush roster** (`closed` + `bids`) | `Name`, `Email` |
| **DWA** (`dwa`) | `PNM Name`, `Professional Score`, `Social Score`, `Comments:` |
| **Case Comp observer** (`observer`) | `Name`, `Final Score` |
| **Case Comp judge, individual** (`individual`) | `Name`, `Team`, `Individual Score (avg, out of 15)` |
| **Case Comp judge, team** (`team`) | `Team`, `Team Score (avg, out of 15)` |
| **Final interview** (`interview`) | `PNM Name`, any columns whose names start with `Score`, any columns with `comment` in the name |
| **Slides input** | `Rank`, `Name`, `Email`, `Final Score`, `Shrunk Score`, `Bonus`, `Interaction Count`, `Percentile`, `Application Number` (capitalization and spacing are matched loosely) |

**Other rules:**
- Open rush scores are read as `cp1252` text, which is what Excel's **"CSV (Comma delimited)"** produces. The closed rush files are read as `latin1`. If a file looks garbled, re-save it in that format.
- Open rush scores run from -2 to +2. The tool treats scores as numbers, so blanks are skipped.
- Duplicate application submissions: the most recent one per email is kept.
- Rows without an `@` in the email are dropped from the applicant list.
- **Match order:** open rush is matched by email. Closed rush matches the open rush file by email first and by name second, and every other file by name (using a close-enough "fuzzy" match).

---

## The math, for reference

You do not need this to run anything.

**Open rush, per score:**

```
adjusted = professional + social
           + PRO_DEFICIT_WEIGHT    * min(0, professional)
           + SOCIAL_DEFICIT_WEIGHT * min(0, social)
```

**Per PNM:**

```
avg    = mean of adjusted scores
n      = number of scores
k      = median n across all PNMs
shrunk = (n * avg + k * class_mean) / (n + k)
bonus  = BONUS_SCALE / (1 + exp(-BONUS_STEEPNESS * (n - k)))
final  = shrunk + bonus
percentile = rank of final, as a percent
```

PNMs with no scores get `final = class_mean + bonus at n = 0`, no percentile, and are sorted last.

**Closed rush, per component:**

```
points = (raw / max_raw) * weight * 100
total  = sum of points
```

| Component | Raw score | Max |
|---|---|---|
| DWA | (professional + 3) + (social + 3), averaged over actives | 10 |
| Open rush | Same formula, averaged over all open rush events | 10 |
| Case Comp observer | Score from the sheet | 30 |
| Case Comp judge, individual | Score from the sheet | 15 |
| Case Comp judge, team | Team's score, assigned through the `Team` column | 15 |
| Final interview | Sum of the `Score` columns, averaged over interviewers | 30 |

The interview is four criteria scored 1 to 5 plus a resume deep dive scored 1 to 10.

**Gaps:** missing case comp values are filled with the cohort average and `cc_missing` is set. Missing DWA and open rush values are not filled in and are flagged (`dwa_missing`, `open_rush_missing`).

---

## Slideshow template (only if you edit the template)

The tool fills in text boxes by their position in the slide. **Moving, adding, or deleting shapes in the template can put the wrong value in the wrong place.** If you must change it, update the `IDX_` numbers at the top of `slides/build_slides.py`.

| Field | Position (counting from 0) |
|---|---|
| Name (label, then value) | 0, 1 |
| Final score | 3 |
| Shrunk score | 6 |
| Bonus | 8 |
| Number of scores | 10 |
| Percentile | 12 |
| Application number | 13 |

The photo placeholder is skipped when slides are copied, and the headshot is added at a fixed position (left 6.25 in, top 0.78 in, 3.125 in wide by 3.65 in tall), cropped to fit and not stretched. Headshots are looked up by `<iu-email>` with the extension `.jpg`, `.jpeg`, `.png`, `.heic`, or `.heif`.

Long names: the name box is widened, the rows below are shifted down, and names over about 23 characters shrink in font size, down to a minimum of 13 pt.

---

## Check-in tools (Google Apps Script)

Full plain-language guide: `06_google_check_in_tools.md`. Summary of the code:

- **Location:** inside the check-in responses Sheet (Extensions > Apps Script). The `.gs` files in `apps_script/` are backups.
- **`data_cleansing.gs`:** `onFormSubmitTrigger` (installable on-form-submit trigger) validates the IU email (red if not `@iu.edu` or `@indiana.edu`), cleans the name into Column E (nicknames in parentheses or quotes become the first name, middle initials dropped, capitalization fixed, one-word names flagged yellow), and refreshes the scoring form's `PNM Name` dropdown. `runMegaDataCleanserManual` converts photo uploads to JPG through the Drive API and writes a share link to Column F. It skips rows already filled, so re-running is safe.
- **`slideshow_generator.gs`:** `generateSlideshow` prompts for a start and end PNM number and builds a Google Slides deck, 10 PNMs per slide, from Columns E and F. Keep each run to about 100 PNMs.
- **Column layout is hardcoded:** A timestamp, B IU email, C typed name, D upload link, E cleaned name, F cleaned image URL.
- **Limits and quirks:** Google stops scripts at about 6 minutes. Converted JPGs are shared "anyone with the link". "Last, First" names are not flipped. The check-in converter keeps the original file name (it does not rename by IU email); the application tools below do.
- The check-in and scoring tools are **not connected**. You move data between them by hand.

---

### Application headshot tools (Google Apps Script)

- **Location:** inside the *application* responses Sheet. Backups: `apps_script/application_headshots.gs`, `rename_headshots.gs`. Must stay in one Apps Script project (the rename tool uses `OUTPUT_HEADER_NAME` and `extractDriveId` from the main file).
- **`processUploadsToTargetFolder`:** finds columns by header: photo (`SOURCE_HEADER_NAME`, fallback column P), email (first header containing "email", fallback column C), output (`OUTPUT_HEADER_NAME`, created after the photo column if missing). For each row without an output link, gets the Drive file's `thumbnailLink` through the Drive API, rewrites it to `=s0` (full size), re-encodes to JPEG, saves it into `TARGET_FOLDER_ID` named `<email>.jpg` (illegal filename characters removed), shares it "anyone with the link", and writes the link. A row with no valid email keeps the photo's original name.
- **`renameExistingJpgs`:** renames each already-linked file to `<email>.jpg`.
- **Limits:** about 6 minutes per run, no self-timer; re-run to continue. Email case is preserved in the file name, but `build_slides.py` looks photos up by the **lowercased** email. Mac and Windows ignore case in file names, so this is fine there; a case-sensitive system would miss a photo named with capitals.

---

## Known issues and open ideas

- **Comment summary instructions** have not been tuned for what PSE specifically looks for.
- **Connecting** the check-in tools to the scoring tools would remove a manual step.
- **A different pull toward the middle** for above-average and below-average PNMs was discussed and never built.
- **Slide name sizing** was set by eye. Check the slides before deliberation.
- **Fixed column names:** if a Google Form question is renamed, the scoring tools stop with a `KeyError`.
