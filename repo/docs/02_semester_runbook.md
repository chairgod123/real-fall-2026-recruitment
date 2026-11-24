# 2. Semester Runbook

A recipe book for running recruitment. **Find the heading for where you are and follow it.** You do not need to read it from top to bottom.

For *when* to make decisions (counted back from the start of recruitment), use the timeline in the VPR handoff document. This runbook covers the scores and slideshow only.

**Commands:** type them in the Terminal, from inside this folder (see `01_setup.md`). Mac: `python3`. Windows: `python`.

**Placeholders:** items marked **[Atulya to fill in]** are things he will show you in person.

---

## The big picture

1. Actives score PNMs after each event, in Google Forms.
2. Those scores get combined into one spreadsheet.
3. You run a command, and it produces a ranked list.
4. You run another command, and it produces a slideshow.
5. The chapter deliberates using the list and the slides.

The tools do the arithmetic. **Your job is to feed them clean files, read what they report, and decide what to do with the results.**

---

## A. Before recruitment starts (one-time prep)

- [ ] **Make this semester's data folder** in the shared Drive (for example `Fall2027`). Share it only with people the chapter bylaws allow to see PNM data.
- [ ] **Download it to your computer** ("Available offline") and set `DATA_DIR` in `.env` (see `01_setup.md`).
- [ ] **Run `python3 check_setup.py`.** Fix anything marked `[FIX]`.
- [ ] **Copy last semester's forms** (check-in and scoring) and the responses Sheet that holds the check-in tools. Copying the Sheet copies the code, but **not the trigger**, so set it up again. Steps are in `06_google_check_in_tools.md`. **[Atulya to fill in: where last semester's forms and Sheet are]**
- [ ] **Test the check-in tool** with two or three fake PNMs before the first event, including one photo from an iPhone. Confirm Column E (cleaned name) fills in, the scoring form's dropdown updates, and the photo gets a link in Column F.
- [ ] **Decide how you want scoring to work** and change `config.py` if needed (see `03_scoring_in_plain_english.md`). Decide **before** the first event, not after you have seen the scores.
- [ ] **Open the slide template** and confirm it holds only placeholder text and no real PNM.

---

## B. After each open rush event

1. **Run the check-in tools** (Part 1 of the Google guide) so the roster and photos are clean: fix red and yellow cells, then run `runMegaDataCleanserManual` (see `06_google_check_in_tools.md`).
2. **Wait for actives to submit their scores** in the scoring form. Remind them if needed.
3. **Add this event's scores to the combined spreadsheet.** In Excel, open the combined-scores file and click **Data > Refresh All**. This pulls in the newest event. **[Atulya to fill in: file location and how to add a new event]**
4. **Save it as a CSV** into your data folder, using the file name set in `.env` (the default is `open_rush_scores.csv`).
   - Save as **"CSV (Comma delimited)"**, not "CSV UTF-8".
5. **Glance at the data** before moving on: Are all the events there? Any blank scores or obvious typos?

> Do not rename an event partway through the semester. Scores are grouped by the event name.

---

## C. After open rush ends: ranking applicants

1. **Download the applications** from the Google Form (Responses tab, then the three-dot menu, then Download responses (.csv)). Save it in your data folder under the name set in `.env` (default `applications_form_responses.csv`).
2. **Run the check:** `python3 check_setup.py`.
3. **Run the ranking:**

   ```
   python3 scoring/fall2026scoring.py
   ```

4. **Read what it printed.** The most useful parts:

   | You see | What it means | What to do |
   |---|---|---|
   | `Likely duplicates` with two similar names | The same person may be spelled two ways | Fix the spelling in the source sheet and re-run |
   | `Dropped ... row(s) with no valid email` | Someone typed a bad email on the application | Follow up with that person by hand |
   | `repeat submissions (same email)` | Someone submitted twice | Nothing, it keeps the most recent. Check that this is what you want |
   | `Applicants with zero interactions` | Applicants nobody scored | They are listed at the bottom in red with no rank. Decide how to treat them **before** you look at who they are |

5. **Open the results.** A new file, `recruitment_scores.xlsx`, appears in your data folder. Open it in Excel.
   - **Final Score** is what the list is ranked by. Higher is better.
   - **Percentile** shows where someone stands: 90 means ahead of about 90% of scored people.
   - **interaction_count** is how many scores they received. A very low number means the ranking is less certain for that person.
   - **Red rows** are applicants with no scores. They have no percentile on purpose.
6. **Sanity check.** Do the top and bottom look reasonable? A surprising result is worth a second look. It is sometimes a typo and sometimes the system working as designed. If you cannot tell which, ask Atulya.

