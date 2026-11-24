/**
 * PSE RECRUITMENT: SLIDESHOW GENERATOR (Google Apps Script)
 * =============================================================================
 * Lives in the same Google Sheet as the check-in cleanser (data_cleansing.gs).
 * Builds a Google Slides roster: 10 PNMs per slide (5 columns x 2 rows), each
 * with a photo and a name underneath. The deck title is hardcoded as
 * "Meet the Chapter - PNMs X to Y"; change it in the code if you use the deck
 * for a different event. See docs/06_google_check_in_tools.md.
 *
 * HOW TO RUN
 *   1. Open the Sheet so it is the tab you can see. Open Extensions > Apps Script.
 *   2. Choose generateSlideshow in the function dropdown and click Run.
 *   3. Switch back to the Sheet. Two pop-ups ask for a STARTING PNM number and
 *      an ENDING PNM number. For the whole list, start at 1 and end at the
 *      total. Batches of 100 or fewer are recommended, since a bigger one can
 *      hit Apps Script's time limit. To do 250 PNMs, run 1-100, 101-200, 201-250.
 *   4. A pop-up gives you a button that opens the finished slideshow. It is
 *      saved in your Google Drive and titled "Meet the Chapter - PNMs X to Y".
 *
 * REQUIRES
 *   Column E (Cleaned Name) and Column F (Cleaned Image URL) filled in by
 *   data_cleansing.gs. Rows missing either are skipped.
 *
 * Note: "PNM #" here means position in the list of valid rows, not any ID
 * number from the application.
 * =============================================================================
 */

