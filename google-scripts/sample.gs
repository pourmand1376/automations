/**
 * Minimal Google Apps Script sample.
 *
 * Google-related scripts should be added under google-scripts/.
 */
function sampleWorkflow() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();
  sheet.getRange('A1').setValue(`Last run: ${new Date().toISOString()}`);
}
