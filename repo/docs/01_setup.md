# 1. Setup (do this once)

This takes about 15 minutes. You only do it the first time, and Atulya will do it with you in person. These notes are here so you can repeat it on a new computer.

You will:
1. Install Python (the program that runs the scoring tools).
2. Put this folder on your computer.
3. Install a few add-ons.
4. Tell the tools where your data folder is.
5. Run the practice data to confirm it all works.

You will use the **Terminal** (Mac) or **Command Prompt / PowerShell** (Windows). It is a window where you type a command and press Enter. You are only copying and pasting commands from this page.

---

## Step 1. Install Python

1. Go to **python.org/downloads** and download the latest version (3.10 or newer).
2. Run the installer.
   - **Windows:** on the first screen, tick **"Add Python to PATH"** before clicking Install. This is the one step people miss.
   - **Mac:** click through the installer normally.
3. Check it worked. Open the Terminal and type:

   ```
   python3 --version
   ```

   (On Windows, type `python --version`.) You should see something like `Python 3.12.1`. If you see "command not found", close and reopen the Terminal and try again.

> **Windows note:** everywhere this folder says `python3`, type `python` instead.

## Step 2. Put this folder on your computer

Atulya will give you this folder (through the shared Drive or a download). Copy it somewhere easy to find, such as your **Desktop**. Do **not** put it inside the shared Drive folder that holds the real PNM data. Keep the tools and the data in different places.

## Step 3. Open the Terminal inside this folder

- **Mac:** open Terminal, type `cd ` (with a space after it), drag the folder from Finder into the Terminal window, and press Enter.
- **Windows:** open the folder in File Explorer, click the address bar at the top, type `cmd`, and press Enter.

Everything from now on is typed in that window, so keep it open. To confirm you are in the right place, type `ls` (Mac) or `dir` (Windows). You should see `README.md`, `config.py`, and `check_setup.py` in the list.

## Step 4. Install the add-ons

Type this and press Enter:

```
pip3 install -r requirements.txt
```

(Windows: `pip install -r requirements.txt`.) A lot of text scrolls by for a minute or two. That is normal. You are done when you get your prompt back. If it ends with a red "ERROR" line, text Atulya the last line.

## Step 5. Check it with the practice data

Type:

```
python3 check_setup.py
```

You will see a list of lines starting with `[ok]`, `[note]`, or `[FIX]`:

- `[ok]` means that is fine.
- `[note]` means it is not a problem. It is just information.
- `[FIX]` means something needs attention. The line says what.

Then try the real thing on the made-up people:

```
python3 scoring/closed_rush_scoring.py
```

You should see a short report ending with a list of fake names and scores and the words "Output saved to". If you do, **everything works**.

---

## Pointing the tools at your real data (after the walkthrough)

The tools read from, and write to, **one data folder**. Right now that is the practice folder. For real recruitment you point it at the semester's folder from the shared Drive.

1. Make sure the Drive folder is **downloaded to your computer** (in Google Drive for desktop, right-click the folder and choose "Available offline"). The tools cannot read files that are only in the cloud.
2. In this folder, find the file called `.env.example`. Make a copy of it and name the copy `.env` (just `.env`, nothing before the dot).
   - Files starting with a dot are hidden on Macs. Press **Command + Shift + .** in Finder to show them.
3. Open `.env` in any text editor (Notepad, TextEdit, VS Code) and fill in this line:

   ```
   DATA_DIR=/Users/yourname/Desktop/Fall2027
   ```

   Use the real path to the data folder. To get the path: **Mac:** right-click the folder, hold **Option**, choose "Copy ... as Pathname". **Windows:** hold **Shift**, right-click the folder, choose "Copy as path" (then remove the quotation marks).
4. Save. Run `python3 check_setup.py` again. It now checks your real folder and tells you which files are missing or misnamed.

### Your own API key (only for comment summaries)

The comment-summary tool uses an AI service and needs your own key. This is optional, and you can skip it until you want summaries. Atulya will show you how to get one. When you have it, paste it into `.env` on the `ANTHROPIC_API_KEY=` line. Never share the key or put it anywhere else.

---

## When you are done

You never need to repeat this setup on the same computer. For each new semester you only change `DATA_DIR` to the new folder.