function generateSlideshow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const ui = SpreadsheetApp.getUi();
  
  if (data.length < 2) {
    ui.alert("No check-in data found in spreadsheet.");
    return;
  }
  
  // 1. Scan and collect all valid candidate rows (Column E = Name, Column F = URL)
  const validRows = [];
  for (let i = 1; i < data.length; i++) {
    const name = data[i][4] ? data[i][4].toString().trim() : ""; 
    const url = data[i][5] ? data[i][5].toString().trim() : ""; 
    if (name && url) {
      validRows.push({ rowIndex: i + 1, name: name, url: url });
    }
  }

  if (validRows.length === 0) {
    ui.alert("No valid PNMs found with both Cleaned Name (Col E) and Cleaned Image URL (Col F).");
    return;
  }

  // 2. Prompt for STARTING PNM number
  const startResponse = ui.prompt(
    '🎬 Generate Grid Slideshow (Batch Mode)',
    `Total valid PNMs found: ${validRows.length}\n\nEnter STARTING PNM # (1 - ${validRows.length}):`,
    ui.ButtonSet.OK_CANCEL
  );

  if (startResponse.getSelectedButton() !== ui.Button.OK) return;
  let startNum = parseInt(startResponse.getResponseText().trim(), 10);
  if (isNaN(startNum) || startNum < 1 || startNum > validRows.length) startNum = 1;

  // 3. Prompt for ENDING PNM number (Default to 100 per deck)
  const suggestedEnd = Math.min(startNum + 99, validRows.length);
  const endResponse = ui.prompt(
    '🎬 Generate Grid Slideshow (Batch Mode)',
    `Enter ENDING PNM # (Recommended max 100 per batch for speed):\nSuggested End: ${suggestedEnd}`,
    ui.ButtonSet.OK_CANCEL
  );

  if (endResponse.getSelectedButton() !== ui.Button.OK) return;
  let endNum = parseInt(endResponse.getResponseText().trim(), 10);
  if (isNaN(endNum) || endNum < startNum) endNum = suggestedEnd;
  if (endNum > validRows.length) endNum = validRows.length;

  // Slice out only the requested batch
  const batchToProcess = validRows.slice(startNum - 1, endNum);

  // 4. Create presentation titled specifically for this batch
  const presentationTitle = `Meet the Chapter - PNMs ${startNum} to ${endNum}`;
  const presentation = SlidesApp.create(presentationTitle);
  
  let currentSlide = presentation.appendSlide(SlidesApp.PredefinedLayout.BLANK);
  let countOnSlide = 0;
  let totalProcessed = 0;
  
  // Layout Constants (16:9 Standard = 720 x 405)
  const SLIDE_WIDTH = 720;
  const SLIDE_HEIGHT = 405;
  const COLS = 5; 
  const ROWS = 2;
  const COL_WIDTH = SLIDE_WIDTH / COLS;   // 144 points
  const ROW_HEIGHT = SLIDE_HEIGHT / ROWS; // 202.5 points

  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Building slides for PNMs ${startNum} to ${endNum}...`, 
    "📸 Generating Slideshow", 
    5
  );

  // 5. Build grid slides for batch
  for (let i = 0; i < batchToProcess.length; i++) {
    const item = batchToProcess[i];
    const name = item.name;
    const url = item.url;

    // Create a new slide every 10 PNMs
    if (countOnSlide >= 10) {
      currentSlide = presentation.appendSlide(SlidesApp.PredefinedLayout.BLANK);
      countOnSlide = 0;
    }
    
    // Extract File ID from standard Drive URLs (id=... OR /d/...)
    let fileId = null;
    const idParamMatch = url.match(/id=([a-zA-Z0-9_-]+)/);
    const dPathMatch = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
    
    if (idParamMatch) fileId = idParamMatch[1];
    else if (dPathMatch) fileId = dPathMatch[1];
    
    if (!fileId) {
      Logger.log(`Skipped row ${item.rowIndex}: Could not parse Drive File ID.`);
      continue;
    }
    
    try {
      // Fetch image from Drive
      const file = DriveApp.getFileById(fileId);
      const blob = file.getBlob();
      
      // Grid positioning
      const col = countOnSlide % COLS;
      const row = Math.floor(countOnSlide / COLS);
      
      const x = col * COL_WIDTH;
      const y = row * ROW_HEIGHT;
      
      const targetWidth = COL_WIDTH - 20; 
      const targetHeight = ROW_HEIGHT - 45; 
      
      // Insert and scale image
      const image = currentSlide.insertImage(blob);
      const imgWidth = image.getWidth();
      const imgHeight = image.getHeight();
      
      const ratio = Math.min(targetWidth / imgWidth, targetHeight / imgHeight);
      const finalImgWidth = imgWidth * ratio;
      const finalImgHeight = imgHeight * ratio;
      
      image.setWidth(finalImgWidth);
      image.setHeight(finalImgHeight);
      
      image.setLeft(x + (COL_WIDTH - finalImgWidth) / 2);
      image.setTop(y + 8);
      
      // Insert Name Text Box directly below image
      const textY = y + 8 + finalImgHeight + 2; 
      const textBox = currentSlide.insertTextBox(name, x, textY, COL_WIDTH, 30);
      
      // Style Name
      const textRange = textBox.getText();
      textRange.getParagraphStyle().setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
      textRange.getTextStyle().setFontSize(13).setBold(true);
      
      countOnSlide++;
      totalProcessed++;
      
    } catch (e) {
      Logger.log(`Error processing row ${item.rowIndex} (${name}): ${e.toString()}`);
    }
  }
  
  // Safely remove initial blank title slide
  const slides = presentation.getSlides();
  if (slides.length > 1 && totalProcessed > 0) {
    presentation.getSlides()[0].remove();
  }
  
  // Popup dialog with clickable button link
  const htmlOutput = HtmlService.createHtmlOutput(
    `<div style="font-family: sans-serif; padding: 10px; text-align: center;">
      <p style="font-size: 14px; margin-bottom: 15px;">
        Successfully created <b>${presentationTitle}</b> with <b>${totalProcessed}</b> PNMs!
      </p>
      <a href="${presentation.getUrl()}" target="_blank" style="background-color: #1a73e8; color: white; padding: 10px 18px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
        Open Slideshow Deck
      </a>
    </div>`
  ).setWidth(360).setHeight(140);
  
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'Slideshow Generated');
}
