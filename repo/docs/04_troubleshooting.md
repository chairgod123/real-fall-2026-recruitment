# 4. Troubleshooting

**Almost nothing here is dangerous.** The tools only read your files and create new result files. They never change or delete your data, so you cannot ruin anything by running them again. If something looks wrong, fix the cause and re-run.

## First, three things to try

1. **Run `python3 check_setup.py`.** It finds most problems and says what to do.
2. **Read the last line the Terminal printed.** Error messages are long, but the last line is the one that matters. Scroll to the bottom and read only that.
3. **Close Excel** if you were looking at a results file. An open file can block the tool from updating it.

---

## Problems running a command

| You see | What it means | Fix |
|---|---|---|
| `command not found: python3` (Mac) or `'python' is not recognized` (Windows) | Python is not installed, or the Terminal needs reopening | Close and reopen the Terminal. If it persists, reinstall Python. On Windows, tick "Add Python to PATH" in the installer |
| `ModuleNotFoundError: No module named 'pandas'` (or `thefuzz`, `pptx`, ...) | An add-on is missing | Run `pip3 install -r requirements.txt` (Windows: `pip install -r requirements.txt`) |
| `can't open file ... No such file or directory` | The Terminal is not inside this folder | Redo step 3 in `01_setup.md`, then try again |
| `DATA_DIR does not exist: ...` | The data folder path in `.env` is wrong, or the folder was moved | Fix the `DATA_DIR` line in `.env`. Copy the path again from Finder or File Explorer |
| `PermissionError ... recruitment_scores.xlsx` | The results file is open in Excel | Close it and re-run |

---

## Problems with the files

| You see | What it means | Fix |
|---|---|---|
| `FileNotFoundError ... open_rush_scores.csv` (or another file name) | The input file is not in the data folder, or is named differently | Save it in the data folder with exactly that name, or change the name in `.env` |
| `No file matching keywords ('dwa',) found` | Closed rush could not find a file with that word in its name | Rename the file so its name contains the word. The list of files it saw is printed underneath |
| `Multiple files match keywords ...` | Two files contain the same word, for example an old and a new `dwa` export | Move or rename the older one out of the folder |
| `Couldn't find the open rush file` | Closed rush could not find the combined open rush scores | Make sure that file is in the data folder and still has the columns `PNM Email` and `Event` |
| `KeyError: 'Professional Score'` (or another column name) | A column in the file is named differently from what the tool expects, usually because a Google Form question was renamed | Restore the original column name, or ask Atulya. The expected names are in `05_technical_reference.md` |
| `Couldn't find a matching column for: ...` (slideshow) | Same, for the slides input file | The message lists the headers it saw. Rename the one that is off |
| Odd characters in comments, such as `â€™` | The file was saved with a different text encoding | Re-save as **"CSV (Comma delimited)"** in Excel and re-run |

---

## Problems with the results

| You see | What it means | Fix |
|---|---|---|
| A PNM is **missing from the results** | Their email or name does not match across files | Search the source sheets for them. Look for a typo in the email, a nickname, or a space. Fix the source file and re-run |
| `missing DWA data` or `missing Open Rush data` for someone | Same cause, a name or email mismatch | Same fix. Do not deliberate until this is fixed |
| `Likely duplicates` lists two names | The same person may be spelled two ways | Fix the spelling in the source. Scoring is keyed on email, so it still works, but fix it anyway so the slides look right |
| Someone's rank looks wrong | Often it is the right result for a reason that is not obvious | Check their number of scores and any low scores, then see "Why is this person ranked there?" in `03_scoring_in_plain_english.md`. If it still looks wrong, send Atulya the PNM's row |
| Results did not change after you edited `config.py` | Not saved, or the command was not re-run | Save the file and run the command again |
| `WARNING: closed rush weights add up to ...` | The six shares in `config.py` do not total 1.00 | Adjust them so they add up to exactly 1.00 |
| Totals marked `provisional` | The final interview file is missing | Normal until interviews are done. Add the file and re-run |

---

## Problems with the slideshow

| You see | What it means | Fix |
|---|---|---|
| `No headshot file found for ...` (a list of names) | No photo named with that person's email | Check the photo exists in your `headshots` folder and is named `<iu-email>.jpg`. If the photo never converted, re-run `processUploadsToTargetFolder` in the **application** Sheet, then `renameExistingJpgs` if the email changed (see `06_google_check_in_tools.md`, Part 2). Missing photos do not stop the slideshow, so the slide is simply blank |
| `Headshot file existed but couldn't be read` | The photo file is damaged | Ask the PNM for a new one, or convert it again |
| A long name runs onto the next line | The name is too long for the box | Shorten it in the slides input file (for example, drop a middle name) and re-run |
| A slide is blank or mislabeled | The template was changed | Do not move or delete shapes in the template. See `05_technical_reference.md` |

---

## Comment summaries

| You see | Fix |
|---|---|
| An error mentioning `api_key`, `authentication`, or `401` | Your key is missing or wrong. Check the `ANTHROPIC_API_KEY=` line in `.env` |
| An error mentioning `credit` or `billing` | Your AI account is out of credit. Add credit on the provider's site |

---

## When to text Atulya

Send him the **last line** the Terminal printed, plus which command you ran. It is helpful to include a screenshot of the Terminal. Do **not** send PNM names or emails over text. Say "a PNM named in row 12" and describe it, or share it through the shared Drive.

**You never need to apologize for asking.** He wrote this and he expects questions.

---

**Problems with the Google tools** (cleaned names not filling in, dropdown not updating, photo errors, timeouts) have their own table at the bottom of `06_google_check_in_tools.md`.
