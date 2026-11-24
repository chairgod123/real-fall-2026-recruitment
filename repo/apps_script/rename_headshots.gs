/**
 * RENAME HEADSHOTS: fix names on photos that were ALREADY converted
 * =============================================================================
 * WHAT IT DOES
 *   For every row that already has a "Cleaned JPEG Link", renames that Drive
 *   file to "<iu-email>.jpg". Use it if photos were converted before the
 *   rename step existed, or if emails were corrected afterward.
 *
 * REQUIRES
 *   Must live in the SAME Apps Script project as application_headshots.gs,
 *   because it uses OUTPUT_HEADER_NAME and extractDriveId() from that file.
 *
 * HOW TO RUN
 *   Pick `renameExistingJpgs` in the function dropdown and click Run.
 *   Safe to re-run: files already named correctly are left alone.
 */
// =============================================================================
// RENAME ONLY: Renames files that are ALREADY converted without remaking them
// =============================================================================
function renameExistingJpgs() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // 1. Locate Email and Cleaned JPEG Link columns
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  let emailColIndex = headers.findIndex(h => h.toString().toLowerCase().trim().includes("email")) + 1;
  if (emailColIndex === 0) emailColIndex = 3; // Column C

  let outputColIndex = headers.indexOf(OUTPUT_HEADER_NAME) + 1;
  if (outputColIndex === 0) {
    SpreadsheetApp.getUi().alert("⚠️ Could not find 'Cleaned JPEG Link' column. Please run the main script first.");
    return;
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  // 2. Read values
  const emailValues = sheet.getRange(2, emailColIndex, lastRow - 1, 1).getValues();
  const outputValues = sheet.getRange(2, outputColIndex, lastRow - 1, 1).getValues();

  ss.toast("Renaming existing image files in Google Drive...", "Image Renamer", 5);
  let renamedCount = 0;

  // 3. Loop through rows and rename existing files in Drive
  for (let i = 0; i < outputValues.length; i++) {
    const row = i + 2;
    const rawEmail = emailValues[i][0] ? emailValues[i][0].toString().trim() : "";
    const cleanJpgUrl = outputValues[i][0] ? outputValues[i][0].toString().trim() : "";

    // Skip if there's no existing cleaned image link or no email
    if (!cleanJpgUrl || !rawEmail) continue;

    const fileId = extractDriveId(cleanJpgUrl);
    if (!fileId) continue;

    try {
      const file = DriveApp.getFileById(fileId);
      
      // Clean invalid filename characters
      const cleanEmail = rawEmail.replace(/[/\\?%*:|"<>]/g, "");
      const newName = cleanEmail.toLowerCase().endsWith(".jpg") ? cleanEmail : `${cleanEmail}.jpg`;

      // Rename only if the name isn't already correct
      if (file.getName() !== newName) {
        file.setName(newName);
        renamedCount++;
        Logger.log(`✏️ Row ${row}: Renamed existing Drive file to "${newName}"`);
      }
    } catch (err) {
      Logger.log(`❌ Error renaming file for Row ${row} (ID: ${fileId}): ${err.message}`);
    }
  }

  ss.toast(`Done! Renamed ${renamedCount} existing files in Google Drive.`, "🔥 Renaming Complete", 8);
}
