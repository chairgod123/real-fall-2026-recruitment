/**
 * PSE RECRUITMENT: CHECK-IN DATA CLEANSER (Google Apps Script)
 * =============================================================================
 * This file lives inside the Google Sheet that collects check-in form
 * responses (Sheet menu: Extensions > Apps Script). It does not run on your
 * computer. See docs/06_google_check_in_tools.md for the full walkthrough.
 *
 * WHAT IT DOES
 *   1. Every time a PNM submits the check-in form (automatic, via a trigger):
 *        - flags non-IU emails (cell turns red)
 *        - cleans the name into Column E (nicknames in parentheses or quotes
 *          become the first name, middle initials are dropped, capitalization
 *          is fixed). A single-word name is flagged yellow for a manual look
 *        - refreshes the dropdown in the SCORING form so actives can pick
 *          the PNM, shown as "First Last - email@iu.edu"
 *   2. When you run runMegaDataCleanserManual() (manual): converts each
 *      uploaded photo to JPG and puts a link in Column F.
 *
 * EXPECTED SHEET LAYOUT (the code depends on these exact columns)
 *   A  Timestamp (from the form)
 *   B  IU email
 *   C  Name as typed
 *   D  Photo upload link (from the form's file-upload question)
 *   E  Cleaned Name   (written by this script)
 *   F  Cleaned Image URL (written by this script)
 * If you reorder the form's questions, these column numbers must be updated
 * in the code below. Ask Atulya before changing the form.
 *
 * SETUP (once per copy of the Sheet)
 *   1. Paste your SCORING form's ID into SCORING_FORM_ID below. The ID is the
 *      long string in the form's edit link, between /d/ and /edit.
 *   2. Make sure the scoring form has a Dropdown question titled exactly the
 *      same as DROPDOWN_QUESTION_TITLE below.
 *   3. In the Apps Script editor, click the clock icon (Triggers) > Add Trigger:
 *        function: onFormSubmitTrigger | event source: From spreadsheet |
 *        event type: On form submit
 *      The first time, Google asks you to authorize the script. Click through
 *      "Advanced" > "Go to project" and allow access.
 *
 * KNOWN QUIRKS
 *   - "Last, First" names are NOT flipped ("Smith, John" becomes "Smith John").
 *   - Converted JPGs are shared as "anyone with the link can view". Photos
 *     are not searchable, but anyone who has a link can open it.
 *   - Safe to re-run: rows that already have a link in Column F are skipped.
 *   - Apps Script stops a run after about 6 minutes. If a big batch does not
 *     finish, run it again and it picks up where it left off.
 * =============================================================================
 */

// =============================================================================
// CONFIGURATION
// =============================================================================
const SCORING_FORM_ID = "PASTE FORM ID HERE"; // Replace with your Scoring Form ID
const DROPDOWN_QUESTION_TITLE = "PNM Name";        // Exact title of the dropdown question
const RED_NON_IU = "#FFCDD2";
const YELLOW_ALERT = "#FFE082";

// =============================================================================
// 1. TRIGGER FUNCTION: Runs automatically on every Form Submission
// =============================================================================
function onFormSubmitTrigger(e) {
  const sheet = e.range.getSheet();
  const row = e.range.getRow();
  
  // Ensure headers exist
  ensureHeadersExist(sheet);
  
  // Clean only the newly submitted row (Fast & Lightweight)
  cleanSingleRow(sheet, row);
  
  // Instantly sync Column E with the Scoring Form Dropdown
  updateScoringFormDropdown();
}

