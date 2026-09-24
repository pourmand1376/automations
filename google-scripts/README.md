# Google Scripts

Google Apps Script projects and Google-related automation scripts belong in this directory.

The `.gs` files can be copied into [Google Apps Script](https://script.google.com/) or managed with the `clasp` CLI when a project needs version control and deployment.

Scripts that need their own manifest, services, or triggers live in a subdirectory with an `appsscript.json`, so each one is a separate Apps Script project.

## Birthday reminder

[`birthday-reminder/`](birthday-reminder/) checks Google Contacts daily at 09:00 Asia/Tehran and sends a Telegram message 3 days before a birthday and on the day itself. It reads birthdays through the People API and takes `TELEGRAM_BOT_TOKEN` and `PERSONAL_CHAT_ID_TELEGRAM` from Script Properties. See its [README](birthday-reminder/README.md) for setup.

## Sample

Open `sample.gs` in Google Apps Script and run `sampleWorkflow`. The first run asks for permission to access the current spreadsheet, then writes a timestamp to cell `A1`.
