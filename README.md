# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

The workflows check both websites every hour and publish new posts to their configured Telegram channels:

- `amirpourmand.ir`, checked at minute 17
- `aprd.ir`, checked at minute 37

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`: shared bot token for both websites
- `WEBSITES_TELEGRAM_CHANNEL_ID`: shared numeric channel ID for both websites

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
