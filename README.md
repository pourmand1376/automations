# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

The workflows check both websites every hour and publish new posts to their configured Telegram channels:

- `amirpourmand.ir`, checked at minute 17
- `aprd.ir`, checked at minute 37

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`: shared bot token for both websites
- `WEBSITES_TELEGRAM_CHANNEL_ID`: shared numeric channel ID for both websites
- `CASTBOX_TELEGRAM_CHANNEL_ID`: numeric ID of the Telegram channel for Castbox episodes

The bot must be an administrator of the target channel. The first run records existing feed entries; later runs publish new entries and commit their IDs to `state/amirpourmand_ir_to_telegram.json`.

To find a channel ID, add the bot to the channel and open:

```text
https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```

Look for `channel_post.chat.id` in the response.

Run locally with:

```bash
TELEGRAM_BOT_TOKEN=... \
WEBSITES_TELEGRAM_CHANNEL_ID=-1001234567890 \
python3 -m workflows.runner amirpourmand-ir
```

Castbox is intentionally not run by GitHub Actions. Run it on your server with Telegram’s local Bot API server so large episodes can be uploaded. From the repository directory, configure `TELEGRAM_BOT_TOKEN`, `CASTBOX_TELEGRAM_CHANNEL_ID`, and `TELEGRAM_API_BASE_URL`, then run:

```bash
TELEGRAM_BOT_TOKEN=... \
CASTBOX_TELEGRAM_CHANNEL_ID=-1001234567890 \
TELEGRAM_API_BASE_URL=http://127.0.0.1:8081 \
python3 -m workflows.runner castbox
```

Schedule that command with cron or a systemd timer. It reads `http://rss.castbox.fm/everest/480c97a079254a06ba396783a44f0acc.xml`, publishes new episodes, and stores deduplication state in `state/castbox_to_telegram.json`. It downloads each RSS audio enclosure and uploads MP3/M4A files as Telegram audio; other audio formats are uploaded as documents.

The website workflows and TickTick workflow continue to run on GitHub Actions. They use Telegram’s hosted API by default.

## TickTick Today alerts

`.github/workflows/ticktick-today-alerts.yml` checks TickTick daily at 06:00 UTC through the official CLI and sends a Telegram alert when the Today-style task list changes. It uses the broad open-task query and filters tasks locally by their start or due date, including overdue tasks.

Add these repository secrets:

- `TICKTICK_ACCESS_TOKEN`: TickTick API access token
- `TELEGRAM_BOT_TOKEN`: the shared Telegram bot token
- `PERSONAL_CHAT_ID_TELEGRAM`: numeric ID of the Telegram chat for Today alerts