// =============================================================================
// HELPER: Clean a single row (Preserves compound last names & prefixes)
// =============================================================================
function cleanSingleRow(sheet, row) {
  const rawEmail = sheet.getRange(row, 2).getValue().toString().trim();
  const rawName = sheet.getRange(row, 3).getValue().toString().trim();
  
  // --- SYSTEM 1: Email Audit ---
  const emailCell = sheet.getRange(row, 2);
  if (rawEmail !== "") {
    const lowerEmail = rawEmail.toLowerCase();
    if (lowerEmail.endsWith("@iu.edu") || lowerEmail.endsWith("@indiana.edu")) {
      emailCell.setBackground(null);
    } else {
      emailCell.setBackground(RED_NON_IU);
    }
  }
  
  // --- SYSTEM 2: V1 Name Cleanser (Smart Middle Initial / Compound Name Handling) ---
  let cleanedName = rawName;
  let flagForReview = false;
  
  if (rawName !== "") {
    const preferredMatch = cleanedName.match(/[\("']([^)"']+)[\)"']/);
    
    // Case A: Handles Preferred Names/Nicknames in quotes/parentheses
    if (preferredMatch) {
      let firstName = preferredMatch[1].trim(); 
      let remainingText = cleanedName.replace(/[\("'][^)"']+[\)"']/, " ").trim();
      remainingText = remainingText.replace(/[.,]/g, " ").replace(/\s+/g, " ").trim();
      let parts = remainingText.split(" ");
      let lastName = parts.length > 1 ? parts.slice(1).join(" ") : parts[0]; 
      cleanedName = firstName + " " + lastName;
    } 
    // Case B: Standard Name Processing
    else {
      cleanedName = cleanedName.replace(/,/g, " ").replace(/\s+/g, " ").trim();
    }
    
    // Split into individual word tokens
    let tokens = cleanedName.split(" ").filter(t => t.length > 0);
    
    if (tokens.length === 0) {
      cleanedName = "";
    } else if (tokens.length === 1) {
      // Single Name (e.g. "Giannis") -> Flag Yellow
      flagForReview = true; 
      cleanedName = tokens[0].charAt(0).toUpperCase() + tokens[0].slice(1).toLowerCase();
    } else {
      // Filter out standalone Middle Initials (e.g., "Ryan J. Van Slyke" -> "Ryan Van Slyke")
      let filteredTokens = tokens.filter((token, index) => {
        // Keep first and last words always
        if (index === 0 || index === tokens.length - 1) return true;
        
        // Strip out single-letter middle initials (with or without a dot)
        let cleanToken = token.replace(/\./g, "");
        if (cleanToken.length === 1) return false; 
        
        return true;
      });
      
      // Rejoin remaining words (Preserves "Ryan van Slyke", "Mary Kate Olsen", etc.)
      cleanedName = filteredTokens.join(" ");
      
      // Enforce proper Title Case across each word (e.g., "van slyke" -> "Van Slyke")
      cleanedName = cleanedName.replace(/\b\w/g, char => char.toUpperCase());
    }
    
    // Output result to Column E
    const nameOutputCell = sheet.getRange(row, 5);
    nameOutputCell.setValue(cleanedName);
    
    if (flagForReview) {
      nameOutputCell.setBackground(YELLOW_ALERT);
    } else {
      nameOutputCell.setBackground(null);
    }
  }
}

// =============================================================================
// 3. DROPDOWN UPDATER: Reads Column E (Cleaned Name) & Column B (Email)
// =============================================================================
function updateScoringFormDropdown() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) return; // No data yet
  
  // Grab emails from Column B (col index 2) and cleaned names from Column E (col index 5)
  const emailsRange = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
  const namesRange = sheet.getRange(2, 5, lastRow - 1, 1).getValues();
  
  let pnmList = [];
  
  for (let i = 0; i < namesRange.length; i++) {
    let email = emailsRange[i][0] ? emailsRange[i][0].toString().trim() : "";
    let name = namesRange[i][0] ? namesRange[i][0].toString().trim() : "";
    
    if (name !== "") {
      // If email exists, combine as "First Last - email@iu.edu". Otherwise just "First Last"
      let formattedChoice = email !== "" ? `${name} - ${email}` : name;
      pnmList.push(formattedChoice);
    }
  }
  
  // Deduplicate and sort alphabetically
  pnmList = [...new Set(pnmList)].sort();
  
  if (pnmList.length === 0) return;
  
  // Access Scoring Form
  try {
    const form = FormApp.openById(SCORING_FORM_ID);
    const items = form.getItems(FormApp.ItemType.LIST); // Find Dropdown items
    
    for (let i = 0; i < items.length; i++) {
      let item = items[i].asListItem();
      if (item.getTitle() === DROPDOWN_QUESTION_TITLE) {
        item.setChoiceValues(pnmList);
        Logger.log("✅ Scoring Form Dropdown updated with " + pnmList.length + " PNM entries.");
        break;
      }
    }
  } catch (err) {
    Logger.log("⚠️ Error updating Scoring Form dropdown: " + err.message);
  }
}