There is a second version, `python3 scoring/fall2026scoring_allpnms.py`, that ranks **everyone who was scored**, even people who did not apply. It writes `recruitment_scores_all.xlsx`. Use it when you want to see the whole pool.

7. **Choose who is invited to closed rush** and make the roster file: a CSV with the columns `Name` and `Email`. **The file name must contain the words `closed` and `bids`** (for example `closed_bids.csv`).

---

## D. During closed rush

After each closed rush event, save its score sheet in your data folder. **The file name has to contain a keyword** so the tool can find it:

| Event | File name must contain |
|---|---|
| The roster of invited PNMs | `closed` and `bids` |
| Dinner with Actives | `dwa` |
| Case Comp observer scores | `observer` |
| Case Comp judge scores, per person | `individual` |
| Case Comp judge scores, per team | `team` |
| Final Interviews | `interview` |

Only one file should match each word. If you keep an old version, move it out of the folder.

**Case Comp:** other people write the case and the scoring rubric. Before the event, ask the Case Comp chair to confirm the score sheets will have the columns listed in `05_technical_reference.md`.

**If a PNM withdraws, or a score sheet uses a nickname:** create a small file called `roster_overrides.json` in your data folder:

```json
{"withdrawn": ["First Last"], "aliases": {"nickname": "Roster Name"}}
```

Use the exact roster spelling. Leave out the file entirely if you have no withdrawals.

You can run closed rush scoring at any time, even before every event is done. Totals that are missing the final interview are marked provisional.

---

## E. Before deliberation

1. **Run closed rush scoring:**

   ```
   python3 scoring/closed_rush_scoring.py
   ```

2. **Read the report it prints.** Look for:

   | You see | What it means | What to do |
   |---|---|---|
   | `missing DWA data` or `missing Open Rush data` for a named PNM | A typo in a name or email in a score sheet | Fix the source file, re-run. The PNM is not scored fairly until you do |
   | `CC missing (flagged)` with a number | Some PNMs have no case comp score | They were given the average. Tell the room |
   | `provisional` | Final interviews are not in yet | Normal until interviews are done |

3. **Open `closed_rush_scores.csv`** in Excel. It has one row per PNM, in rank order:
   - **total_score** is out of 100.
   - The **pts_** columns show the points earned from each event, so you can see *why* someone is where they are.
   - **cc_missing, dwa_missing, open_rush_missing:** `True` means check that row.
   - The comment columns collect what actives wrote.
4. **(Optional) Run the comment summaries**: `python3 scoring/summarize_comments.py`. This needs your API key. Always check a flagged concern against the original comments before acting on it.
5. **Build the slideshow:** `python3 slides/build_slides.py`.
   - It needs a slides input file with each PNM's rank, name, email, scores, and application number. **[Atulya to fill in: how this file is made]**
   - It also needs the headshots in a `headshots` folder on your computer, each saved as `<iu-email>.jpg`. The Google application-headshot tool makes these; download them from Drive as described in `06_google_check_in_tools.md` (Part 2) and put them in `DATA_DIR/headshots`.
   - It writes `recruitment_slides.pptx` **into your data folder, never into the repo** (these files are large and contain real faces, so they are never committed to git). **Open it and flip through it** before deliberation. Look for names that run off the edge and missing photos. The tool lists missing photos when it finishes.
6. **Choose your cutoffs** (see below) and write them down **before** anyone looks at names.

---

## F. Deliberation day

The structure Atulya used, which you can change:
- **Top group:** admitted automatically. Show the list so everyone can see it, but limit discussion time.
- **Middle group (the "bubble"):** discussed one at a time, using the scores and comments as a starting point.
- **Bottom group:** denied automatically.

The cutoffs came from finding natural gaps in the scores, meaning places where the numbers drop noticeably. In the semester before Fall 2026, this sorted 67 PNMs into 12 / 34 / 21, and deliberation took 6 to 7 hours.

**Agree on the cutoffs before discussing individual people.** Once names are on the table, a cutoff turns into an argument about a person, not about a score.

After deliberation comes the PFC bid process. That is covered in the VPR handoff document.

---

## G. After the cycle

- [ ] **Move everything into the semester's Drive folder** (inputs, results, the slideshow, and the cutoffs you used).
- [ ] **Write down baselines** (attendance per event, number of applications, PNMs at each stage). This semester's goals had to use placeholder targets because there was no baseline.
- [ ] **Write a few lines on what you changed and why** so the next VPR knows.
