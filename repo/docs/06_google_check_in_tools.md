# 6. Google Tools (Check-In and Application Headshots)

There are **two sets of tools, in two different Google Sheets**. Neither lives on your computer. A backup copy of every file's code is in the `apps_script/` folder.

| Set | Sheet it lives in | What it is for |
|---|---|---|
| **Check-in tools** (Part 1) | The check-in responses Sheet | Cleans names and emails, updates the scoring form dropdown, converts check-in photos, builds the roster slideshow |
| **Application headshot tools** (Part 2) | The application responses Sheet | Turns application photos into `<iu-email>.jpg` files in one Drive folder. **This is the folder that feeds the deliberation slideshow** |

---

# Part 1: Check-in tools

**You do not need to read or change the code.** This page explains what the tools do, how to set them up each semester, and what to do when something looks off. Atulya will walk you through it in person.

---

## The pieces

| Piece | What it is |
|---|---|
| **Check-in form** | The Google Form PNMs fill out at each event |
| **Responses Sheet** | The Google Sheet that collects the form answers. **The tools live in this Sheet** (menu: Extensions > Apps Script) |
| **Scoring form** | The Google Form actives use to score PNMs. It has a dropdown of PNM names that the tools keep up to date |
| `data_cleansing.gs` | Cleans names and emails, updates the dropdown, converts photos |
| `slideshow_generator.gs` | Builds the roster slideshow in Google Slides |

## What the tools expect in the Sheet

The tools read and write specific columns, so **do not insert, delete, or reorder columns** in the responses tab.

| Column | Contents | Who fills it |
|---|---|---|
| A | Timestamp | The form |
| B | IU email | The form |
| C | Name as the PNM typed it | The form |
| D | Photo upload link | The form (file upload question) |
| **E** | **Cleaned Name** | The tool |
| **F** | **Cleaned Image URL** | The tool |

If you ever change the order of the form's questions, tell Atulya first. The column numbers are written into the code.

---

## What happens, step by step

```
PNM submits the check-in form
        |
        v   (automatic, within a few seconds)
Email checked  -> red cell if it is not an @iu.edu or @indiana.edu address
Name cleaned   -> Column E (yellow if it needs a human look)
Dropdown       -> scoring form dropdown refreshed
        |
        v   (you run this by hand, once photos have come in)
Photos         -> converted to JPG, link written to Column F
        |
        v   (you run this by hand, when you want the roster)
Slideshow      -> 10 PNMs per slide in Google Slides
```

**What the name cleaning does** (examples):

| Typed | Becomes in Column E |
|---|---|
| `Zhengjia (Esther) Sun` | `Esther Sun` (the nickname in parentheses or quotes becomes the first name) |
| `Ryan J. Van Slyke` | `Ryan Van Slyke` (middle initials are dropped) |
| `mary kate olsen` | `Mary Kate Olsen` (capitalization is fixed) |
| `giannis` | `Giannis`, **and the cell turns yellow** because it is a single word and probably needs a last name |

**What the colors mean:**
- **Red email cell:** not an IU email. Check whether it is a typo or the PNM used a personal address.
- **Yellow name cell:** a one-word name. Look the PNM up and fix Column E by hand. Your edit is kept.

---

## Each semester: setting it up

1. **Make a copy of last semester's responses Sheet** (File > Make a copy). The code comes along with the copy. **Triggers do not**, so you must redo step 4.
2. **Connect your new check-in form** to the new Sheet (in the form: Responses tab > link to Sheets), or have Atulya show you. **[Atulya to fill in: how the form and Sheet are linked]**
3. **Paste your scoring form's ID** into the code. In the Sheet, go to Extensions > Apps Script, open `data_cleansing`, and replace `PASTE FORM ID HERE` near the top with your scoring form's ID. The ID is the long string of letters and numbers in the form's edit link, between `/d/` and `/edit`. The scoring form must have a dropdown question titled exactly **PNM Name**.
4. **Turn on the automatic part (the trigger).** In the Apps Script editor, click the **clock icon** on the left (Triggers), then **Add Trigger**. Choose:
   - Function: `onFormSubmitTrigger`
   - Event source: From spreadsheet
   - Event type: On form submit

   Save. The first time, Google asks you to authorize the script. Click **Advanced**, then **Go to (project name)**, then **Allow**. This warning is normal for personal scripts.