// =============================================================================
// 4. MANUAL MEGA SWEEP: Process images with non-blocking toast notifications
// =============================================================================
function runMegaDataCleanserManual() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  ensureHeadersExist(sheet);
  
  Logger.log("🚀 Starting Manual Image Processing Sweep...");
  
  // Show starting toast on spreadsheet
  SpreadsheetApp.getActiveSpreadsheet().toast("Scanning and converting new images...", "Image Processor", 5);
  
  // Run heavy image conversion
  const processedCount = processImageUrls(sheet);
  
  Logger.log("✅ Image processing finished smoothly.");
  
  // Show completion toast (auto-dismisses in 8 seconds, doesn't freeze execution)
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Done! Processed ${processedCount} new images.`, 
    "🔥 Sweep Complete", 
    8
  );
}

// =============================================================================
// HELPER: Optimized & Non-Blocking Image Processor
// =============================================================================
function processImageUrls(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return 0; // No data rows
  
  // Read Columns A through F in a single read
  const dataRange = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  let countProcessed = 0;
  
  for (let i = 0; i < dataRange.length; i++) {
    const row = i + 2;
    const rawUrl = dataRange[i][3] ? dataRange[i][3].toString().trim() : "";    // Column D (Index 3)
    const currentJpgUrl = dataRange[i][5] ? dataRange[i][5].toString().trim() : ""; // Column F (Index 5)
    
    // SKIP IF: Cell is empty OR Column F already has a URL
    if (!rawUrl || currentJpgUrl !== "") continue;
    
    // Extract Drive ID safely from common URL formats (id=... or /d/...)
    let fileId = null;
    const idParamMatch = rawUrl.match(/id=([a-zA-Z0-9_-]+)/);
    const dPathMatch = rawUrl.match(/\/d\/([a-zA-Z0-9_-]+)/);
    
    if (idParamMatch) {
      fileId = idParamMatch[1];
    } else if (dPathMatch) {
      fileId = dPathMatch[1];
    }
    
    // If no valid ID could be parsed, skip row immediately
    if (!fileId) {
      Logger.log(`⏩ Skipping Row ${row}: Invalid/Unrecognized Drive URL format.`);
      continue;
    }
    
    try {
      const file = DriveApp.getFileById(fileId);
      const originalName = file.getName();
      const lowerName = originalName.toLowerCase();
      
      // If already a standard JPG/JPEG, pass link through directly
      if (lowerName.endsWith('.jpg') || lowerName.endsWith('.jpeg')) {
        sheet.getRange(row, 6).setValue(rawUrl);
        countProcessed++;
        Logger.log(`✅ Row ${row}: Direct JPG link saved.`);
      } else {
        // Fetch thumbnail from Drive API for conversion
        const driveApiUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?fields=thumbnailLink`;
        const response = UrlFetchApp.fetch(driveApiUrl, {
          headers: { 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() },
          muteHttpExceptions: true
        });
        
        if (response.getResponseCode() === 200) {
          const fileMetadata = JSON.parse(response.getContentText());
          let thumbnailLink = fileMetadata.thumbnailLink;
          
          if (thumbnailLink) {
            const highResJpgUrl = thumbnailLink.replace(/=s\d+/, '=s0');
            const jpgBlob = UrlFetchApp.fetch(highResJpgUrl).getBlob();
            const baseName = originalName.replace(/\.[^/.]+$/, "");
            jpgBlob.setName(baseName + ".jpg");
            
            const parents = file.getParents();
            let targetFolder = parents.hasNext() ? parents.next() : DriveApp.getRootFolder();
            const newJpgFile = targetFolder.createFile(jpgBlob);
            newJpgFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
            
            sheet.getRange(row, 6).setValue(`https://drive.google.com/open?id=${newJpgFile.getId()}`);
            countProcessed++;
            Logger.log(`🖼️ Row ${row}: Converted non-JPG image to JPG file.`);
          }
        } else {
          Logger.log(`⚠️ Row ${row}: Drive API returned status ${response.getResponseCode()}`);
        }
      }
    } catch (err) {
      Logger.log(`❌ Error processing Row ${row} (File ID: ${fileId}): ${err.message}`);
      // Continue loop even if one row fails
    }
  }
  
  return countProcessed;
}

// Helpers
function ensureHeadersExist(sheet) {
  if (sheet.getRange("E1").getValue() !== "Cleaned Name") {
    sheet.getRange("E1").setValue("Cleaned Name").setFontWeight("bold").setBackground("#E0E0E0");
    sheet.getRange("F1").setValue("Cleaned Image URL").setFontWeight("bold").setBackground("#E0E0E0");
  }
}
