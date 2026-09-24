# Birthday reminder

Checks Google Contacts once a day and sends a Telegram message when a contact has a
birthday in 3 days, and again on the day itself. Nothing is sent on quiet days.

Unlike the jobs in `.github/workflows/`, this one cannot run on GitHub Actions: reading
Google Contacts needs an interactive OAuth consent from the account that owns them.
Apps Script runs as that account and has its own daily trigger.

## Setup

1. Create a new project at [script.google.com](https://script.google.com/).
2. Copy `birthday-reminder.gs` into the editor, and paste `appsscript.json` over the
   manifest (**Project Settings → Show "appsscript.json" manifest file in editor**).
   With `clasp`, `clasp push` from this directory does both.
3. **Services → +** and add **People API** (`v1`, identifier `People`). The manifest
   already declares it, but the editor needs it enabled once.
4. **Project Settings → Script Properties** and add:
   - `TELEGRAM_BOT_TOKEN`: the shared bot token
   - `PERSONAL_CHAT_ID_TELEGRAM`: numeric ID of the private chat
   - `TELEGRAM_API_BASE_URL`: optional, defaults to `https://api.telegram.org`
5. Run `previewBirthdays` once and accept the permission prompt. It logs the message
   that today would produce and sends nothing.
6. Run `sendTestMessage` to confirm the token and chat ID work.
7. Run `installDailyTrigger` to schedule `dailyBirthdayCheck` daily at 09:00
   Asia/Tehran. Re-running it replaces the trigger instead of adding a second one.

Start a chat with the bot first, otherwise Telegram rejects the message with
`chat not found`.

## Behaviour

- Reminder days come from `REMIND_DAYS` at the top of the script, `[3, 0]` by default.
- Contacts without a birthday month and day are skipped; a stored birth year adds
  `turning N` to the line.
- Time-driven triggers fire within the hour they are scheduled for, so the message
  arrives between 09:00 and 10:00.
- `LAST_RUN_DATE` in Script Properties stops a second message on the same day. It is
  written after a successful send, so a failed run retries the next day.
- Failures throw, which makes Apps Script email the stack trace to the account owner.

## Message

```text
<b>Birthdays</b>

• Sara Ahmadi — today (Mon, Sep 21)
• Ali Rezaei — in 3 days (Thu, Sep 24), turning 30
```