5. **Test it.** Submit the check-in form yourself with a made-up name and a photo. Within a few seconds, Column E should fill in and the scoring form's dropdown should include the new name.

---

## At each event

1. **Skim the Sheet:** look for red emails and yellow names and fix them. Fix Column E by hand if needed.
2. **Convert the photos** once uploads have come in:
   - In the Sheet, go to **Extensions > Apps Script**.
   - In the function dropdown at the top, choose **`runMegaDataCleanserManual`** and click **Run**.
   - Switch back to the Sheet. A message in the corner says "Scanning and converting new images...", then "Done! Processed N new images."
   - Rows that already have a link in Column F are skipped, so **it is safe to run again** if it stops early or new photos arrive.
3. **Build the roster slideshow** when you want it:
   - In the Apps Script editor, choose **`generateSlideshow`** and click **Run**.
   - Switch to the Sheet. It asks for a **starting number** and an **ending number**. For everyone, start at 1 and end at the total. **Keep each run to about 100 PNMs.** For 250 PNMs, run 1-100, 101-200, and 201-250.
   - A box pops up with a button to open the finished slideshow. It is saved in your Google Drive, titled "Meet the Chapter - PNMs 1 to 100".
4. **Check the slideshow:** flip through it for blank spots (a photo that failed) and long names that wrap.

**The deliberation slideshow does not use these photos.** It uses the application headshots from Part 2.

---

## Things to know

- **Photo privacy.** Each converted JPG is shared as "anyone with the link can view". It is not searchable, but anyone who has the link can open it. Do not post the links anywhere public. If you would like them restricted to IU accounts only, ask Atulya. It is a one-line change.
- **"Last, First" is not flipped.** `Smith, John` becomes `Smith John`. If a PNM typed their name that way, fix Column E by hand. (The scoring tools flip these separately.)
- **Run time.** Google stops a script after about 6 minutes. A very large batch of photos may need a second run. It continues where it left off.
- **Two sources of truth.** Column E (cleaned name) is what the slideshow and dropdown use. The original in Column C is never changed.
- **The Sheet and the scoring tools are separate.** Data moves between them by hand, as the runbook describes.

---

## When something goes wrong

| What you see | Likely cause | Fix |
|---|---|---|
| New submissions do not get a cleaned name in Column E | The trigger is missing. It does not copy over with a copy of the Sheet | Set up the trigger (step 4 above) |
| The scoring form dropdown does not update | Wrong form ID, or the dropdown's title is not exactly `PNM Name` | Check both. Open **Executions** (left side of the Apps Script editor) and read the latest log line |
| "Authorization required" or a permissions warning | The script has not been approved by your account yet | Run any function once and click through Advanced > Go to project > Allow |
| `Skipping Row N: Invalid/Unrecognized Drive URL format` in the log | That row's photo link is blank or not a Drive link | Check Column D for that row. The PNM may not have uploaded a photo |
| `Drive API returned status 403` or `404` for a row | The photo file is not accessible to your account | Make sure the form's upload folder belongs to, or is shared with, your Google account |
| "Exceeded maximum execution time" | The batch was too big | Run again (photos) or use a smaller number range (slideshow) |
| A slide has a name but no photo | That photo failed to load | Check that row's Column F link opens. Re-run the photo step for it |
| A "Meet the Chapter" deck appears but looks empty | Columns E and F are empty | Run the photo step first and make sure names cleaned correctly |

**Reading the log:** in the Apps Script editor, click **Executions** on the left, click a run, and read the lines. A ✅ means that row worked. A ⚠️ or ❌ names the row and the problem.

---

## Backing up the code

The Sheet is the real home of the tools, so **keep making a copy of the whole Sheet each semester**. The files in `apps_script/` are a backup. If you ever need to restore one, open the Apps Script editor, create a file with the same name, paste the code, and set the trigger again.

---

# Part 2: Application headshot tools

These feed `slides/build_slides.py`. That script looks for a file named exactly `<iu-email>.jpg` for each PNM (for example `jsmith@iu.edu.jpg`), so these tools do the converting and naming.

## The pieces

| Piece | What it is |
|---|---|
| **Application form** | The form PNMs fill out after open rush, including a photo upload question |
| **Application responses Sheet** | Where the answers land. **The tools live in this Sheet** |
| `application_headshots.gs` | The main tool: converts each photo and names it with the IU email |
| `rename_headshots.gs` | A fix-up tool: renames photos that were already converted |
| **The headshots folder (in Drive)** | One Drive folder that collects all the finished `<iu-email>.jpg` files |

