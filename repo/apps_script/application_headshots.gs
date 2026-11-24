/**
 * APPLICATION HEADSHOTS: convert, rename to IU email, save to one Drive folder
 * =============================================================================
 * WHAT IT DOES
 *   Reads the photo each PNM uploaded on the APPLICATION form, converts it to a
 *   true JPG, names it "<iu-email>.jpg", saves it in one Drive folder, and
 *   writes the link into a new "Cleaned JPEG Link" column. This folder is what
 *   you download into the local `headshots/` folder for slides/build_slides.py.
 *
 * WHERE IT LIVES
 *   Inside the APPLICATION responses Google Sheet (Extensions > Apps Script).
 *   This is a different Sheet from the check-in Sheet. See
 *   docs/06_google_check_in_tools.md.
 *
 * SETUP (once per semester)
 *   1. Make a Drive folder for the converted photos.
 *   2. Paste its ID (the string after /folders/ in its link) into
 *      TARGET_FOLDER_ID below.
 *   3. Check the three header names below match the application form's
 *      question text exactly. If the photo header is not found, it falls back
 *      to column P; if the email header is not found, column C.
 *
 * HOW TO RUN
 *   Pick `processUploadsToTargetFolder` in the function dropdown and click Run.
 *   Safe to re-run: rows that already have a link are skipped.
 *
 * QUIRKS
 *   - No timer: a very large batch can hit Google's ~6 minute limit. Just run
 *     again and it picks up where it stopped.
 *   - Converted files are shared "anyone with the link can view".
 *   - Two applications with the same email would create two files with the same
 *     name in the folder. Check for duplicates before downloading.
 *   - The email is used as typed (not lowercased). Keep email columns clean.
 *   - Keeps its own copy of OUTPUT_HEADER_NAME, which rename_headshots.gs also
 *     uses, so keep both files in the same Apps Script project.
 */
// =============================================================================
// CONFIGURATION
// =============================================================================
// 1. Paste your existing Google Drive Folder ID between the quotes below:
const TARGET_FOLDER_ID = "PASTE TARGET FOLDER ID HERE"; 

const SOURCE_HEADER_NAME = "Please upload a recent picture of yourself.";
const EMAIL_HEADER_NAME = "IU Email";
const OUTPUT_HEADER_NAME = "Cleaned JPEG Link";