## Setup (once per semester)

1. **Make a Drive folder** for the converted photos (for example "Fall 2027 Application Headshots"). Share it only with people the bylaws allow to see PNM data.
2. **Copy last semester's application responses Sheet** (File > Make a copy), or connect the new application form to a new Sheet. **[Atulya to fill in: which of these you do]**
3. **Paste the folder's ID** into the code. In the Sheet: Extensions > Apps Script > `application_headshots`. Replace `PASTE TARGET FOLDER ID HERE` with the ID (the long string after `/folders/` in the folder's link).
4. **Check the three header names** near the top match the form's wording exactly:
   - the photo question (currently "Please upload a recent picture of yourself.")
   - the email question (the tool finds the first header containing the word "email")
   - the output column "Cleaned JPEG Link" (the tool creates it for you the first time, right after the photo column)

   If the form's wording changed, update the quoted text in the code to match.
5. **Authorize it** the first time you run it (Advanced > Go to project > Allow).

## Each time applications come in

1. Open the **application responses Sheet**.
2. In Extensions > Apps Script, choose **`processUploadsToTargetFolder`** and click **Run**.
3. Back in the Sheet, a message says "Starting image conversion and upload...", then "Done! Converted and saved N new JPGs to your folder."
4. A new **Cleaned JPEG Link** column appears with a link for each PNM. Rows that already have a link are skipped, so **running it again is safe**.
5. **Fix-up:** if some photos were converted before names were set, or an email was corrected after conversion, run **`renameExistingJpgs`**. It renames those files to match the email now in the Sheet.

## Getting the photos onto your computer

1. Open the headshots folder in Drive.
2. Select all files, then right-click > **Download**. Drive gives you a zip file.
3. Unzip it. Move the `.jpg` files into the `headshots` folder **inside your data folder** (`DATA_DIR/headshots`; the name can be changed with `HEADSHOTS_DIR` in `.env`). **[Atulya to confirm this is how you do it]**
4. Run `python3 check_setup.py`. It reports how many headshots it found.
5. Files keep their `<iu-email>.jpg` names through the zip, which is what the slideshow needs.

**Never commit the headshots folder to git.** It is already ignored, but double-check before sharing the repo.

## Things to know

- **Photo privacy.** Each converted JPG is shared as "anyone with the link can view". Do not post the links anywhere public. Asking for IU-only sharing is a one-line change.
- **No timer.** A very large batch may stop at Google's roughly 6 minute limit. Run it again and it continues.
- **Capital letters in an email** (`JSmith@iu.edu`) are kept in the photo's file name. The slideshow looks for the lowercase version. This works on Mac and Windows but would fail on a case-sensitive system.
- **Same email twice** (a PNM applied twice) gives two files with the same name in the Drive folder. Delete the extra before downloading.
- **Missing or bad email** in a row gives the file the photo's original name instead. The slideshow will not find it. Fix the email in the Sheet, then run `renameExistingJpgs`.
- **The two tools must stay in the same Apps Script project.** `rename_headshots.gs` borrows a setting and a helper from `application_headshots.gs`.

## When something goes wrong

| What you see | Likely cause | Fix |
|---|---|---|
| Alert: "Invalid Folder ID" | Folder ID not pasted, or it is wrong | Paste the ID from the Drive folder link |
| Log says `Could not extract Drive ID from URL` for a row | That row has a blank or non-Drive photo link | Check the photo column for that row |
| Log says `Drive API error (403)` or `(404)` | Your Google account cannot open that uploaded photo | Make sure the form's upload folder is yours or shared with you |
| Log says `Unable to fetch image thumbnail/preview` | Drive could not make a preview (odd file type or a PDF) | Ask the PNM for a normal photo, or save one by hand as `<iu-email>.jpg` |
| "Exceeded maximum execution time" | Batch too big for one run | Run again |
| A PNM shows a blank slide photo | Their file is missing, misnamed, or the email differs from the slides input file | Check the file name against the email in `slides_input.csv`, rename if needed |
| "Could not find 'Cleaned JPEG Link' column" | `renameExistingJpgs` was run before the main tool | Run `processUploadsToTargetFolder` first |

**Reading the log:** Extensions > Apps Script > **Executions** on the left, click the run, read the lines. A checkmark means that row worked.