// =============================================================================
// MAIN FUNCTION: Run this to convert, rename, and save true JPEGs
// =============================================================================
function processUploadsToTargetFolder() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // 1. Get header row to dynamically locate columns
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  // Locate Column P ("Please upload...")
  let sourceColIndex = headers.indexOf(SOURCE_HEADER_NAME) + 1;
  if (sourceColIndex === 0) sourceColIndex = 16; // Default to Column P (index 16)
  
  // Locate Column C ("IU Email")
  let emailColIndex = headers.findIndex(h => h.toString().toLowerCase().trim().includes("email")) + 1;
  if (emailColIndex === 0) emailColIndex = 3; // Default to Column C (index 3)

  // Locate or create output column ("Cleaned JPEG Link") right next to Column P
  let outputColIndex = headers.indexOf(OUTPUT_HEADER_NAME) + 1;
  if (outputColIndex === 0) {
    outputColIndex = sourceColIndex + 1;
    sheet.insertColumnAfter(sourceColIndex);
    sheet.getRange(1, outputColIndex)
         .setValue(OUTPUT_HEADER_NAME)
         .setFontWeight("bold")
         .setBackground("#E0E0E0");
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    ss.toast("No data rows found.", "Image Processor");
    return;
  }

  // 2. Get target folder object
  let targetFolder;
  try {
    targetFolder = DriveApp.getFolderById(TARGET_FOLDER_ID);
  } catch (e) {
    SpreadsheetApp.getUi().alert("⚠️ Invalid Folder ID. Please check the TARGET_FOLDER_ID variable.");
    return;
  }

  // 3. Read email links, source image links, and existing output links in batch
  const emailValues = sheet.getRange(2, emailColIndex, lastRow - 1, 1).getValues();
  const sourceValues = sheet.getRange(2, sourceColIndex, lastRow - 1, 1).getValues();
  const outputValues = sheet.getRange(2, outputColIndex, lastRow - 1, 1).getValues();
  
  ss.toast("Starting image conversion and upload...", "Image Processor", 5);
  let countProcessed = 0;

  // 4. Loop through each row
  for (let i = 0; i < sourceValues.length; i++) {
    const row = i + 2;
    const rawEmail = emailValues[i][0] ? emailValues[i][0].toString().trim() : "";
    const rawUrl = sourceValues[i][0] ? sourceValues[i][0].toString().trim() : "";
    const existingOutput = outputValues[i][0] ? outputValues[i][0].toString().trim() : "";

    // SKIP IF: Link is empty OR row was already processed
    if (!rawUrl || existingOutput !== "") continue;

    // Extract Drive File ID from URL
    const fileId = extractDriveId(rawUrl);
    if (!fileId) {
      Logger.log(`⏩ Skipping Row ${row}: Could not extract Drive ID from URL.`);
      continue;
    }

    try {
      // Convert image, rename to IU Email, & save as true JPG to folder
      const newJpgUrl = convertAndSaveJpg(fileId, targetFolder, rawEmail);
      
      if (newJpgUrl) {
        sheet.getRange(row, outputColIndex).setValue(newJpgUrl);
        countProcessed++;
        Logger.log(`✅ Row ${row}: Saved true JPG (${rawEmail || 'Default Name'}) to folder & updated sheet.`);
      }
    } catch (err) {
      Logger.log(`❌ Error processing Row ${row} (ID: ${fileId}): ${err.message}`);
    }
  }

  // Done notification
  ss.toast(`Done! Converted and saved ${countProcessed} new JPGs to your folder.`, "🔥 Complete", 8);
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// Parses Drive File ID from common Google Drive URL structures
function extractDriveId(url) {
  const match = url.match(/(?:id=|\/d\/)([a-zA-Z0-9_-]+)/);
  return match ? match[1] : null;
}

// Fetches image, converts metadata/bytes to TRUE JPEG format, and saves to Drive folder
function convertAndSaveJpg(fileId, targetFolder, customName) {
  const file = DriveApp.getFileById(fileId);
  const originalName = file.getName();
  const baseName = originalName.replace(/\.[^/.]+$/, ""); // Strip file extension

  // Construct target file name
  let newFileName;
  if (customName) {
    const cleanCustomName = customName.replace(/[/\\?%*:|"<>]/g, ""); 
    newFileName = cleanCustomName.toLowerCase().endsWith(".jpg") ? cleanCustomName : `${cleanCustomName}.jpg`;
  } else {
    newFileName = `${baseName}.jpg`;
  }

  // Request thumbnail link from Drive API
  const driveApiUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?fields=thumbnailLink`;
  const response = UrlFetchApp.fetch(driveApiUrl, {
    headers: { 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true
  });

  if (response.getResponseCode() !== 200) {
    throw new Error(`Drive API error (${response.getResponseCode()})`);
  }

  const metadata = JSON.parse(response.getContentText());
  const thumbnailLink = metadata.thumbnailLink;

  if (!thumbnailLink) {
    throw new Error("Unable to fetch image thumbnail/preview.");
  }

  // Force full resolution rendering (=s0)
  const highResJpgUrl = thumbnailLink.replace(/=s\d+/, '=s0');

  // Fetch raw response blob
  const rawBlob = UrlFetchApp.fetch(highResJpgUrl).getBlob();

  // FORCE RE-ENCODING TO TRUE JPEG FORMAT
  const trueJpgBlob = rawBlob.getAs(MimeType.JPEG);
  trueJpgBlob.setName(newFileName);

  // Create file inside the TARGET folder
  const newJpgFile = targetFolder.createFile(trueJpgBlob);
  newJpgFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  return `https://drive.google.com/open?id=${newJpgFile.getId()}`;
}
